"""Thin backward-compatibility wrapper for the headless pipeline smoke test.

The smoke assertions now live as real pytest tests in ``tests/test_smoke.py``.
This wrapper keeps ``python tests/smoke.py`` working for anyone (or any script)
that still invokes it directly; CI runs the whole suite via ``python -m pytest``.

Run:  py tests/smoke.py    (exit code 0 = pass)
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests/ is not a package; make the sibling pytest module importable by path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_smoke import main

if __name__ == "__main__":
    raise SystemExit(main())
