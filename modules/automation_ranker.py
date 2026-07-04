from __future__ import annotations

import numpy as np
import pandas as pd


OPSPILOT_AUTOMATION_SPECS = {
    "Missing Document Follow-Up": {
        "problem": "Requests stall because required documentation is missing during intake.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Reduces waiting time, rework, and requester follow-up burden.",
        "tool": "Power Automate, SharePoint Lists, Teams, email automation",
        "first_step": "Define required fields by request type and create a follow-up template.",
        "repeatability": 92,
        "rule_clarity": 90,
        "save_rate": 0.62,
    },
    "Approval Reminder Automation": {
        "problem": "Approvals sit in queues without timely nudges or escalation.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Improves cycle time and SLA performance for approval-heavy work.",
        "tool": "Power Automate, Teams approvals, scheduled Python job",
        "first_step": "Map approval owners, escalation windows, and exception paths.",
        "repeatability": 86,
        "rule_clarity": 82,
        "save_rate": 0.48,
    },
    "Duplicate Request Detection": {
        "problem": "Teams spend time reviewing duplicate or near-duplicate requests.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Reduces duplicate work and improves intake quality.",
        "tool": "Python matching rules, database constraints, form validation",
        "first_step": "Create duplicate checks using requester, request type, and recent submission window.",
        "repeatability": 78,
        "rule_clarity": 74,
        "save_rate": 0.52,
    },
    "Auto-Routing by Request Type": {
        "problem": "Requests are manually routed even when assignment rules are stable.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Shortens intake time and improves queue visibility.",
        "tool": "Streamlit admin rules, Power Automate, service desk routing rules",
        "first_step": "Build a request-type-to-owner routing matrix.",
        "repeatability": 94,
        "rule_clarity": 88,
        "save_rate": 0.55,
    },
    "SLA Escalation Alerts": {
        "problem": "Aging work is not escalated until it is already late.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves responsiveness and reduces surprise escalations.",
        "tool": "Scheduled Python job, Teams alerts, email digest",
        "first_step": "Define alert thresholds by priority and process stage.",
        "repeatability": 88,
        "rule_clarity": 86,
        "save_rate": 0.44,
    },
    "Request Intake Validation": {
        "problem": "Incomplete requests enter the workflow and create downstream rework.",
        "complexity": "Medium",
        "risk": "Low",
        "impact": "Improves quality at the source and reduces back-and-forth.",
        "tool": "Microsoft Forms, form validation, SharePoint Lists",
        "first_step": "Identify required fields and validation rules for the top request types.",
        "repeatability": 90,
        "rule_clarity": 84,
        "save_rate": 0.58,
    },
    "Recurring Status Summary": {
        "problem": "Leaders lack predictable visibility into work volume and aging.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves management visibility without manual status gathering.",
        "tool": "Scheduled email, Streamlit export, Teams digest",
        "first_step": "Create weekly summary fields and audience list.",
        "repeatability": 84,
        "rule_clarity": 80,
        "save_rate": 0.36,
    },
    "Rework Prevention Checklist": {
        "problem": "Common quality misses cause requests to bounce between teams.",
        "complexity": "Medium",
        "risk": "Low",
        "impact": "Reduces rework, touches, and owner frustration.",
        "tool": "Checklist workflow, form validation, Teams reminder",
        "first_step": "Identify the top five rework causes and convert them into validation checks.",
        "repeatability": 82,
        "rule_clarity": 78,
        "save_rate": 0.5,
    },
}


RESCUEOPS_AUTOMATION_SPECS = {
    "Adoption Inquiry Triage": {
        "problem": "Adoption inquiries wait too long and require manual prioritization.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Improves response time while routing sensitive decisions to humans.",
        "tool": "Streamlit rules engine, Airtable/Sheets, email templates",
        "first_step": "Define triage categories and human-review rules.",
        "repeatability": 88,
        "rule_clarity": 82,
    },
    "Foster Match Recommendation": {
        "problem": "Foster placement depends on manual memory of capacity and capabilities.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Improves foster fit and reduces emergency placement scrambling.",
        "tool": "Rules engine, volunteer database, scheduled digest",
        "first_step": "Capture foster capacity, constraints, and dog needs in one table.",
        "repeatability": 80,
        "rule_clarity": 74,
    },
    "Medical Funding Priority Alert": {
        "problem": "Medical needs compete for attention without a consistent priority view.",
        "complexity": "Low",
        "risk": "Medium",
        "impact": "Improves donor focus and leadership visibility into urgent needs.",
        "tool": "Scheduled report, donation tracker, Streamlit dashboard",
        "first_step": "Map urgency, funding gap, and adoption-readiness impact into a priority score.",
        "repeatability": 84,
        "rule_clarity": 80,
    },
    "Dog Bio/Social Post Generator": {
        "problem": "Adoption-ready dogs wait for bios and social posts.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Increases visibility for adoption-ready dogs and foster needs.",
        "tool": "Template generator, optional AI copy assistant, social queue",
        "first_step": "Create safe copy templates using only approved dog profile fields.",
        "repeatability": 90,
        "rule_clarity": 86,
    },
    "Volunteer Task Reminder": {
        "problem": "Volunteer tasks can fall through when capacity is limited.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves follow-through and reduces founder coordination load.",
        "tool": "Email digest, Teams/Slack reminders, Google Sheets",
        "first_step": "Define task owners, due dates, and escalation reminders.",
        "repeatability": 86,
        "rule_clarity": 82,
    },
    "Weekly Founder Brief": {
        "problem": "Founders need a concise view of dogs, gaps, inquiries, and funding.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Creates leadership visibility without manual spreadsheet review.",
        "tool": "Streamlit report export, scheduled email, Google Docs",
        "first_step": "Standardize the weekly brief sections and source metrics.",
        "repeatability": 92,
        "rule_clarity": 88,
    },
    "Unanswered Message Escalation": {
        "problem": "Messages age past acceptable response windows.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves applicant experience and reduces missed opportunities.",
        "tool": "Email alerts, shared inbox labels, scheduled digest",
        "first_step": "Set response thresholds and escalation owners by inquiry type.",
        "repeatability": 90,
        "rule_clarity": 90,
    },
}


def _normalize(series: pd.Series) -> pd.Series:
    series = series.astype(float)
    span = series.max() - series.min()
    if span == 0:
        return pd.Series(np.ones(len(series)) * 50, index=series.index)
    return ((series - series.min()) / span) * 100


def _complexity_penalty(complexity: str) -> int:
    return {"Low": 18, "Medium": 48, "High": 78}.get(complexity, 50)


def build_opspilot_automation_ranker(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.assign(manual_hours=df["estimated_manual_minutes"] / 60)
        .groupby("automation_candidate_type")
        .agg(
            volume=("request_id", "count"),
            manual_hours=("manual_hours", "sum"),
            sla_breaches=("sla_breached", "sum"),
        )
        .reset_index()
        .rename(columns={"automation_candidate_type": "automation_name"})
    )

    grouped["volume_score"] = _normalize(grouped["volume"])
    grouped["manual_hours_score"] = _normalize(grouped["manual_hours"])
    grouped["sla_impact_score"] = _normalize(grouped["sla_breaches"])

    rows: list[dict] = []
    for _, row in grouped.iterrows():
        spec = OPSPILOT_AUTOMATION_SPECS.get(row["automation_name"], OPSPILOT_AUTOMATION_SPECS["Recurring Status Summary"])
        complexity_score = _complexity_penalty(spec["complexity"])
        score = (
            row["volume_score"] * 0.25
            + row["manual_hours_score"] * 0.25
            + spec["repeatability"] * 0.2
            + row["sla_impact_score"] * 0.15
            + spec["rule_clarity"] * 0.1
            - complexity_score * 0.05
        )
        rows.append(
            {
                "Domain": "OpsPilot",
                "Automation Candidate": row["automation_name"],
                "Problem Solved": spec["problem"],
                "Volume": int(row["volume"]),
                "Estimated Hours Saved": round(row["manual_hours"] * spec["save_rate"], 1),
                "Complexity": spec["complexity"],
                "Risk": spec["risk"],
                "Business/Mission Impact": spec["impact"],
                "Automation Score": round(float(np.clip(score, 0, 100)), 1),
                "Recommended First Step": spec["first_step"],
                "Recommended Implementation Tool": spec["tool"],
            }
        )

    return _rank(pd.DataFrame(rows))


def build_rescueops_automation_ranker(
    dogs: pd.DataFrame, inquiries: pd.DataFrame, volunteers: pd.DataFrame, medical: pd.DataFrame
) -> pd.DataFrame:
    foster_need = len(
        dogs[
            (dogs["current_status"].isin(["Foster Needed", "Intake", "Medical Hold"]))
            | (dogs["foster_status"].isin(["Needs Foster", "Needs Backup", "Boarding"]))
        ]
    )
    medical_priority_cases = len(
        medical[(medical["urgency"].isin(["High", "Critical"])) | (medical["funded_status"] != "Funded")]
    )
    bio_social_need = int((dogs["bio_needed"] | dogs["social_post_needed"]).sum())
    overdue_messages = len(inquiries[inquiries["days_waiting"] > 3])
    open_adoption_inquiries = len(
        inquiries[
            (inquiries["inquiry_type"] == "Adoption Inquiry")
            & (inquiries["response_status"].isin(["New", "In Review", "Overdue", "Escalated"]))
        ]
    )
    active_volunteer_tasks = int(volunteers["current_assignments"].sum())

    base = pd.DataFrame(
        [
            ("Adoption Inquiry Triage", max(open_adoption_inquiries, 1), open_adoption_inquiries * 0.18 + 8, 88),
            ("Foster Match Recommendation", max(foster_need, 1), foster_need * 0.45 + 6, 86),
            ("Medical Funding Priority Alert", max(medical_priority_cases, 1), medical_priority_cases * 0.14 + 5, 92),
            ("Dog Bio/Social Post Generator", max(bio_social_need, 1), bio_social_need * 0.42 + 4, 82),
            ("Volunteer Task Reminder", max(active_volunteer_tasks, 1), active_volunteer_tasks * 0.18 + 5, 74),
            ("Weekly Founder Brief", 4, 7.0, 90),
            ("Unanswered Message Escalation", max(overdue_messages, 1), overdue_messages * 0.15 + 4, 84),
        ],
        columns=["automation_name", "volume", "estimated_hours_saved", "mission_impact_score"],
    )
    base["volume_score"] = _normalize(base["volume"])
    base["manual_hours_score"] = _normalize(base["estimated_hours_saved"])

    rows: list[dict] = []
    for _, row in base.iterrows():
        spec = RESCUEOPS_AUTOMATION_SPECS[row["automation_name"]]
        complexity_score = _complexity_penalty(spec["complexity"])
        score = (
            row["volume_score"] * 0.22
            + row["manual_hours_score"] * 0.24
            + spec["repeatability"] * 0.2
            + row["mission_impact_score"] * 0.19
            + spec["rule_clarity"] * 0.1
            - complexity_score * 0.05
        )
        rows.append(
            {
                "Domain": "RescueOps",
                "Automation Candidate": row["automation_name"],
                "Problem Solved": spec["problem"],
                "Volume": int(row["volume"]),
                "Estimated Hours Saved": round(float(row["estimated_hours_saved"]), 1),
                "Complexity": spec["complexity"],
                "Risk": spec["risk"],
                "Business/Mission Impact": spec["impact"],
                "Automation Score": round(float(np.clip(score, 0, 100)), 1),
                "Recommended First Step": spec["first_step"],
                "Recommended Implementation Tool": spec["tool"],
            }
        )

    return _rank(pd.DataFrame(rows))


def build_combined_automation_ranker(
    opspilot_df: pd.DataFrame,
    dogs: pd.DataFrame,
    inquiries: pd.DataFrame,
    volunteers: pd.DataFrame,
    medical: pd.DataFrame,
) -> pd.DataFrame:
    return _rank(
        pd.concat(
            [
                build_opspilot_automation_ranker(opspilot_df),
                build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical),
            ],
            ignore_index=True,
        ).drop(columns=["Rank"], errors="ignore")
    )


def _rank(df: pd.DataFrame) -> pd.DataFrame:
    ranked = df.sort_values("Automation Score", ascending=False).reset_index(drop=True)
    ranked.insert(0, "Rank", ranked.index + 1)
    return ranked


def get_automation_blueprint(automation_name: str, domain: str, estimated_hours_saved: float | None = None) -> dict:
    spec = (
        OPSPILOT_AUTOMATION_SPECS.get(automation_name)
        if domain == "OpsPilot"
        else RESCUEOPS_AUTOMATION_SPECS.get(automation_name)
    )
    if spec is None:
        spec = {
            "problem": "A repeatable workflow is consuming manual coordination time.",
            "complexity": "Medium",
            "risk": "Medium",
            "impact": "Improves speed, quality, and management visibility.",
            "tool": "Python, Streamlit, workflow automation, and a lightweight database",
            "first_step": "Define the process trigger, owner, rules, and exception path.",
        }

    if domain == "OpsPilot":
        trigger = _opspilot_trigger(automation_name)
        inputs = [
            "request_id",
            "request_type",
            "process_stage",
            "priority",
            "owner",
            "submitted_date",
            "sla_days",
            "required_documents_missing",
            "approval_status",
        ]
        audit = "Log request id, rule triggered, prior status, new status, notification recipient, timestamp, and escalation outcome."
        production = "Connect to Microsoft Graph, SharePoint or service desk data, Teams notifications, role-based access, and durable audit tables."
    else:
        trigger = _rescueops_trigger(automation_name)
        inputs = [
            "dog profile",
            "inquiry details",
            "volunteer capacity",
            "medical status",
            "funding status",
            "human-review flags",
        ]
        audit = "Log case id, recommendation, source fields used, volunteer or founder owner, timestamp, and human decision."
        production = "Connect to the rescue CRM, shared inbox, donation platform, volunteer database, and secure file storage with human approval workflows."

    return {
        "Automation Name": automation_name,
        "Business Problem": spec["problem"],
        "Trigger": trigger,
        "Required Inputs": inputs,
        "Decision Rules": _decision_rules(automation_name, domain),
        "Workflow Steps": _workflow_steps(automation_name, domain),
        "Exception Handling": _exception_handling(automation_name, domain),
        "Notification Logic": _notification_logic(automation_name, domain),
        "Audit Log Requirements": audit,
        "Estimated Hours Saved": f"{estimated_hours_saved:.1f} hours/month" if estimated_hours_saved is not None else "Estimate from current volume and manual effort.",
        "Recommended Tooling": spec["tool"],
        "Implementation Difficulty": spec["complexity"],
        "MVP Build Version": _mvp_version(automation_name, domain),
        "Production Version": production,
    }


def blueprint_to_markdown(blueprint: dict) -> str:
    lines = [f"## {blueprint['Automation Name']}"]
    for key, value in blueprint.items():
        if key == "Automation Name":
            continue
        lines.append(f"\n### {key}")
        if isinstance(value, list):
            lines.extend([f"{idx}. {item}" for idx, item in enumerate(value, start=1)])
        else:
            lines.append(str(value))
    return "\n".join(lines)


def _opspilot_trigger(name: str) -> str:
    if name == "Missing Document Follow-Up":
        return "New request submitted or existing request updated with missing required documents."
    if name == "Approval Reminder Automation":
        return "Approval-required request remains pending beyond the configured reminder window."
    if name == "Duplicate Request Detection":
        return "New request matches a recent open request by requester, request type, or business key."
    if name == "SLA Escalation Alerts":
        return "Request reaches 75%, 100%, or 125% of its SLA target."
    return "New request enters the workflow or a scheduled monitoring job runs."


def _rescueops_trigger(name: str) -> str:
    if name == "Adoption Inquiry Triage":
        return "New inquiry received or unanswered inquiry exceeds response threshold."
    if name == "Foster Match Recommendation":
        return "Dog is marked foster needed, intake, medical hold, or backup foster required."
    if name == "Medical Funding Priority Alert":
        return "Medical expense is added or funding status changes."
    if name == "Dog Bio/Social Post Generator":
        return "Dog is marked bio_needed or social_post_needed."
    return "Scheduled weekly review or change in rescue operations data."


def _decision_rules(name: str, domain: str) -> list[str]:
    if domain == "OpsPilot":
        return [
            "Evaluate the request against SLA age, status, stage, missing document, duplicate, and approval fields.",
            "Route standard cases through deterministic rules and flag ambiguous cases for human owner review.",
            "Escalate high-priority or critical business-impact work faster than standard priority work.",
        ]
    return [
        "Use only structured rescue data and avoid unsupported medical or behavioral claims.",
        "Route medical, safety, adoption, and foster placement decisions to a human reviewer.",
        "Prioritize cases by urgency, days waiting, funding gap, foster gap, and mission impact.",
    ]


def _workflow_steps(name: str, domain: str) -> list[str]:
    if domain == "OpsPilot" and name == "Missing Document Follow-Up":
        return [
            "Detect missing required document.",
            "Move request to Waiting on Requester.",
            "Generate follow-up message with missing items.",
            "Notify requester and assigned owner.",
            "Wait 48 hours.",
            "Send reminder.",
            "Escalate after 5 business days.",
            "Log all actions.",
        ]
    if domain == "RescueOps" and name == "Adoption Inquiry Triage":
        return [
            "Receive inquiry.",
            "Match inquiry to dog profile when available.",
            "Classify triage category.",
            "Generate follow-up questions.",
            "Flag human-review cases.",
            "Create response queue ordered by priority and age.",
            "Log recommendation and reviewer decision.",
        ]
    return [
        "Monitor source data for trigger conditions.",
        "Apply scoring or routing rules.",
        "Generate recommended action.",
        "Notify responsible owner.",
        "Track completion, exceptions, and outcomes.",
        "Summarize results in weekly leadership reporting.",
    ]


def _exception_handling(name: str, domain: str) -> str:
    if domain == "OpsPilot":
        return "High-priority, critical-impact, rejected approval, or ambiguous duplicate cases notify the assigned owner immediately."
    return "Medical, safety, compatibility, surrender, and placement concerns are routed to rescue leadership or the appropriate licensed professional."


def _notification_logic(name: str, domain: str) -> str:
    if domain == "OpsPilot":
        return "Send requester updates for standard cases, owner alerts for aging work, and manager escalations for SLA breach risk."
    return "Send volunteer task notifications for routine work and founder/leadership alerts for urgent medical, foster, or safety cases."


def _mvp_version(name: str, domain: str) -> str:
    if domain == "OpsPilot":
        return "Use CSV or SQLite data, scheduled rule checks, Streamlit review queue, and downloadable leadership report."
    return "Use local rescue CSV data, Streamlit review queue, safe template generation, and weekly founder brief export."
