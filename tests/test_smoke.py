"""Pytest port of the headless OpsPilot pipeline smoke test.

Every assertion here maps 1:1 to a ``_check(...)`` in the original
``tests/smoke.py`` script (now a thin wrapper that calls ``main`` below). The
original's loop-based checks (the summary-key loops and the per-ranker loop) are
unrolled into explicit ``assert`` statements, so this suite asserts at least as
many conditions as the original.

Runs every analyzer / ranker / report function end to end and asserts the
contract keys are present and outputs are non-empty. No Streamlit required.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules import classification as cl
from modules import scoring as sc
from modules.automation_ranker import (
    build_combined_automation_ranker,
    build_opspilot_automation_ranker,
    build_rescueops_automation_ranker,
)
from modules.data_generator import ensure_data
from modules.opspilot_analyzer import (
    detect_bottlenecks,
    load_opspilot_data,
    summarize_opspilot,
)
from modules.report_generator import generate_opspilot_report, generate_rescueops_report
from modules.rescueops_analyzer import (
    foster_matching,
    load_rescueops_data,
    medical_priority_scoring,
    summarize_rescueops,
    triage_adoption_inquiries,
)
from modules.roi_calculator import calculate_opspilot_roi, calculate_rescueops_roi


def _build_pipeline() -> SimpleNamespace:
    """Generate synthetic data in a temp dir and load every frame into memory.

    Mirrors the original smoke script's end-to-end run: it exercises the data
    generation path (``ensure_data(force=True)``) and every loader. Frames are
    read into memory before the temp dir is torn down, so callers get a
    self-contained namespace.
    """
    with tempfile.TemporaryDirectory() as tmp:
        paths = ensure_data(Path(tmp) / "data", force=True)
        generated_files_exist = all(Path(p).exists() for p in paths.values())
        ops = load_opspilot_data(paths["opspilot"])
        dogs, inquiries, volunteers, medical = load_rescueops_data(paths)
    return SimpleNamespace(
        ops=ops,
        dogs=dogs,
        inquiries=inquiries,
        volunteers=volunteers,
        medical=medical,
        generated_files_exist=generated_files_exist,
    )


@pytest.fixture(scope="module")
def pipeline() -> SimpleNamespace:
    return _build_pipeline()


def test_data_generation_produces_all_files(pipeline: SimpleNamespace) -> None:
    # End-to-end data-generation path the original smoke script exercised.
    assert pipeline.generated_files_exist, "ensure_data(force=True) wrote every dataset file"


def test_classification_scoring_invariants(pipeline: SimpleNamespace) -> None:
    ops = pipeline.ops
    membership = cl.candidate_membership(ops)
    assert int((membership.sum(axis=1) > 1).sum()) > 0, "membership multi-membership exists"
    primary = cl.primary_candidate(ops, membership)
    manual_hours = ops["estimated_manual_minutes"] / 60.0
    attributed = manual_hours.groupby(primary).sum().sum()
    assert attributed <= manual_hours.sum() + 1e-6, "no double-count: attributed <= total"
    assert 0 < cl.blended_save_rate(ops, membership) < 1, "blended save rate in (0,1)"
    assert sc.absolute_automation_score(1000, 100, 100, 100, "Low") == 100.0, (
        "score reaches 100 at max inputs"
    )


def test_opspilot_summary_and_bottlenecks(pipeline: SimpleNamespace) -> None:
    s = summarize_opspilot(pipeline.ops)
    assert "total_requests" in s, "opspilot summary has total_requests"
    assert "sla_breach_rate" in s, "opspilot summary has sla_breach_rate"
    assert "top_automation_candidate" in s, "opspilot summary has top_automation_candidate"
    assert "potential_monthly_savings" in s, "opspilot summary has potential_monthly_savings"
    b = detect_bottlenecks(pipeline.ops)
    assert len(b) > 0, "bottlenecks non-empty"


def test_rescueops_summary_and_functions(pipeline: SimpleNamespace) -> None:
    rs = summarize_rescueops(
        pipeline.dogs, pipeline.inquiries, pipeline.volunteers, pipeline.medical
    )
    assert "dogs_in_care" in rs, "rescue summary has dogs_in_care"
    assert "unanswered_messages" in rs, "rescue summary has unanswered_messages"
    assert "highest_priority_dog" in rs, "rescue summary has highest_priority_dog"
    assert len(triage_adoption_inquiries(pipeline.inquiries, pipeline.dogs)) > 0, (
        "triage non-empty"
    )
    assert len(foster_matching(pipeline.dogs, pipeline.volunteers)) > 0, (
        "foster matching non-empty"
    )
    assert len(medical_priority_scoring(pipeline.dogs, pipeline.medical)) > 0, (
        "medical scoring non-empty"
    )


def test_rescueops_empty_input_regression(pipeline: SimpleNamespace) -> None:
    # On real data with zero foster-need dogs / zero adoption inquiries these must
    # return a well-formed empty frame, not crash.
    dogs, inquiries, volunteers = pipeline.dogs, pipeline.inquiries, pipeline.volunteers
    empty_dogs = dogs[dogs["current_status"] == "__no_such_status__"]
    empty_inq = inquiries[inquiries["inquiry_type"] == "__no_such_type__"]
    fm_empty = foster_matching(empty_dogs, volunteers)
    assert len(fm_empty) == 0 and "match_score" in fm_empty.columns, (
        "foster matching empty -> framed empty (no KeyError)"
    )
    tr_empty = triage_adoption_inquiries(empty_inq, dogs)
    assert len(tr_empty) == 0 and "triage_category" in tr_empty.columns, (
        "triage empty -> framed empty (no KeyError)"
    )


def test_rankers_build_with_score_column(pipeline: SimpleNamespace) -> None:
    ops, dogs, inquiries, volunteers, medical = (
        pipeline.ops,
        pipeline.dogs,
        pipeline.inquiries,
        pipeline.volunteers,
        pipeline.medical,
    )
    r_ops = build_opspilot_automation_ranker(ops)
    r_res = build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical)
    r_all = build_combined_automation_ranker(ops, dogs, inquiries, volunteers, medical)
    assert "Automation Score" in r_ops.columns and len(r_ops) > 0, (
        "opspilot ranker has Automation Score"
    )
    assert "Automation Score" in r_res.columns and len(r_res) > 0, (
        "rescueops ranker has Automation Score"
    )
    assert "Automation Score" in r_all.columns and len(r_all) > 0, (
        "combined ranker has Automation Score"
    )
    assert (
        float(r_all["Automation Score"].max()) <= 100
        and float(r_all["Automation Score"].min()) >= 0
    ), "scores within 0-100"


def test_roi_and_reports(pipeline: SimpleNamespace) -> None:
    ops, dogs, inquiries, volunteers, medical = (
        pipeline.ops,
        pipeline.dogs,
        pipeline.inquiries,
        pipeline.volunteers,
        pipeline.medical,
    )
    s = summarize_opspilot(ops)
    b = detect_bottlenecks(ops)
    rs = summarize_rescueops(dogs, inquiries, volunteers, medical)
    r_ops = build_opspilot_automation_ranker(ops)
    r_res = build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical)
    roi_ops = calculate_opspilot_roi(45, 30, 200, 35)
    roi_res = calculate_rescueops_roi(28, 140, 14, 80, 5000, 35, 45)
    assert roi_ops["annual_labor_savings"] == roi_ops["monthly_labor_savings"] * 12, (
        "opspilot roi labor math"
    )
    assert {"payback_months", "annual_net_savings", "first_year_roi_pct"} <= set(roi_ops), (
        "opspilot roi exposes payback + net keys"
    )
    assert len(generate_opspilot_report(s, b, r_ops, roi_ops)) > 200, "opspilot report non-empty"
    assert (
        len(
            generate_rescueops_report(
                rs, medical_priority_scoring(dogs, medical), r_res, "brief", roi_res
            )
        )
        > 200
    ), "rescue report non-empty"


def main() -> int:
    """Thin runner so ``python tests/test_smoke.py`` still works; it delegates to
    the same test functions pytest collects."""
    data = _build_pipeline()
    test_data_generation_produces_all_files(data)
    test_classification_scoring_invariants(data)
    test_opspilot_summary_and_bottlenecks(data)
    test_rescueops_summary_and_functions(data)
    test_rescueops_empty_input_regression(data)
    test_rankers_build_with_score_column(data)
    test_roi_and_reports(data)
    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
