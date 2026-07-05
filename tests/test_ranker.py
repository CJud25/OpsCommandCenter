"""Pytest port of the Workstream B ranker + ROI property tests.

Each assertion maps 1:1 to a ``_check(...)`` in the original script version of
this file; the original's per-frame loops (non-empty, columns, score bounds) are
unrolled into explicit ``assert`` statements, so this suite asserts at least as
many conditions as the original.

Covers, within B's scope only:
- both rankers + the combined ranker build against the shipped ``data/*.csv``;
- every ``Automation Score`` is within [0, 100];
- the display columns exactly match CONTRACTS.md;
- score STABILITY -- a candidate's score is a pure function of its own aggregate
  (absolute, not min-max), and an org-level candidate is input-independent;
- score SENSITIVITY -- doubling a candidate's matching rows raises its score;
- the ROI functions return exactly the contract keys (no removed keys).

The ``main()`` wrapper keeps ``python tests/test_ranker.py`` working; CI runs the
suite via ``python -m pytest``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Read-only reuse of the analyzers' load functions so bool coercion matches prod.
from modules import scoring
from modules.automation_ranker import (
    OPSPILOT_AUTOMATION_SPECS,
    build_combined_automation_ranker,
    build_opspilot_automation_ranker,
    build_rescueops_automation_ranker,
    opspilot_monthly_impact,
)
from modules.opspilot_analyzer import load_opspilot_data
from modules.rescueops_analyzer import load_rescueops_data
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


def _load() -> SimpleNamespace:
    ops = load_opspilot_data(DATA / "opspilot_requests.csv")
    dogs, inquiries, volunteers, medical = load_rescueops_data(
        {
            "dogs": DATA / "rescueops_dogs.csv",
            "inquiries": DATA / "rescueops_inquiries.csv",
            "volunteers": DATA / "rescueops_volunteers.csv",
            "medical": DATA / "rescueops_medical_costs.csv",
        }
    )
    r_ops = build_opspilot_automation_ranker(ops)
    r_res = build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical)
    r_all = build_combined_automation_ranker(ops, dogs, inquiries, volunteers, medical)
    return SimpleNamespace(
        ops=ops,
        dogs=dogs,
        inquiries=inquiries,
        volunteers=volunteers,
        medical=medical,
        r_ops=r_ops,
        r_res=r_res,
        r_all=r_all,
    )


@pytest.fixture(scope="module")
def rk() -> SimpleNamespace:
    return _load()


def test_rankers_nonempty_and_columns(rk: SimpleNamespace) -> None:
    assert len(rk.r_ops) > 0, "opspilot ranker non-empty"
    assert len(rk.r_res) > 0, "rescueops ranker non-empty"
    assert len(rk.r_all) > 0, "combined ranker non-empty"
    assert list(rk.r_ops.columns) == CONTRACT_COLUMNS, "opspilot display columns match CONTRACTS.md"
    assert list(rk.r_res.columns) == CONTRACT_COLUMNS, (
        "rescueops display columns match CONTRACTS.md"
    )
    assert list(rk.r_all.columns) == CONTRACT_COLUMNS, "combined display columns match CONTRACTS.md"


def test_candidate_counts(rk: SimpleNamespace) -> None:
    assert len(rk.r_ops) == 8, "opspilot has all 8 candidates"
    assert len(rk.r_res) == 7, "rescueops has all 7 candidates"
    assert len(rk.r_all) == 15, "combined has 15 candidates"


def test_scores_within_bounds(rk: SimpleNamespace) -> None:
    assert 0.0 <= float(rk.r_ops["Automation Score"].min()) and float(
        rk.r_ops["Automation Score"].max()
    ) <= 100.0, "opspilot scores within [0,100]"
    assert 0.0 <= float(rk.r_res["Automation Score"].min()) and float(
        rk.r_res["Automation Score"].max()
    ) <= 100.0, "rescueops scores within [0,100]"
    assert 0.0 <= float(rk.r_all["Automation Score"].min()) and float(
        rk.r_all["Automation Score"].max()
    ) <= 100.0, "combined scores within [0,100]"


def test_combined_sorted_and_spans_both_domains(rk: SimpleNamespace) -> None:
    # Cross-domain comparability: both domains land on the same 0-100 anchor, so
    # the combined ranking is a straight sort with no per-domain rescale.
    combined_sorted = rk.r_all["Automation Score"].tolist()
    assert combined_sorted == sorted(combined_sorted, reverse=True), (
        "combined is sorted desc by score"
    )
    assert set(rk.r_all["Domain"]) == {"OpsPilot", "RescueOps"}, "combined spans both domains"


def test_score_is_absolute_not_minmax(rk: SimpleNamespace) -> None:
    # Prove it directly: a candidate's score is a pure function of ITS OWN
    # aggregate impact + spec, with no cross-candidate normalization. Recompute one
    # candidate's score in isolation and match the builder.
    baseline = rk.r_ops.set_index("Automation Candidate")["Automation Score"]
    _impact = opspilot_monthly_impact(rk.ops).set_index("automation_name")
    _iso_name = "SLA Escalation Alerts"
    _spec = OPSPILOT_AUTOMATION_SPECS[_iso_name]
    _expected = scoring.absolute_automation_score(
        net_hours_saved=float(_impact.loc[_iso_name, "manual_hours"])
        * scoring.OPSPILOT_SAVE_RATES[_iso_name],
        impact_0_100=scoring.sla_impact_score(float(_impact.loc[_iso_name, "sla_breaches"])),
        repeatability=_spec["repeatability"],
        rule_clarity=_spec["rule_clarity"],
        complexity=_spec["complexity"],
    )
    assert abs(baseline[_iso_name] - _expected) < 1e-9, (
        "candidate score is a pure function of its own aggregate (absolute, not min-max)"
    )
    # Recurring Status Summary is synthetic/org-level -> fully input-independent:
    # its score is identical when built from a strict subset of the requests.
    subset = rk.ops[~rk.ops["required_documents_missing"].astype(bool)].copy()
    subset_scores = build_opspilot_automation_ranker(subset).set_index("Automation Candidate")[
        "Automation Score"
    ]
    assert subset_scores["Recurring Status Summary"] == baseline["Recurring Status Summary"], (
        "org-level candidate score is input-independent"
    )


def test_score_responds_to_volume(rk: SimpleNamespace) -> None:
    # Doubling a row-level candidate's matching rows increases its own score. This
    # guards against effort-term saturation, where all volumes scored identically.
    baseline = rk.r_ops.set_index("Automation Candidate")["Automation Score"]
    dup_name = "SLA Escalation Alerts"
    breached = rk.ops[rk.ops["sla_breached"].astype(bool)]
    doubled = build_opspilot_automation_ranker(pd.concat([rk.ops, breached], ignore_index=True))
    doubled_scores = doubled.set_index("Automation Candidate")["Automation Score"]
    assert doubled_scores[dup_name] > baseline[dup_name], (
        "doubling a candidate's volume raises its score (not saturated)"
    )


def test_opspilot_roi_contract() -> None:
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
    assert set(roi_ops.keys()) == expected_ops_keys, "opspilot ROI keys exactly match contract"
    assert roi_ops["annual_labor_savings"] == roi_ops["monthly_labor_savings"] * 12, (
        "opspilot ROI labor math consistent"
    )
    # The two removed metrics (slider-echo cycle time and the invented SLA formula) stay gone.
    removed_ops = {
        "estimated_cycle_time_improvement",
        "new_cycle_time_estimate",
        "sla_breach_reduction_estimate",
    }
    assert removed_ops.isdisjoint(roi_ops.keys()), (
        "opspilot ROI removed the slider-echo and fabricated metrics"
    )
    # Net-of-cost math: first-year net = 12 * monthly net - one-time build cost.
    assert abs(roi_ops["annual_net_savings"] - (roi_ops["monthly_net_savings"] * 12 - 12000.0)) < 1e-6, (
        "opspilot ROI net-of-cost math consistent"
    )
    # time_saved_per_request_pct scales hours saved linearly.
    roi_half = calculate_opspilot_roi(45, 30, 200, 35, time_saved_per_request_pct=50.0)
    roi_full = calculate_opspilot_roi(45, 30, 200, 35, time_saved_per_request_pct=100.0)
    assert abs(roi_half["monthly_hours_saved"] - roi_full["monthly_hours_saved"] * 0.5) < 1e-9, (
        "time_saved_per_request_pct scales hours saved"
    )


def test_rescueops_roi_contract() -> None:
    roi_res = calculate_rescueops_roi(28, 140, 14, 80, 5000, 35, 45)
    expected_res_keys = {
        "volunteer_hours_saved",
        "monthly_volunteer_value",
        "estimated_inquiries_handled_faster",
        "mission_impact_summary",
    }
    assert set(roi_res.keys()) == expected_res_keys, "rescueops ROI keys exactly match contract"
    removed = {
        "improved_response_capacity",
        "estimated_admin_burden_reduced",
        "medical_funding_visibility_improvement",
    }
    assert removed.isdisjoint(roi_res.keys()), "rescueops ROI removed the three bogus keys"


def main() -> int:
    """Thin runner so ``python tests/test_ranker.py`` still works; it delegates to
    the same test functions pytest collects."""
    data = _load()
    test_rankers_nonempty_and_columns(data)
    test_candidate_counts(data)
    test_scores_within_bounds(data)
    test_combined_sorted_and_spans_both_domains(data)
    test_score_is_absolute_not_minmax(data)
    test_score_responds_to_volume(data)
    test_opspilot_roi_contract()
    test_rescueops_roi_contract()

    print("\n--- Automation scores (comparable across domains) ---")
    for _, row in data.r_all.iterrows():
        print(f"  {row['Automation Score']:6.1f}  {row['Domain']:<10}  {row['Automation Candidate']}")
    print("\nALL RANKER/ROI CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
