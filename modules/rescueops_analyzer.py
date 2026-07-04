from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DOG_BOOL_COLUMNS = [
    "special_needs",
    "adoption_ready",
    "bio_needed",
    "social_post_needed",
]

INQUIRY_BOOL_COLUMNS = ["has_children", "has_other_pets"]
VOLUNTEER_BOOL_COLUMNS = [
    "can_foster",
    "can_transport",
    "can_handle_medical",
    "can_handle_seniors",
    "can_handle_large_dogs",
]


def _as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def load_rescueops_data(paths: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dogs = pd.read_csv(paths["dogs"], parse_dates=["intake_date"])
    inquiries = pd.read_csv(paths["inquiries"], parse_dates=["inquiry_date"])
    volunteers = pd.read_csv(paths["volunteers"])
    medical = pd.read_csv(paths["medical"], parse_dates=["expense_date"])

    for column in DOG_BOOL_COLUMNS:
        dogs[column] = _as_bool(dogs[column])
    for column in INQUIRY_BOOL_COLUMNS:
        inquiries[column] = _as_bool(inquiries[column])
    for column in VOLUNTEER_BOOL_COLUMNS:
        volunteers[column] = _as_bool(volunteers[column])
    return dogs, inquiries, volunteers, medical


def summarize_rescueops(
    dogs: pd.DataFrame, inquiries: pd.DataFrame, volunteers: pd.DataFrame, medical: pd.DataFrame
) -> dict:
    in_care = dogs[dogs["current_status"] != "Adopted"]
    foster_need = dogs[
        (dogs["current_status"].isin(["Foster Needed", "Intake"]))
        | (dogs["foster_status"].isin(["Needs Foster", "Needs Backup", "Boarding"]))
    ]
    urgent_medical = dogs[dogs["medical_status"].isin(["Emergency", "Surgery Needed", "Medical Hold"])]
    unanswered = inquiries[inquiries["response_status"].isin(["New", "In Review", "Overdue", "Escalated"])]
    recent_cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=30)
    recent_medical = medical[medical["expense_date"] >= recent_cutoff]
    open_capacity = (volunteers["foster_capacity"] - volunteers["current_assignments"]).clip(lower=0).sum()

    priority_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    highest_priority = (
        in_care.assign(priority_rank=in_care["priority_level"].map(priority_order).fillna(0))
        .sort_values(["priority_rank", "days_in_care", "estimated_monthly_cost"], ascending=False)
        .head(1)
    )

    unfunded_amount = _unfunded_amount(medical)

    return {
        "dogs_in_care": int(len(in_care)),
        "dogs_needing_foster": int(len(foster_need)),
        "dogs_adoption_ready": int(dogs["adoption_ready"].sum()),
        "urgent_medical_cases": int(len(urgent_medical)),
        "open_adoption_inquiries": int(
            len(
                inquiries[
                    (inquiries["inquiry_type"] == "Adoption Inquiry")
                    & (inquiries["response_status"].isin(["New", "In Review", "Overdue", "Escalated"]))
                ]
            )
        ),
        "unanswered_messages": int(len(unanswered)),
        "monthly_medical_costs": float(recent_medical["amount"].sum()),
        "unfunded_medical_need": float(unfunded_amount),
        "volunteer_capacity": int(open_capacity),
        "highest_priority_dog": str(highest_priority.iloc[0]["dog_name"] if len(highest_priority) else "No active cases"),
    }


def _unfunded_amount(medical: pd.DataFrame) -> float:
    unfunded = medical.loc[medical["funded_status"] == "Unfunded", "amount"].sum()
    partial = medical.loc[medical["funded_status"] == "Partially Funded", "amount"].sum() * 0.5
    return float(unfunded + partial)


def get_rescueops_chart_data(
    dogs: pd.DataFrame, inquiries: pd.DataFrame, volunteers: pd.DataFrame, medical: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    foster_need = int(
        len(
            dogs[
                (dogs["current_status"].isin(["Foster Needed", "Intake"]))
                | (dogs["foster_status"].isin(["Needs Foster", "Needs Backup", "Boarding"]))
            ]
        )
    )
    open_capacity = int((volunteers["foster_capacity"] - volunteers["current_assignments"]).clip(lower=0).sum())

    return {
        "dogs_by_status": dogs.groupby("current_status").size().reset_index(name="dogs").sort_values("dogs", ascending=False),
        "dogs_by_medical_status": dogs.groupby("medical_status").size().reset_index(name="dogs").sort_values(
            "dogs", ascending=False
        ),
        "adoption_pipeline": dogs.groupby("adoption_status").size().reset_index(name="dogs").sort_values(
            "dogs", ascending=False
        ),
        "inquiry_types": inquiries.groupby("inquiry_type").size().reset_index(name="inquiries").sort_values(
            "inquiries", ascending=False
        ),
        "inquiry_response_aging": _aging_buckets(inquiries),
        "medical_costs_by_dog": medical.groupby("dog_name")["amount"].sum().reset_index().sort_values(
            "amount", ascending=False
        ).head(15),
        "medical_costs_by_type": medical.groupby("expense_type")["amount"].sum().reset_index().sort_values(
            "amount", ascending=False
        ),
        "foster_capacity_vs_need": pd.DataFrame(
            {"category": ["Open Foster Capacity", "Dogs Needing Foster"], "count": [open_capacity, foster_need]}
        ),
        "volunteer_role_coverage": volunteers.groupby("role").size().reset_index(name="volunteers").sort_values(
            "volunteers", ascending=False
        ),
    }


def _aging_buckets(inquiries: pd.DataFrame) -> pd.DataFrame:
    buckets = pd.cut(
        inquiries["days_waiting"],
        bins=[-1, 1, 3, 7, 30],
        labels=["0-1 days", "2-3 days", "4-7 days", "8+ days"],
    )
    return inquiries.assign(aging_bucket=buckets).groupby("aging_bucket", observed=False).size().reset_index(name="inquiries")


def triage_adoption_inquiries(inquiries: pd.DataFrame, dogs: pd.DataFrame) -> pd.DataFrame:
    adoption = inquiries[inquiries["inquiry_type"] == "Adoption Inquiry"].copy()
    joined = adoption.merge(
        dogs[
            [
                "dog_name",
                "adoption_ready",
                "medical_status",
                "special_needs",
                "good_with_dogs",
                "good_with_cats",
                "good_with_children",
                "energy_level",
            ]
        ],
        on="dog_name",
        how="left",
    )
    joined["overdue"] = joined["days_waiting"] > 3
    joined["follow_up_questions"] = joined.apply(_follow_up_questions, axis=1)
    joined["review_flag"] = joined["triage_category"].isin(["Not Ideal Fit", "Urgent Human Review", "Medical/Safety Escalation"])
    return joined.sort_values(["priority_score", "days_waiting"], ascending=False)


def _follow_up_questions(row: pd.Series) -> str:
    questions: list[str] = []
    if row["triage_category"] == "Missing Information":
        questions.append("Confirm household schedule, pet history, and preferred adoption timeline.")
    if row["has_children"] and row.get("good_with_children") in {"No", "Unknown"}:
        questions.append("Ask for child ages and confirm comfort with a human-reviewed match.")
    if row["has_other_pets"] and row.get("good_with_dogs") in {"No", "Unknown"}:
        questions.append("Ask about resident pets, introductions, and management plan.")
    if row.get("special_needs"):
        questions.append("Confirm ability to support ongoing care and follow rescue guidance.")
    if row["days_waiting"] > 3:
        questions.append("Send an apology for delayed response and provide a clear next step.")
    return " ".join(questions) if questions else "Confirm availability, adoption timeline, and best contact method."


def foster_matching(dogs: pd.DataFrame, volunteers: pd.DataFrame) -> pd.DataFrame:
    need = dogs[
        (dogs["current_status"].isin(["Foster Needed", "Intake", "Medical Hold"]))
        | (dogs["foster_status"].isin(["Needs Foster", "Needs Backup", "Boarding"]))
    ].copy()
    candidates = volunteers[
        (volunteers["can_foster"]) & ((volunteers["foster_capacity"] - volunteers["current_assignments"]) > 0)
    ].copy()

    rows: list[dict] = []
    for _, dog in need.iterrows():
        if candidates.empty:
            rows.append(
                {
                    "dog_name": dog["dog_name"],
                    "best_foster_match": "No open foster capacity",
                    "match_score": 0,
                    "reason_for_match": "All active foster capacity is currently assigned.",
                    "caution_notes": "Recruit backup foster or temporary boarding support.",
                    "recommended_next_step": "Escalate foster need in the weekly volunteer brief.",
                }
            )
            continue

        scored = candidates.copy()
        scored["available_capacity"] = scored["foster_capacity"] - scored["current_assignments"]
        scored["match_score"] = scored.apply(lambda volunteer: _foster_score(dog, volunteer), axis=1)
        best = scored.sort_values("match_score", ascending=False).iloc[0]
        reason, caution = _foster_reason(dog, best)
        rows.append(
            {
                "dog_name": dog["dog_name"],
                "best_foster_match": best["volunteer_name"],
                "match_score": int(best["match_score"]),
                "reason_for_match": reason,
                "caution_notes": caution,
                "recommended_next_step": "Confirm availability, share dog profile, and schedule handoff discussion.",
            }
        )

    return pd.DataFrame(rows).sort_values("match_score", ascending=False)


def _is_large_breed(breed: str) -> bool:
    large_terms = ["Shepherd", "Labrador", "Pit", "Husky", "Great Pyrenees", "Mastiff", "Boxer"]
    return any(term in breed for term in large_terms)


def _foster_score(dog: pd.Series, volunteer: pd.Series) -> float:
    score = 25 + volunteer["available_capacity"] * 10 + volunteer["reliability_score"] * 0.25
    if volunteer["can_transport"]:
        score += 8
    if dog["medical_status"] not in {"Clear", "Routine Care"} and volunteer["can_handle_medical"]:
        score += 18
    if dog["age_group"] == "Senior" and volunteer["can_handle_seniors"]:
        score += 12
    if _is_large_breed(dog["breed_mix"]) and volunteer["can_handle_large_dogs"]:
        score += 10
    if volunteer["availability"] == "Flexible":
        score += 8
    if volunteer["availability"] == "Limited":
        score -= 10
    if dog["medical_status"] in {"Emergency", "Surgery Needed"} and not volunteer["can_handle_medical"]:
        score -= 20
    return max(0, min(100, round(score, 1)))


def _foster_reason(dog: pd.Series, volunteer: pd.Series) -> tuple[str, str]:
    reasons = [f"{volunteer['volunteer_name']} has open foster capacity"]
    cautions: list[str] = []
    if volunteer["can_transport"]:
        reasons.append("can transport")
    if dog["medical_status"] not in {"Clear", "Routine Care"}:
        if volunteer["can_handle_medical"]:
            reasons.append("can support medical coordination")
        else:
            cautions.append("medical status needs coordinator oversight")
    if dog["age_group"] == "Senior" and not volunteer["can_handle_seniors"]:
        cautions.append("senior experience not confirmed")
    if _is_large_breed(dog["breed_mix"]) and not volunteer["can_handle_large_dogs"]:
        cautions.append("large-dog handling should be confirmed")
    return "; ".join(reasons) + ".", "; ".join(cautions) if cautions else "No major matching cautions from structured data."


def medical_priority_scoring(dogs: pd.DataFrame, medical: pd.DataFrame) -> pd.DataFrame:
    medical_copy = medical.copy()
    medical_copy["unfunded_estimate"] = np.select(
        [
            medical_copy["funded_status"] == "Unfunded",
            medical_copy["funded_status"] == "Partially Funded",
        ],
        [medical_copy["amount"], medical_copy["amount"] * 0.5],
        default=0,
    )
    agg = (
        medical_copy.groupby("dog_name")
        .agg(
            total_medical_cost=("amount", "sum"),
            funding_needed=("unfunded_estimate", "sum"),
            highest_urgency=("urgency", _highest_urgency),
        )
        .reset_index()
    )
    joined = dogs.merge(agg, on="dog_name", how="left").fillna(
        {"total_medical_cost": 0, "funding_needed": 0, "highest_urgency": "Low"}
    )
    urgency_score = joined["highest_urgency"].map({"Low": 20, "Medium": 45, "High": 75, "Critical": 100}).fillna(20)
    status_score = joined["medical_status"].map(
        {
            "Clear": 10,
            "Routine Care": 25,
            "Vaccines Needed": 35,
            "Dental Needed": 55,
            "Heartworm Treatment": 70,
            "Medical Hold": 78,
            "Surgery Needed": 90,
            "Emergency": 100,
        }
    ).fillna(30)
    amount_score = _normalize(joined["funding_needed"])
    days_score = _normalize(joined["days_in_care"])
    adoption_impact = np.where((~joined["adoption_ready"]) & (status_score >= 55), 100, 35)

    joined["medical_priority_score"] = (
        urgency_score * 0.3 + status_score * 0.25 + amount_score * 0.25 + days_score * 0.1 + adoption_impact * 0.1
    ).round(1)
    joined["recommended_donation_campaign_focus"] = joined.apply(_campaign_focus, axis=1)
    joined["suggested_founder_action"] = joined.apply(_founder_action, axis=1)
    return joined[
        [
            "dog_name",
            "medical_status",
            "priority_level",
            "days_in_care",
            "total_medical_cost",
            "funding_needed",
            "highest_urgency",
            "medical_priority_score",
            "recommended_donation_campaign_focus",
            "suggested_founder_action",
        ]
    ].sort_values("medical_priority_score", ascending=False)


def _normalize(series: pd.Series) -> pd.Series:
    series = series.astype(float)
    span = series.max() - series.min()
    if span == 0:
        return pd.Series(np.ones(len(series)) * 50, index=series.index)
    return ((series - series.min()) / span) * 100


def _highest_urgency(values: pd.Series) -> str:
    order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    return sorted(values, key=lambda item: order.get(item, 0), reverse=True)[0]


def _campaign_focus(row: pd.Series) -> str:
    if row["funding_needed"] <= 0:
        return "No active funding gap; feature adoption readiness or foster progress."
    if row["highest_urgency"] == "Critical":
        return "Immediate medical stabilization fund."
    if row["medical_status"] in {"Surgery Needed", "Heartworm Treatment", "Dental Needed"}:
        return f"{row['medical_status']} funding campaign."
    return "General medical care support."


def _founder_action(row: pd.Series) -> str:
    if row["medical_priority_score"] >= 80:
        return "Review today, confirm care plan, and elevate donor visibility."
    if row["medical_priority_score"] >= 60:
        return "Add to weekly medical funding review and assign volunteer owner."
    return "Monitor through normal rescue operations cadence."


def generate_dog_content(dog: pd.Series, dog_medical: pd.DataFrame | None = None) -> dict[str, str]:
    funding_needed = 0.0
    if dog_medical is not None and not dog_medical.empty:
        funding_needed = float(
            dog_medical.loc[dog_medical["funded_status"] == "Unfunded", "amount"].sum()
            + dog_medical.loc[dog_medical["funded_status"] == "Partially Funded", "amount"].sum() * 0.5
        )

    safe_medical_line = (
        f"{dog['dog_name']} is currently listed as {dog['medical_status'].lower()} in the rescue tracker."
        if dog["medical_status"] != "Clear"
        else f"{dog['dog_name']} is listed as medically clear in the rescue tracker."
    )
    adoption_bio = (
        f"{dog['dog_name']} is a {dog['age_group'].lower()} {dog['breed_mix']} with a {dog['energy_level'].lower()} "
        f"energy level. Current notes say: {dog['behavior_notes'].lower()}. Compatibility from the structured profile: "
        f"dogs: {dog['good_with_dogs']}, cats: {dog['good_with_cats']}, children: {dog['good_with_children']}. "
        f"{safe_medical_line} A human adoption lead should confirm fit before placement."
    )
    facebook_post = (
        f"Meet {dog['dog_name']}! This {dog['age_group'].lower()} {dog['breed_mix']} is currently "
        f"{dog['current_status'].lower()} and could use the right next step. Energy level: {dog['energy_level']}. "
        "Message the rescue team to learn more or help share the profile."
    )
    donation_appeal = (
        f"{dog['dog_name']} has an estimated ${funding_needed:,.0f} in visible unfunded or partially funded medical need. "
        "A donation campaign can help the rescue keep care moving while volunteers coordinate the next safe step."
        if funding_needed > 0
        else f"{dog['dog_name']} does not show a current structured medical funding gap. Consider featuring adoption or foster support."
    )
    foster_plea = (
        f"{dog['dog_name']} needs a foster plan that matches the structured profile: {dog['age_group'].lower()}, "
        f"{dog['breed_mix']}, {dog['energy_level'].lower()} energy, medical status {dog['medical_status'].lower()}. "
        "The rescue should confirm compatibility and care details before placement."
    )
    volunteer_summary = (
        f"Volunteer focus for {dog['dog_name']}: confirm foster/adoption readiness, update bio/social needs, "
        "and route any medical or compatibility questions to the appropriate human lead."
    )
    return {
        "Adoption Bio": adoption_bio,
        "Short Facebook Post": facebook_post,
        "Donation Appeal": donation_appeal,
        "Foster Plea": foster_plea,
        "Volunteer-Friendly Summary": volunteer_summary,
    }


def weekly_founder_brief(
    summary: dict,
    dogs: pd.DataFrame,
    inquiries: pd.DataFrame,
    medical_priority: pd.DataFrame,
    foster_matches: pd.DataFrame,
) -> str:
    urgent_dogs = ", ".join(
        dogs.loc[dogs["priority_level"].isin(["Critical", "High"]), "dog_name"].head(6).tolist()
    )
    overdue = inquiries[inquiries["days_waiting"] > 3]
    top_medical = medical_priority.head(3)
    foster_gap = foster_matches[foster_matches["match_score"] < 60].head(5)
    social_need = dogs[(dogs["bio_needed"]) | (dogs["social_post_needed"])]["dog_name"].head(8).tolist()

    medical_lines = "\n".join(
        [
            f"- {row.dog_name}: ${row.funding_needed:,.0f} funding need, {row.highest_urgency} urgency, score {row.medical_priority_score:.0f}."
            for row in top_medical.itertuples()
        ]
    )
    foster_lines = "\n".join(
        [
            f"- {row.dog_name}: {row.best_foster_match}, score {row.match_score}. {row.caution_notes}"
            for row in foster_gap.itertuples()
        ]
    )
    social_line = ", ".join(social_need) if social_need else "No immediate social-content queue from structured data."

    return f"""## Weekly Founder Brief

### Executive Summary
Rosalie and Friends currently has {summary['dogs_in_care']} dogs in care, {summary['dogs_needing_foster']} foster gaps, {summary['urgent_medical_cases']} urgent medical cases, and {summary['unanswered_messages']} unanswered messages. The highest priority dog from the structured tracker is {summary['highest_priority_dog']}.

### Dogs Needing Urgent Attention
{urgent_dogs if urgent_dogs else "No high-priority dogs are currently flagged."}

### Foster Gaps
{foster_lines if foster_lines else "- Current foster matches show adequate structured fit for the highest-need dogs."}

### Medical Funding Needs
{medical_lines}

### Unanswered Inquiries
{len(overdue)} inquiries have waited more than 3 days. Prioritize adoption inquiries, surrender requests, and any medical/safety escalations.

### Volunteer Actions
Assign one owner for overdue inquiry response, one owner for foster follow-up, and one owner for donor/social updates.

### Social Media Priorities
Feature: {social_line}

### Safety Boundary
This brief supports volunteer coordination. Medical decisions, foster placement, and adoption decisions require human review.
"""


def safety_boundaries() -> list[str]:
    return [
        "This tool does not provide veterinary medical advice.",
        "Medical questions should be routed to a licensed veterinarian or emergency vet.",
        "Adoption and foster decisions require human review.",
        "The app supports volunteers but does not replace judgment.",
        "Personal data should be handled securely in any production version.",
    ]
