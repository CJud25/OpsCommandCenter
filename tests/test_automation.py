"""Pytest port of the missing-document follow-up micro-automation tests.

Each assertion maps 1:1 to a ``_check(...)`` in the original script version of
this file. Covers the guarantees the README advertises:
- first run writes exactly one follow-up + one audit row per missing-doc request;
- re-running is idempotent (zero new files, zero new audit rows);
- --dry-run writes nothing;
- --max-actions caps a run;
- --window-days re-enables a request after its window elapses (reminder ladder);
- a crafted request_id cannot escape the outbox directory;
- a formula-like request_id is neutralized in the audit log.

The ``main()`` wrapper keeps ``python tests/test_automation.py`` working; CI runs
the suite via ``python -m pytest``.
"""

from __future__ import annotations

import csv
import datetime as dt
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automations.missing_document_followup import run


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = ["request_id", "required_documents_missing", "owner", "priority", "submitted_date"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _audit_rows(audit_log: Path) -> int:
    if not audit_log.exists():
        return 0
    with audit_log.open("r", newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _outbox_count(outbox: Path) -> int:
    return len(list(outbox.glob("*.txt"))) if outbox.exists() else 0


def test_first_run_idempotency_and_reminder_ladder() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"

        rows = [
            {
                "request_id": f"REQ-{i:03d}",
                "required_documents_missing": missing,
                "owner": "Alex",
                "priority": "High",
                "submitted_date": "2026-06-01",
            }
            for i, missing in enumerate(["true", "false", "true", "true", "false"], start=1)
        ]
        _write_csv(data, rows)  # 3 missing-doc requests
        t0 = dt.datetime(2026, 6, 15, 9, 0, 0)

        # --- first run ---
        r1 = run(data, outbox, audit, now=t0)
        assert r1["written"] == 3 and _outbox_count(outbox) == 3, (
            "first run writes one file per missing-doc request"
        )
        assert _audit_rows(audit) == 3, "first run writes one audit row per action"

        # --- idempotent re-run ---
        r2 = run(data, outbox, audit, now=t0 + dt.timedelta(days=1))
        assert r2["written"] == 0 and _outbox_count(outbox) == 3, "re-run writes zero new files"
        assert _audit_rows(audit) == 3 and r2["skipped"] == 3, "re-run writes zero new audit rows"

        # --- windowed re-trigger ---
        r3 = run(data, outbox, audit, now=t0 + dt.timedelta(days=40), window_days=30)
        assert r3["written"] == 3 and _audit_rows(audit) == 6 and _outbox_count(outbox) == 6, (
            "window elapsed -> request chased again as a distinct file"
        )
        r4 = run(data, outbox, audit, now=t0 + dt.timedelta(days=45), window_days=60)
        assert r4["written"] == 0, "still within window -> skipped"


def test_dry_run_and_circuit_breaker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(
            data,
            [
                {"request_id": "REQ-1", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
                {"request_id": "REQ-2", "required_documents_missing": "true", "owner": "B", "priority": "Low", "submitted_date": "2026-06-01"},
            ],
        )
        rd = run(data, outbox, audit, dry_run=True)
        assert rd["written"] == 2 and rd["dry_run"] is True, "dry-run reports would-write count"
        assert _outbox_count(outbox) == 0 and not audit.exists(), (
            "dry-run writes no files and no audit log"
        )

        # --- circuit breaker ---
        rc = run(data, outbox, audit, max_actions=1)
        assert rc["written"] == 1 and rc["capped"] == 1 and _outbox_count(outbox) == 1, (
            "max-actions caps the run"
        )


def test_empty_audit_file_recovery() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(
            data,
            [
                {"request_id": "REQ-1", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
            ],
        )
        audit.write_text("", encoding="utf-8")  # simulate a crash-left empty file
        run(data, outbox, audit)
        # Header must be present, so DictReader parses one action row (not zero).
        assert _audit_rows(audit) == 1, "empty audit file gets a header written"
        r_again = run(data, outbox, audit)
        assert r_again["written"] == 0 and _audit_rows(audit) == 1, (
            "idempotent after empty-file recovery"
        )


def test_path_traversal_defense() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(
            data,
            [
                {"request_id": "../../evil", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
            ],
        )
        run(data, outbox, audit)
        escaped = (base / "evil.txt").exists() or (base.parent / "evil.txt").exists()
        assert _outbox_count(outbox) == 1 and not escaped, (
            "crafted request_id stays inside the outbox"
        )


def test_csv_formula_injection_guard() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(
            data,
            [
                {"request_id": "=HYPERLINK(1)", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
            ],
        )
        run(data, outbox, audit)
        raw = audit.read_text(encoding="utf-8")
        # No audit cell may begin a field with a live formula character.
        cells_ok = all(
            not cell.startswith(("=", "+", "@")) or cell.startswith("'")
            for line in raw.splitlines()[1:]
            for cell in line.split(",")
        )
        assert cells_ok and "'=HYPERLINK(1)" in raw, (
            "formula-like id is neutralized in the audit log"
        )
        r_again = run(data, outbox, audit)
        assert r_again["written"] == 0, "idempotency holds despite the injection guard"


def main() -> int:
    """Thin runner so ``python tests/test_automation.py`` still works; it delegates
    to the same test functions pytest collects."""
    test_first_run_idempotency_and_reminder_ladder()
    test_dry_run_and_circuit_breaker()
    test_empty_audit_file_recovery()
    test_path_traversal_defense()
    test_csv_formula_injection_guard()
    print("ALL AUTOMATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
