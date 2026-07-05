"""Shared scoring and reference helpers used across the analytics modules.

This module centralizes small pieces of logic that used to be duplicated (or
buried as magic numbers) in the analyzer and ranker modules:

- ``_normalize``      -- min-max scaling to 0-100 (was pasted into three files).
- ``PRIORITY_ORDER``  -- the canonical severity ranking (Critical highest).
- ``data_today``      -- anchors "recency" windows to the dataset instead of the
                         wall clock, so KPIs never silently decay to $0 as the
                         committed synthetic data ages.
- ``OPSPILOT_SAVE_RATES`` / ``ASSUMED_AUTOMATION_COVERAGE`` -- the two named
                         assumptions behind savings estimates. They are kept
                         separate on purpose: *coverage* (share of eligible
                         requests we actually automate) is a different quantity
                         from *save rate* (time removed per automated request).
- ``absolute_automation_score`` -- an absolute-anchor score (0-100) that is
                         stable when candidates are added/removed and directly
                         comparable across the OpsPilot and RescueOps domains.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# Severity ranking. Higher number = more urgent. Used anywhere a priority column
# must be sorted or compared (never sort the raw strings -- "Medium" > "Critical"
# alphabetically, which is the opposite of intent).
PRIORITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}


# Time removed per automated request, by OpsPilot automation candidate. These are
# planning assumptions (rounded, defensible), not measured values. Sourced from the
# automation blueprint specs; kept here so the ranker and the savings math agree.
OPSPILOT_SAVE_RATES = {
    "Missing Document Follow-Up": 0.62,
    "Approval Reminder Automation": 0.48,
    "Duplicate Request Detection": 0.52,
    "Auto-Routing by Request Type": 0.55,
    "SLA Escalation Alerts": 0.44,
    "Request Intake Validation": 0.58,
    "Recurring Status Summary": 0.36,
    "Rework Prevention Checklist": 0.50,
}

# Share of eligible manual work we assume is actually automated in the MVP
# scenario. Matches the default "Percent automated" control on the ROI page so the
# home-page savings figure and the ROI page tell a consistent story.
ASSUMED_AUTOMATION_COVERAGE = 0.35

# Ease-of-implementation credit by complexity band (higher = easier to ship).
# Replaces the old negative "complexity penalty" so the score can actually reach
# 100 and every term is additive.
EASE_BY_COMPLEXITY = {"Low": 100, "Medium": 55, "High": 25}

# Diminishing-returns scale (in monthly hours saved) for the effort term. The
# term is 1 - exp(-hours/scale), so it never hard-saturates: every additional
# hour saved still raises the score, just with diminishing marginal weight. This
# replaces an earlier hard ceiling that pinned most candidates to the same effort
# value -- which made the "data-driven" ranking effectively constant-driven and
# insensitive to volume. At scale=60: ~26h -> 35, ~60h -> 63, ~120h -> 86.
EFFORT_SCALE_HOURS = 60.0
# Diminishing-returns scale (in monthly breaches) for the SLA impact term.
SLA_SCALE_BREACHES = 40.0


def _diminishing(value: float, scale: float) -> float:
    """Map a non-negative magnitude to 0-100 with diminishing returns.

    Monotonic and strictly increasing (so doubling the input always raises the
    score) but with a soft knee, so a huge outlier does not dwarf everything else.
    """
    return float(100.0 * (1.0 - np.exp(-max(0.0, value) / scale)))


def _normalize(series: pd.Series) -> pd.Series:
    """Min-max scale a series to 0-100. Degenerate (all-equal) input maps to 50."""
    series = series.astype(float)
    span = series.max() - series.min()
    if span == 0:
        return pd.Series(np.ones(len(series)) * 50, index=series.index)
    return ((series - series.min()) / span) * 100


def data_today(df: pd.DataFrame, date_col: str) -> pd.Timestamp:
    """Reference "today" anchored to the newest date in the dataset.

    Recency windows (for example "last 30 days") are measured backwards from this
    point rather than from the wall clock, so metrics stay stable no matter when
    the demo is opened.
    """
    return pd.Timestamp(pd.to_datetime(df[date_col]).max())


def absolute_automation_score(
    net_hours_saved: float,
    impact_0_100: float,
    repeatability: float,
    rule_clarity: float,
    complexity: str,
) -> float:
    """Automation opportunity score on an absolute 0-100 scale.

    Anchored (not min-max normalized), so a score does not shift with which other
    candidates are present, and every domain is scored on the SAME 0-100 curve.

    The effort term (35% weight) is driven by ``net_hours_saved`` -- the estimated
    monthly hours an automation actually removes (gross manual hours x save rate).
    Both domains feed this SAME shared, data-derived quantity into the SAME curve;
    that shared effort anchor is what keeps OpsPilot and RescueOps on one comparable
    scale. The impact term (15%) is domain-specific by design: a measured SLA-breach
    signal for OpsPilot vs. a leadership-set mission weight for RescueOps.

    Weights sum to 1.0 and every term is additive; 100 is approached at large inputs.
      35% effort saved, 20% repeatability, 15% impact, 15% rule clarity, 15% ease.
    """
    effort = _diminishing(net_hours_saved, EFFORT_SCALE_HOURS)
    ease = EASE_BY_COMPLEXITY.get(complexity, 55)
    score = (
        0.35 * effort
        + 0.20 * repeatability
        + 0.15 * impact_0_100
        + 0.15 * rule_clarity
        + 0.15 * ease
    )
    return round(float(np.clip(score, 0, 100)), 1)


def sla_impact_score(sla_breaches: float) -> float:
    """Map a monthly SLA-breach count to the 0-100 impact term used in scoring.

    Same diminishing-returns curve as the effort term so a very high breach count
    does not pin every candidate to the same impact value.
    """
    return _diminishing(float(sla_breaches), SLA_SCALE_BREACHES)
