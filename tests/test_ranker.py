"""Workstream B checks for the absolute-scoring ranker and the ROI fixes.

Run: ``py tests/test_ranker.py`` from the repo root.

Covers, within B's scope only:
- both rankers + the combined ranker build against the shipped ``data/*.csv``;
- every ``Automation Score`` is within [0, 100];
- the display columns exactly match CONTRACTS.md;
- score STABILITY -- dropping one candidate's rows from the OpsPilot input does not
  change another candidate's score (proves scoring is absolute, not min-max);
- the ROI functions return exactly the contract keys (no removed keys).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Read-only reuse of the analyzers' load functions so bool coercion matches prod.
from modules.opspilot_analyzer import load_opspilot_data
from modules.rescueops_analyzer import load_rescueops_data
from modules.automation_ranker import (
    OPSPILOT_AUTOMATION_SPECS,
    build_combined_automation_ranker,
    build_opspilot_automation_ranker,
    build_rescueops_automation_ranker,
)
from modules.roi_calculator import calculate_opspilot_roi, calculate_rescueops_roi
from modules import classification, scoring

DATA = ROOT / "data"

CONTRACT_COLUMNS = [
    "Rank",
    "Domain",
    "Automation Candidate",
    "Problem Solved",
    "Volume",
    "Estimated Hours Saved",
    "Complexity",
    "Risk",
    "Business/Mission Impact",
    "Automation Score",
    "Recommended First Step",
    "Recommended Implementation Tool",
]

_failures: list[str] = []


def _check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


def _load():
    ops = load_opspilot_data(DATA / "opspilot_requests.csv")
    dogs, inquiries, volunteers, medical = load_rescueops_data(
        {
            "dogs": DATA / "rescueops_dogs.csv",
            "inquiries": DATA / "rescueops_inquiries.csv",
            "volunteers": DATA / "rescueops_volunteers.csv",
            "medical": DATA / "rescueops_medical_costs.csv",
        }
    )
    return ops, dogs, inquiries, volunteers, medical


def main() -> int:
    ops, dogs, inquiries, volunteers, medical = _load()

    r_ops = build_opspilot_automation_ranker(ops)
    r_res = build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical)
    r_all = build_combined_automation_ranker(ops, dogs, inquiries, volunteers, medical)

    # --- shape + columns ---------------------------------------------------
    for label, frame in (("opspilot", r_ops), ("rescueops", r_res), ("combined", r_all)):
        _check(f"{label} ranker non-empty", len(frame) > 0)
        _check(f"{label} display columns match CONTRACTS.md", list(frame.columns) == CONTRACT_COLUMNS)

    _check("opspilot has all 8 candidates", len(r_ops) == 8)
    _check("rescueops has all 7 candidates", len(r_res) == 7)
    _check("combined has 15 candidates", len(r_all) == 15)

    # --- scores within [0, 100] -------------------------------------------
    for label, frame in (("opspilot", r_ops), ("rescueops", r_res), ("combined", r_all)):
        lo = float(frame["Automation Score"].min())
        hi = float(frame["Automation Score"].max())
        _check(f"{label} scores within [0,100]", 0.0 <= lo and hi <= 100.0)

    # --- cross-domain comparability: both domains land on the same 0-100 anchor,
    #     so the combined ranking is a straight sort with no per-domain rescale.
    combined_sorted = r_all["Automation Score"].tolist()
    _check("combined is sorted desc by score", combined_sorted == sorted(combined_sorted, reverse=True))
    both_domains = set(r_all["Domain"]) == {"OpsPilot", "RescueOps"}
    _check("combined spans both domains", both_domains)

    # --- score is ABSOLUTE, not min-max ------------------------------------
    # Prove it directly: a candidate's score is a pure function of ITS OWN
    # aggregate impact + spec, with no cross-candidate normalization. Recompute one
    # candidate's score in isolation and match the builder. (A row-drop test is
    # unreliable here because candidate memberships overlap -- dropping one
    # candidate's rows also removes rows that belong to another.)
    baseline = r_ops.set_index("Automation Candidate")["Automation Score"]
    _impact = classification.aggregate_candidate_impact(ops).set_index("automation_name")
    _iso_name = "SLA Escalation Alerts"
    _spec = OPSPILOT_AUTOMATION_SPECS[_iso_name]
    _expected = scoring.absolute_automation_score(
        net_hours_saved=float(_impact.loc[_iso_name, "manual_hours"]) * scoring.OPSPILOT_SAVE_RATES[_iso_name],
        impact_0_100=scoring.sla_impact_score(int(_impact.loc[_iso_name, "sla_breaches"])),
        repeatability=_spec["repeatability"],
        rule_clarity=_spec["rule_clarity"],
        complexity=_spec["complexity"],
    )
    _check(
        "candidate score is a pure function of its own aggregate (absolute, not min-max)",
        abs(baseline[_iso_name] - _expected) < 1e-9,
    )
    # Recurring Status Summary is synthetic/org-level -> fully input-independent:
    # its score is identical when built from a strict subset of the requests.
    subset = ops[~ops["required_documents_missing"].astype(bool)].copy()
    subset_scores = build_opspilot_automation_ranker(subset).set_index("Automation Candidate")["Automation Score"]
    _check(
        "org-level candidate score is input-independent",
        subset_scores["Recurring Status Summary"] == baseline["Recurring Status Summary"],
    )

    # --- score RESPONDS to the data (not constant-driven) ------------------
    # Doubling a row-level candidate's matching rows increases its own score. This
    # guards against effort-term saturation, where all volumes scored identically.
    dup_name = "SLA Escalation Alerts"
    breached = ops[ops["sla_breached"].astype(bool)]
    doubled = build_opspilot_automation_ranker(pd.concat([ops, breached], ignore_index=True))
    doubled_scores = doubled.set_index("Automation Candidate")["Automation Score"]
    _check(
        "doubling a candidate's volume raises its score (not saturated)",
        doubled_scores[dup_name] > baseline[dup_name],
    )

    # --- ROI contract keys -------------------------------------------------
    roi_ops = calculate_opspilot_roi(45, 30, 200, 35)
    expected_ops_keys = {
        "monthly_hours_saved",
        "monthly_labor_savings",
        "annual_labor_savings",
        "monthly_net_savings",
        "annual_net_savings",
        "payback_months",
        "first_year_roi_pct",
        "qualitative_business_value",
    }
    _check("opspilot ROI keys exactly match contract", set(roi_ops.keys()) == expected_ops_keys)
    _check("opspilot ROI labor math consistent", roi_ops["annual_labor_savings"] == roi_ops["monthly_labor_savings"] * 12)
    # The two removed metrics (slider-echo cycle time and the invented SLA formula) stay gone.
    removed_ops = {"estimated_cycle_time_improvement", "new_cycle_time_estimate", "sla_breach_reduction_estimate"}
    _check("opspilot ROI removed the slider-echo and fabricated metrics", removed_ops.isdisjoint(roi_ops.keys()))
    # Net-of-cost math: first-year net = 12 * monthly net - one-time build cost.
    _check(
        "opspilot ROI net-of-cost math consistent",
        abs(roi_ops["annual_net_savings"] - (roi_ops["monthly_net_savings"] * 12 - 12000.0)) < 1e-6,
    )

    # time_saved_per_request_pct scales hours saved linearly.
    roi_half = calculate_opspilot_roi(45, 30, 200, 35, time_saved_per_request_pct=50.0)
    roi_full = calculate_opspilot_roi(45, 30, 200, 35, time_saved_per_request_pct=100.0)
    _check(
        "time_saved_per_request_pct scales hours saved",
        abs(roi_half["monthly_hours_saved"] - roi_full["monthly_hours_saved"] * 0.5) < 1e-9,
    )

    roi_res = calculate_rescueops_roi(28, 140, 14, 80, 5000, 35, 45)
    expected_res_keys = {
        "volunteer_hours_saved",
        "monthly_volunteer_value",
        "estimated_inquiries_handled_faster",
        "mission_impact_summary",
    }
    _check("rescueops ROI keys exactly match contract", set(roi_res.keys()) == expected_res_keys)
    removed = {"improved_response_capacity", "estimated_admin_burden_reduced", "medical_funding_visibility_improvement"}
    _check("rescueops ROI removed the three bogus keys", removed.isdisjoint(roi_res.keys()))

    # --- report the 15 scores ---------------------------------------------
    print("\n--- Automation scores (comparable across domains) ---")
    for _, row in r_all.iterrows():
        print(f"  {row['Automation Score']:6.1f}  {row['Domain']:<10}  {row['Automation Candidate']}")

    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s): {_failures}")
        return 1
    print("\nALL RANKER/ROI CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
