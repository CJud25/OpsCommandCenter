from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BOOL_COLUMNS = [
    "required_documents_missing",
    "duplicate_flag",
    "rework_flag",
    "approval_required",
    "sla_breached",
]


def load_opspilot_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["submitted_date"])
    for column in BOOL_COLUMNS:
        if column in df.columns:
            df[column] = df[column].astype(str).str.lower().isin(["true", "1", "yes"])
    return df


def _normalize(series: pd.Series) -> pd.Series:
    series = series.astype(float)
    span = series.max() - series.min()
    if span == 0:
        return pd.Series(np.ones(len(series)) * 50, index=series.index)
    return ((series - series.min()) / span) * 100


def summarize_opspilot(df: pd.DataFrame, assumed_hourly_rate: float = 45.0) -> dict:
    open_df = df[df["current_status"] != "Closed"]
    recent_cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=30)
    recent_df = df[df["submitted_date"] >= recent_cutoff]
    bottlenecks = detect_bottlenecks(df)

    manual_hours = df["estimated_manual_minutes"].sum() / 60
    recent_manual_hours = recent_df["estimated_manual_minutes"].sum() / 60
    monthly_waste = recent_manual_hours * assumed_hourly_rate
    top_automation = (
        df.groupby("automation_candidate_type")["estimated_manual_minutes"].sum().sort_values(ascending=False).index[0]
    )

    return {
        "total_requests": int(len(df)),
        "open_requests": int(len(open_df)),
        "average_cycle_time": float(df["cycle_time_days"].mean()),
        "sla_breach_rate": float(df["sla_breached"].mean()),
        "oldest_open_request": int(open_df["days_open"].max() if len(open_df) else 0),
        "estimated_manual_hours": float(manual_hours),
        "estimated_monthly_waste": float(monthly_waste),
        "top_bottleneck_stage": str(bottlenecks.iloc[0]["process_stage"]),
        "top_automation_candidate": str(top_automation),
        "potential_monthly_savings": float(monthly_waste * 0.42),
    }


def detect_bottlenecks(df: pd.DataFrame) -> pd.DataFrame:
    open_mask = df["current_status"] != "Closed"
    total_delay = max(df.loc[open_mask, "days_open"].sum(), 1)
    total_volume = max(len(df), 1)

    grouped = (
        df.groupby("process_stage")
        .agg(
            volume=("request_id", "count"),
            open_count=("current_status", lambda values: int((values != "Closed").sum())),
            avg_days_open=("days_open", "mean"),
            breach_rate=("sla_breached", "mean"),
            rework_rate=("rework_flag", "mean"),
            missing_doc_rate=("required_documents_missing", "mean"),
            manual_minutes=("estimated_manual_minutes", "sum"),
        )
        .reset_index()
    )

    delay_by_stage = df.loc[open_mask].groupby("process_stage")["days_open"].sum()
    grouped["delay_days"] = grouped["process_stage"].map(delay_by_stage).fillna(0)
    grouped["volume_pct"] = grouped["volume"] / total_volume
    grouped["open_pct"] = grouped["open_count"] / grouped["volume"].replace(0, np.nan)
    grouped["delay_contribution"] = grouped["delay_days"] / total_delay
    grouped["manual_hours"] = grouped["manual_minutes"] / 60

    grouped["bottleneck_score"] = (
        _normalize(grouped["avg_days_open"]) * 0.3
        + grouped["open_pct"].fillna(0) * 100 * 0.22
        + grouped["breach_rate"].fillna(0) * 100 * 0.22
        + grouped["delay_contribution"].fillna(0) * 100 * 0.16
        + (grouped["rework_rate"].fillna(0) + grouped["missing_doc_rate"].fillna(0)) * 50 * 0.1
    )
    grouped["bottleneck_score"] = grouped["bottleneck_score"].round(1)
    return grouped.sort_values("bottleneck_score", ascending=False).reset_index(drop=True)


def bottleneck_insight(bottlenecks: pd.DataFrame) -> str:
    if bottlenecks.empty:
        return "No bottleneck pattern is available yet."

    top = bottlenecks.iloc[0]
    stage = top["process_stage"]
    volume_pct = top["volume_pct"] * 100
    delay_pct = top["delay_contribution"] * 100
    breach_rate = top["breach_rate"] * 100
    missing_rate = top["missing_doc_rate"] * 100
    return (
        f"{stage} is the primary bottleneck. It represents {volume_pct:.0f}% of request volume "
        f"but accounts for {delay_pct:.0f}% of total open-request delay, with a {breach_rate:.0f}% SLA breach rate "
        f"and {missing_rate:.0f}% missing-document rate."
    )


def get_opspilot_chart_data(df: pd.DataFrame, bottlenecks: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "requests_by_department": (
            df.groupby("department").size().reset_index(name="requests").sort_values("requests", ascending=False)
        ),
        "requests_by_stage": (
            df.groupby("process_stage").size().reset_index(name="requests").sort_values("requests", ascending=False)
        ),
        "avg_cycle_by_type": (
            df.groupby("request_type")["cycle_time_days"].mean().reset_index(name="avg_cycle_time").sort_values(
                "avg_cycle_time", ascending=False
            )
        ),
        "breaches_by_department": (
            df.groupby("department")["sla_breached"].sum().reset_index(name="sla_breaches").sort_values(
                "sla_breaches", ascending=False
            )
        ),
        "manual_hours_by_type": (
            df.assign(manual_hours=df["estimated_manual_minutes"] / 60)
            .groupby("request_type")["manual_hours"]
            .sum()
            .reset_index()
            .sort_values("manual_hours", ascending=False)
        ),
        "bottleneck_breakdown": bottlenecks[
            ["process_stage", "volume", "open_count", "breach_rate", "delay_contribution", "bottleneck_score"]
        ],
        "automation_impact": (
            df.assign(manual_hours=df["estimated_manual_minutes"] / 60)
            .groupby("automation_candidate_type")
            .agg(volume=("request_id", "count"), manual_hours=("manual_hours", "sum"), sla_breaches=("sla_breached", "sum"))
            .reset_index()
            .sort_values(["manual_hours", "sla_breaches"], ascending=False)
        ),
    }


def get_operational_problem_statement(summary: dict, bottleneck_text: str) -> str:
    return (
        "Summit Services Group has high-volume operational work moving through manual intake, review, approval, "
        "and fulfillment queues. "
        f"{bottleneck_text} The current dataset shows {summary['open_requests']:,} open requests, "
        f"an average cycle time of {summary['average_cycle_time']:.1f} days, and an estimated "
        f"${summary['estimated_monthly_waste']:,.0f} in monthly manual-work waste."
    )
