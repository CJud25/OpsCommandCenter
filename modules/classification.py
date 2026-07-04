"""OpsPilot automation-candidate classification.

Previously the automation candidate for each request was baked into the synthetic
data by ``data_generator`` and the ranker merely grouped on that column -- the
"analysis" only re-displayed a label the data already carried. This module moves
the classification into the analytics layer: it derives candidacy from the raw
request fields, so the exact same logic runs unchanged on real operational data.

Two views are provided on purpose:

- **Membership** (``candidate_membership`` / ``aggregate_candidate_impact``):
  a request can qualify for MULTIPLE automations (a missing-document request that
  is also SLA-breached is an opportunity for both). Per-candidate impact therefore
  overlaps -- correct for *opportunity sizing* ("how much is this one automation
  worth"), but the hours must not be summed across candidates.

- **Primary attribution** (``primary_candidate`` / ``blended_save_rate``):
  each request is assigned to a single candidate (the qualifying automation with
  the highest save rate). Used for *portfolio totals* so manual hours are counted
  exactly once.

Only the seven row-level candidates live here. "Recurring Status Summary" is an
org-level reporting automation with no per-request trigger, so the ranker adds it
as a synthetic row rather than a mask.
"""

from __future__ import annotations

import pandas as pd

from modules.scoring import OPSPILOT_SAVE_RATES


# Request types whose routing is stable enough to automate assignment.
_AUTO_ROUTE_TYPES = {"Access Request", "Training Assignment", "Equipment Request"}


# name -> predicate(df) returning a boolean Series aligned to df.index.
# Ported field-for-field from the generator's original cascade, but as independent
# (overlapping) masks instead of a first-match-wins if/elif chain.
OPSPILOT_CANDIDATE_RULES: dict[str, "callable"] = {
    "Missing Document Follow-Up": lambda df: df["required_documents_missing"].astype(bool),
    "Approval Reminder Automation": lambda df: df["approval_status"].eq("Pending"),
    "Duplicate Request Detection": lambda df: df["duplicate_flag"].astype(bool),
    "SLA Escalation Alerts": lambda df: df["sla_breached"].astype(bool),
    "Request Intake Validation": lambda df: df["process_stage"].eq("Intake"),
    "Rework Prevention Checklist": lambda df: df["rework_flag"].astype(bool),
    "Auto-Routing by Request Type": lambda df: df["request_type"].isin(_AUTO_ROUTE_TYPES),
}


def candidate_membership(df: pd.DataFrame) -> pd.DataFrame:
    """Boolean matrix: one column per row-level candidate, aligned to ``df.index``.

    Multi-membership is expected; a row may match zero, one, or several candidates.
    """
    return pd.DataFrame(
        {name: rule(df).fillna(False).astype(bool) for name, rule in OPSPILOT_CANDIDATE_RULES.items()},
        index=df.index,
    )


def aggregate_candidate_impact(df: pd.DataFrame, membership: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per-candidate opportunity size. Overlapping (a request can appear under more
    than one candidate); use for ranking/sizing, not for portfolio totals.

    Columns: automation_name, volume, manual_hours, sla_breaches.
    """
    if membership is None:
        membership = candidate_membership(df)
    manual_hours = df["estimated_manual_minutes"] / 60.0
    sla = df["sla_breached"].astype(bool)
    rows = []
    for name in OPSPILOT_CANDIDATE_RULES:
        mask = membership[name]
        rows.append(
            {
                "automation_name": name,
                "volume": int(mask.sum()),
                "manual_hours": float(manual_hours[mask].sum()),
                "sla_breaches": int(sla[mask].sum()),
            }
        )
    return pd.DataFrame(rows)


def primary_candidate(df: pd.DataFrame, membership: pd.DataFrame | None = None) -> pd.Series:
    """Assign each request to exactly one candidate: the qualifying automation with
    the highest save rate. Requests matching no rule become "Unclassified".

    Unique attribution -- safe to sum manual hours across the result.
    """
    if membership is None:
        membership = candidate_membership(df)
    # Evaluate candidates from highest save rate to lowest; first match wins.
    ordered = sorted(
        OPSPILOT_CANDIDATE_RULES,
        key=lambda name: OPSPILOT_SAVE_RATES.get(name, 0.0),
        reverse=True,
    )
    result = pd.Series("Unclassified", index=df.index, dtype=object)
    assigned = pd.Series(False, index=df.index)
    for name in ordered:
        take = membership[name] & ~assigned
        result[take] = name
        assigned |= membership[name]
    return result


def blended_save_rate(df: pd.DataFrame, membership: pd.DataFrame | None = None) -> float:
    """Manual-hours-weighted mean save rate over uniquely-attributed requests.

    This is the single "how much of the manual work is actually removable" figure
    behind the portfolio savings estimate -- derived, not a magic constant.
    """
    if membership is None:
        membership = candidate_membership(df)
    primary = primary_candidate(df, membership)
    manual_hours = df["estimated_manual_minutes"] / 60.0
    classified = primary != "Unclassified"
    total_hours = float(manual_hours[classified].sum())
    if total_hours <= 0:
        return float(sum(OPSPILOT_SAVE_RATES.values()) / len(OPSPILOT_SAVE_RATES))
    weighted = sum(
        float(manual_hours[(primary == name)].sum()) * OPSPILOT_SAVE_RATES.get(name, 0.0)
        for name in OPSPILOT_CANDIDATE_RULES
    )
    return round(weighted / total_hours, 4)
