"""Headless smoke test for the OpsPilot analytics pipeline.

Runs every analyzer / ranker / report function end to end and asserts the
contract keys are present and outputs are non-empty. No Streamlit required.

Run:  py tests/smoke.py
Exit code 0 = pass. Each workstream keeps this green before merge.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Allow running from the repo root without installation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.data_generator import ensure_data  # noqa: E402
from modules import classification as cl  # noqa: E402
from modules import scoring as sc  # noqa: E402


def _check(name: str, cond: bool) -> None:
    if not cond:
        raise AssertionError(f"FAIL: {name}")
    print(f"  ok: {name}")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        paths = ensure_data(Path(tmp) / "data", force=True)

        from modules.opspilot_analyzer import (
            load_opspilot_data,
            summarize_opspilot,
            detect_bottlenecks,
        )
        from modules.rescueops_analyzer import (
            load_rescueops_data,
            summarize_rescueops,
            triage_adoption_inquiries,
            foster_matching,
            medical_priority_scoring,
        )
        from modules.automation_ranker import (
            build_opspilot_automation_ranker,
            build_rescueops_automation_ranker,
            build_combined_automation_ranker,
        )
        from modules.roi_calculator import calculate_opspilot_roi, calculate_rescueops_roi
        from modules.report_generator import generate_opspilot_report, generate_rescueops_report

        ops = load_opspilot_data(paths["opspilot"])
        dogs, inquiries, volunteers, medical = load_rescueops_data(paths)

        # --- classification / scoring invariants -------------------------------
        membership = cl.candidate_membership(ops)
        _check("membership multi-membership exists", int((membership.sum(axis=1) > 1).sum()) > 0)
        primary = cl.primary_candidate(ops, membership)
        manual_hours = (ops["estimated_manual_minutes"] / 60.0)
        attributed = manual_hours.groupby(primary).sum().sum()
        _check("no double-count: attributed <= total", attributed <= manual_hours.sum() + 1e-6)
        _check("blended save rate in (0,1)", 0 < cl.blended_save_rate(ops, membership) < 1)
        _check("score reaches 100 at max inputs", sc.absolute_automation_score(1000, 100, 100, 100, "Low") == 100.0)

        # --- opspilot ----------------------------------------------------------
        s = summarize_opspilot(ops)
        for k in ("total_requests", "sla_breach_rate", "top_automation_candidate", "potential_monthly_savings"):
            _check(f"opspilot summary has {k}", k in s)
        b = detect_bottlenecks(ops)
        _check("bottlenecks non-empty", len(b) > 0)

        # --- rescueops ---------------------------------------------------------
        rs = summarize_rescueops(dogs, inquiries, volunteers, medical)
        for k in ("dogs_in_care", "unanswered_messages", "highest_priority_dog"):
            _check(f"rescue summary has {k}", k in rs)
        _check("triage non-empty", len(triage_adoption_inquiries(inquiries, dogs)) > 0)
        _check("foster matching non-empty", len(foster_matching(dogs, volunteers)) > 0)
        _check("medical scoring non-empty", len(medical_priority_scoring(dogs, medical)) > 0)

        # --- rankers -----------------------------------------------------------
        r_ops = build_opspilot_automation_ranker(ops)
        r_res = build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical)
        r_all = build_combined_automation_ranker(ops, dogs, inquiries, volunteers, medical)
        for name, r in (("opspilot", r_ops), ("rescueops", r_res), ("combined", r_all)):
            _check(f"{name} ranker has Automation Score", "Automation Score" in r.columns and len(r) > 0)
        _check("scores within 0-100", float(r_all["Automation Score"].max()) <= 100 and float(r_all["Automation Score"].min()) >= 0)

        # --- roi + reports -----------------------------------------------------
        roi_ops = calculate_opspilot_roi(45, 30, 200, 35)
        roi_res = calculate_rescueops_roi(28, 140, 14, 80, 5000, 35, 45)
        _check("opspilot roi labor math", roi_ops["annual_labor_savings"] == roi_ops["monthly_labor_savings"] * 12)
        _check("opspilot roi exposes payback + net keys", {"payback_months", "annual_net_savings", "first_year_roi_pct"} <= set(roi_ops))
        _check("opspilot report non-empty", len(generate_opspilot_report(s, b, r_ops, roi_ops)) > 200)
        _check("rescue report non-empty", len(generate_rescueops_report(rs, medical_priority_scoring(dogs, medical), r_res, "brief", roi_res)) > 200)

    print("\nSMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
