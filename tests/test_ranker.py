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

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Read-only reuse of the analyzers' load functions so bool coercion matches prod.
from modules.opspilot_analyzer import load_opspilot_data
from modules.rescueops_analyzer import load_rescueops_data
from modules.automation_ranker import (
    build_combined_automation_ranker,
    build_opspilot_automation_ranker,
    build_rescueops_automation_ranker,
)
from modules.roi_calculator import calculate_opspilot_roi, calculate_rescueops_roi

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

    # --- score STABILITY (absolute, not min-max) ---------------------------
    # Drop every row belonging to one row-level candidate ("Missing Document
    # Follow-Up") and confirm another candidate's score is unchanged.
    baseline = r_ops.set_index("Automation Candidate")["Automation Score"]
    reference_name = "SLA Escalation Alerts"
    dropped = ops[~ops["required_documents_missing"].astype(bool)].copy()
    r_ops_dropped = build_opspilot_automation_ranker(dropped)
    dropped_scores = r_ops_dropped.set_index("Automation Candidate")["Automation Score"]
    _check(
        "dropping a candidate's rows leaves another candidate's score unchanged",
        reference_name in dropped_scores.index
        and dropped_scores[reference_name] == baseline[reference_name],
    )
    # Recurring Status Summary is synthetic/org-level -> fully input-independent.
    _check(
        "org-level candidate score is input-independent",
        dropped_scores["Recurring Status Summary"] == baseline["Recurring Status Summary"],
    )

    # --- ROI contract keys -------------------------------------------------
    roi_ops = calculate_opspilot_roi(45, 30, 200, 35, 10, 25)
    expected_ops_keys = {
        "monthly_hours_saved",
        "monthly_labor_savings",
        "annual_labor_savings",
        "estimated_cycle_time_improvement",
        "new_cycle_time_estimate",
        "sla_breach_reduction_estimate",
        "qualitative_business_value",
    }
    _check("opspilot ROI keys exactly match contract", set(roi_ops.keys()) == expected_ops_keys)
    _check("opspilot ROI labor math consistent", roi_ops["annual_labor_savings"] == roi_ops["monthly_labor_savings"] * 12)

    # time_saved_per_request_pct default (70) scales hours below the naive 100%.
    roi_ops_full = calculate_opspilot_roi(45, 30, 200, 35, 10, 25, time_saved_per_request_pct=100.0)
    _check(
        "time_saved_per_request_pct scales hours saved",
        abs(roi_ops["monthly_hours_saved"] - roi_ops_full["monthly_hours_saved"] * 0.7) < 1e-9,
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
