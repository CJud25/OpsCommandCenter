"""Tests for the missing-document follow-up micro-automation.

Covers the guarantees the README advertises but were previously unverified:
- first run writes exactly one follow-up + one audit row per missing-doc request;
- re-running is idempotent (zero new files, zero new audit rows);
- --dry-run writes nothing;
- --max-actions caps a run;
- --window-days re-enables a request after its window elapses (reminder ladder);
- a crafted request_id cannot escape the outbox directory.

Run: ``py tests/test_automation.py`` from the repo root. Exit 0 = pass.
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

_failures: list[str] = []


def _check(label: str, condition: bool) -> None:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    if not condition:
        _failures.append(label)


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


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"

        rows = [
            {"request_id": f"REQ-{i:03d}", "required_documents_missing": missing,
             "owner": "Alex", "priority": "High", "submitted_date": "2026-06-01"}
            for i, missing in enumerate(["true", "false", "true", "true", "false"], start=1)
        ]
        _write_csv(data, rows)  # 3 missing-doc requests
        t0 = dt.datetime(2026, 6, 15, 9, 0, 0)

        # --- first run ----------------------------------------------------------
        r1 = run(data, outbox, audit, now=t0)
        _check("first run writes one file per missing-doc request", r1["written"] == 3 and _outbox_count(outbox) == 3)
        _check("first run writes one audit row per action", _audit_rows(audit) == 3)

        # --- idempotent re-run --------------------------------------------------
        r2 = run(data, outbox, audit, now=t0 + dt.timedelta(days=1))
        _check("re-run writes zero new files", r2["written"] == 0 and _outbox_count(outbox) == 3)
        _check("re-run writes zero new audit rows", _audit_rows(audit) == 3 and r2["skipped"] == 3)

        # --- windowed re-trigger ------------------------------------------------
        r3 = run(data, outbox, audit, now=t0 + dt.timedelta(days=40), window_days=30)
        _check(
            "window elapsed -> request chased again as a distinct file",
            r3["written"] == 3 and _audit_rows(audit) == 6 and _outbox_count(outbox) == 6,
        )
        r4 = run(data, outbox, audit, now=t0 + dt.timedelta(days=45), window_days=60)
        _check("still within window -> skipped", r4["written"] == 0)

    # --- dry run (fresh dirs) --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(data, [
            {"request_id": "REQ-1", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
            {"request_id": "REQ-2", "required_documents_missing": "true", "owner": "B", "priority": "Low", "submitted_date": "2026-06-01"},
        ])
        rd = run(data, outbox, audit, dry_run=True)
        _check("dry-run reports would-write count", rd["written"] == 2 and rd["dry_run"] is True)
        _check("dry-run writes no files and no audit log", _outbox_count(outbox) == 0 and not audit.exists())

        # --- circuit breaker ---------------------------------------------------
        rc = run(data, outbox, audit, max_actions=1)
        _check("max-actions caps the run", rc["written"] == 1 and rc["capped"] == 1 and _outbox_count(outbox) == 1)

    # --- zero-byte audit file still gets a header (crash-recovery edge) ---------
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(data, [
            {"request_id": "REQ-1", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
        ])
        audit.write_text("", encoding="utf-8")  # simulate a crash-left empty file
        run(data, outbox, audit)
        # Header must be present, so DictReader parses one action row (not zero).
        _check("empty audit file gets a header written", _audit_rows(audit) == 1)
        r_again = run(data, outbox, audit)
        _check("idempotent after empty-file recovery", r_again["written"] == 0 and _audit_rows(audit) == 1)

    # --- path traversal --------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(data, [
            {"request_id": "../../evil", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
        ])
        run(data, outbox, audit)
        escaped = (base / "evil.txt").exists() or (base.parent / "evil.txt").exists()
        _check("crafted request_id stays inside the outbox", _outbox_count(outbox) == 1 and not escaped)

    # --- CSV formula-injection guard + idempotency consistency -----------------
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        data = base / "requests.csv"
        outbox = base / "outbox"
        audit = base / "audit_log.csv"
        _write_csv(data, [
            {"request_id": "=HYPERLINK(1)", "required_documents_missing": "true", "owner": "A", "priority": "Low", "submitted_date": "2026-06-01"},
        ])
        run(data, outbox, audit)
        raw = audit.read_text(encoding="utf-8")
        # No audit cell may begin a field with a live formula character.
        cells_ok = all(
            not cell.startswith(("=", "+", "@")) or cell.startswith("'")
            for line in raw.splitlines()[1:] for cell in line.split(",")
        )
        _check("formula-like id is neutralized in the audit log", cells_ok and "'=HYPERLINK(1)" in raw)
        r_again = run(data, outbox, audit)
        _check("idempotency holds despite the injection guard", r_again["written"] == 0)

    if _failures:
        print(f"\nFAILED: {len(_failures)} check(s): {_failures}")
        return 1
    print("\nALL AUTOMATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
