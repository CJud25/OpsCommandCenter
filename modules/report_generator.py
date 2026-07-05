from __future__ import annotations

import html
import re
from datetime import date

import pandas as pd


# ---------------------------------------------------------------------------
# Small helpers for pulling data-driven values out of the analyzer outputs.
# These keep the report text honest: if a value is missing we degrade to a
# neutral phrase instead of raising or fabricating a number.
# ---------------------------------------------------------------------------
def _first_value(df: pd.DataFrame | None, column: str, default):
    try:
        if df is not None and len(df) > 0 and column in df.columns:
            return df.iloc[0][column]
    except Exception:
        pass
    return default


def _nth_value(df: pd.DataFrame | None, index: int, column: str, default):
    try:
        if df is not None and len(df) > index and column in df.columns:
            return df.iloc[index][column]
    except Exception:
        pass
    return default


def generate_opspilot_report(
    summary: dict,
    bottlenecks: pd.DataFrame,
    automations: pd.DataFrame,
    roi: dict | None = None,
) -> str:
    top_bottlenecks = "\n".join(
        [
            f"- {row.process_stage}: score {row.bottleneck_score:.1f}, {row.delay_contribution * 100:.0f}% of open delay."
            for row in bottlenecks.head(3).itertuples()
        ]
    )
    top_automations = "\n".join(
        [
            f"- {row['Automation Candidate']}: score {row['Automation Score']:.1f}, estimated {row['Estimated Hours Saved']:.1f} hours saved."
            for _, row in automations.head(5).iterrows()
        ]
    )
    roi_text = _opspilot_roi_text(roi) if roi else "ROI can be estimated on the ROI & Business Case page."

    # Data-driven anchors for the adaptive sections.
    top_stage = str(_first_value(bottlenecks, "process_stage", summary.get("top_bottleneck_stage", "the top bottleneck stage")))
    top_delay_pct = float(_first_value(bottlenecks, "delay_contribution", 0.0)) * 100
    top_auto = str(_first_value(automations, "Automation Candidate", summary.get("top_automation_candidate", "the top automation candidate")))
    second_auto = _nth_value(automations, 1, "Automation Candidate", None)
    breach_pct = float(summary.get("sla_breach_rate", 0.0)) * 100

    assumptions = _opspilot_assumptions_block(summary)
    plan_30 = _opspilot_30_day_plan(top_stage, top_auto, top_delay_pct)
    roadmap_90 = _opspilot_90_day_roadmap(top_auto, second_auto)
    risks = _opspilot_risks(top_stage, breach_pct)

    return f"""# OpsPilot Command Center Leadership Brief

Generated: {date.today().isoformat()}

## Executive Summary
Summit Services Group is experiencing delayed internal requests, approval bottlenecks, missing documentation, duplicate work, and limited workload visibility. OpsPilot identified {summary['open_requests']:,} open requests, a {summary['sla_breach_rate'] * 100:.0f}% SLA breach rate, and an estimated ${summary['estimated_monthly_waste']:,.0f} in monthly manual-work waste. The largest measured source of delay is the {top_stage} stage, and the strongest automation opportunity is {top_auto}.

## Current Operational Problem
The current process relies on manual intake review, manual owner follow-up, and inconsistent escalation. Work is aging in bottleneck stages before leaders have a clear view of risk.

## Key Metrics
- Total requests: {summary['total_requests']:,}
- Open requests: {summary['open_requests']:,}
- Average cycle time: {summary['average_cycle_time']:.1f} days
- SLA breach rate: {summary['sla_breach_rate'] * 100:.0f}%
- Oldest open request: {summary['oldest_open_request']} days
- Estimated manual hours: {summary['estimated_manual_hours']:,.1f}
- Potential monthly savings: ${summary['potential_monthly_savings']:,.0f}

## Top Bottlenecks
{top_bottlenecks}

## Top Automation Opportunities
{top_automations}

## Estimated ROI
{roi_text}

### Assumptions
{assumptions}

## Recommended 30-Day MVP Implementation Plan
{plan_30}

## Recommended 90-Day Production Roadmap
{roadmap_90}

## Risks and Controls
{risks}

## Final Recommendation
Build the first MVP around {top_auto} and pair it with SLA escalation reporting focused on the {top_stage} stage. This creates fast, visible value while establishing a scalable operating model for future automation.
"""


def _opspilot_30_day_plan(top_stage: str, top_auto: str, top_delay_pct: float) -> str:
    return "\n".join(
        [
            f"1. Validate the {top_stage} bottleneck with its process owner; it drives about {top_delay_pct:.0f}% of measured open-request delay.",
            f"2. Launch a rule-based automation for {top_auto}, the highest-scoring candidate.",
            f"3. Add SLA aging alerts for the {top_stage} stage and a weekly executive digest.",
            "4. Track time saved, breach reduction, and owner adoption.",
        ]
    )


def _opspilot_90_day_roadmap(top_auto: str, second_auto) -> str:
    expansion = (
        f"4. Expand automation coverage beyond {top_auto} to {second_auto}, approvals, routing, and recurring status summaries."
        if second_auto
        else f"4. Expand automation coverage beyond {top_auto} to approvals, routing, duplicate detection, and recurring status summaries."
    )
    return "\n".join(
        [
            "1. Move from CSV data to a database-backed workflow tracker.",
            "2. Integrate Microsoft 365, service desk, or intake form data.",
            "3. Add role-based access, audit logs, and human approval controls.",
            expansion,
        ]
    )


def _opspilot_risks(top_stage: str, breach_pct: float) -> str:
    return "\n".join(
        [
            f"- The {top_stage} stage carries the highest delay concentration; keep human review for its high-risk approvals and ambiguous duplicates.",
            f"- With a {breach_pct:.0f}% SLA breach rate, prioritize aging alerts so escalation happens before, not after, a breach.",
            "- Maintain audit logs for every automated status change.",
            "- Validate automation rules with process owners before production release.",
        ]
    )


def _opspilot_assumptions_block(summary: dict) -> str:
    return "\n".join(
        [
            "- Staff time is valued at the assumed blended hourly rate (default $45/hour) used by the ROI calculator.",
            "- Savings assume a percent-automated / coverage rate that you set on the ROI & Business Case page; only that share of manual work is removed.",
            "- Time saved per request comes from the estimated manual minutes recorded per request in the dataset.",
            "- Potential monthly savings apply a conservative capture rate to recent manual-work waste rather than assuming full elimination.",
            "- These figures are estimates for demonstration purposes only and should be validated against real operational data before budgeting.",
        ]
    )


def generate_rescueops_report(
    summary: dict,
    medical_priority: pd.DataFrame,
    automations: pd.DataFrame,
    weekly_brief: str,
    roi: dict | None = None,
) -> str:
    top_medical = "\n".join(
        [
            f"- {row.dog_name}: score {row.medical_priority_score:.0f}, funding need ${row.funding_needed:,.0f}, urgency {row.highest_urgency}."
            for row in medical_priority.head(5).itertuples()
        ]
    )
    top_automations = "\n".join(
        [
            f"- {row['Automation Candidate']}: score {row['Automation Score']:.1f}, estimated {row['Estimated Hours Saved']:.1f} hours saved."
            for _, row in automations.head(5).iterrows()
        ]
    )
    roi_text = _rescueops_roi_text(roi) if roi else "Mission impact can be estimated on the ROI & Business Case page."

    # Data-driven anchors for the adaptive sections.
    top_auto = str(_first_value(automations, "Automation Candidate", "Adoption Inquiry Triage"))
    second_auto = _nth_value(automations, 1, "Automation Candidate", None)
    top_dog = str(_first_value(medical_priority, "dog_name", summary.get("highest_priority_dog", "the highest-priority dog")))

    assumptions = _rescueops_assumptions_block(summary)
    plan_30 = _rescueops_30_day_plan(summary, top_auto, top_dog)
    roadmap_90 = _rescueops_90_day_roadmap(top_auto, second_auto)
    risks = _rescueops_risks(top_dog)

    return f"""# RescueOps Leadership Brief

Generated: {date.today().isoformat()}

## Executive Summary
Life's Paw-pose has {summary['dogs_in_care']} dogs in care, {summary['dogs_needing_foster']} dogs needing foster support, {summary['urgent_medical_cases']} urgent medical cases, and {summary['unanswered_messages']} unanswered messages. The highest-scoring medical case is {top_dog}, and the strongest automation opportunity is {top_auto}. RescueOps recommends prioritizing inquiry triage, foster matching, and medical funding visibility.

## Current Operational Problem
The rescue is volunteer-powered and must coordinate dogs, fosters, adoption inquiries, medical expenses, and donor priorities with limited capacity. The operational risk is not only cost. It is delayed response, missed foster fit, and slow movement through the rescue pipeline.

## Key Metrics
- Dogs in care: {summary['dogs_in_care']}
- Dogs needing foster: {summary['dogs_needing_foster']}
- Dogs adoption ready: {summary['dogs_adoption_ready']}
- Urgent medical cases: {summary['urgent_medical_cases']}
- Open adoption inquiries: {summary['open_adoption_inquiries']}
- Unanswered messages: {summary['unanswered_messages']}
- Monthly medical costs: ${summary['monthly_medical_costs']:,.0f}
- Unfunded medical need: ${summary['unfunded_medical_need']:,.0f}
- Volunteer capacity: {summary['volunteer_capacity']}

## Top Medical Priorities
{top_medical}

## Top Automation Opportunities
{top_automations}

## Estimated Mission Impact
{roi_text}

### Assumptions
{assumptions}

## Recommended 30-Day MVP Implementation Plan
{plan_30}

## Recommended 90-Day Production Roadmap
{roadmap_90}

## Risks and Controls
{risks}

## Weekly Founder Brief Snapshot
{weekly_brief}

## Final Recommendation
Start with {top_auto} and the Weekly Founder Brief, and open a funding push for {top_dog}. Together they reduce founder coordination load, protect human review, and create immediate operational clarity.
"""


def _rescueops_30_day_plan(summary: dict, top_auto: str, top_dog: str) -> str:
    return "\n".join(
        [
            f"1. Launch {top_auto} with human-review categories to work down the {summary['unanswered_messages']} unanswered messages.",
            f"2. Build a foster matching queue for the {summary['dogs_needing_foster']} dogs needing foster support.",
            f"3. Open a medical funding push for {top_dog}, the highest-scoring medical case.",
            "4. Publish a weekly founder brief and use safe profile templates for bios and social posts.",
        ]
    )


def _rescueops_90_day_roadmap(top_auto: str, second_auto) -> str:
    expansion = (
        f"4. Schedule weekly briefs and urgent alerts, and extend automation from {top_auto} to {second_auto}."
        if second_auto
        else f"4. Schedule weekly briefs and urgent alerts, and extend automation coverage beyond {top_auto}."
    )
    return "\n".join(
        [
            "1. Connect the shared inbox, adoption form, volunteer tracker, and donation tracker.",
            "2. Add secure volunteer roles and human approval workflow.",
            "3. Create audit logs for recommendations and placement decisions.",
            expansion,
        ]
    )


def _rescueops_risks(top_dog: str) -> str:
    return "\n".join(
        [
            "- This tool does not provide veterinary medical advice.",
            f"- Medical concerns, including the plan for {top_dog}, should be routed to a licensed veterinarian or emergency vet.",
            "- Foster and adoption decisions require human review.",
            "- The app should use secure data handling in any production version.",
        ]
    )


def _rescueops_assumptions_block(summary: dict) -> str:
    return "\n".join(
        [
            "- Volunteer time is valued at the assumed volunteer hourly value used by the mission-impact calculator.",
            "- Savings assume an admin-reduction / coverage rate you set on the ROI & Business Case page; only that share of response time is recovered.",
            "- Time saved per inquiry comes from the assumed minutes per manual response.",
            "- Unfunded medical need counts fully unfunded expenses plus a 0.5 weight on partially funded expenses, so it is a conservative funding gap.",
            "- These figures are estimates for demonstration purposes only and should be validated against real rescue data before donor commitments.",
        ]
    )


# ---------------------------------------------------------------------------
# Markdown rendering. A small, deterministic converter -- no third-party
# dependency. Handles headings (#, ##, ###), bullet lists (-, *), ordered
# lists (1.), inline bold (**...**), and paragraphs.
# ---------------------------------------------------------------------------
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^[-*]\s+(.*)$")
_ORDERED_RE = re.compile(r"^\d+\.\s+(.*)$")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _inline(text: str) -> str:
    escaped = html.escape(text)
    return _BOLD_RE.sub(r"<strong>\1</strong>", escaped)


def _render_markdown_body(markdown_text: str) -> str:
    parts: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(paragraph).strip()
            if text:
                parts.append(f"<p>{_inline(text)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            parts.append(f"</{list_type}>")
            list_type = None

    def open_list(kind: str) -> None:
        nonlocal list_type
        if list_type != kind:
            close_list()
            parts.append(f"<{kind}>")
            list_type = kind

    for raw in markdown_text.split("\n"):
        stripped = raw.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            continue

        heading = _HEADING_RE.match(stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = min(len(heading.group(1)), 6)
            parts.append(f"<h{level}>{_inline(heading.group(2).strip())}</h{level}>")
            continue

        bullet = _BULLET_RE.match(stripped)
        if bullet:
            flush_paragraph()
            open_list("ul")
            parts.append(f"<li>{_inline(bullet.group(1).strip())}</li>")
            continue

        ordered = _ORDERED_RE.match(stripped)
        if ordered:
            flush_paragraph()
            open_list("ol")
            parts.append(f"<li>{_inline(ordered.group(1).strip())}</li>")
            continue

        close_list()
        paragraph.append(stripped)

    flush_paragraph()
    close_list()
    return "\n".join(parts)


def markdown_to_html(markdown_text: str, title: str) -> str:
    body = _render_markdown_body(markdown_text)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #172026;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.55;
    }}
    main {{
      max-width: 960px;
      margin: 40px auto;
      padding: 36px;
      background: #ffffff;
      border: 1px solid #d9dee5;
      border-radius: 8px;
      box-shadow: 0 12px 30px rgba(23, 32, 38, 0.08);
    }}
    h1 {{ font-size: 26px; margin: 0 0 18px; }}
    h2 {{ font-size: 20px; margin: 28px 0 10px; border-bottom: 1px solid #e5e9ee; padding-bottom: 6px; }}
    h3 {{ font-size: 16px; margin: 20px 0 8px; color: #2a3742; }}
    p {{ margin: 10px 0; }}
    ul, ol {{ margin: 10px 0 10px 22px; padding: 0; }}
    li {{ margin: 4px 0; }}
    strong {{ font-weight: 700; }}
  </style>
</head>
<body>
  <main>
{body}
  </main>
</body>
</html>"""


def markdown_to_text(markdown_text: str) -> str:
    """Strip leading heading hashes and bullet markers per line; drop bold markers.

    Unlike a blind replace("#", ""), this only removes the markers at the start
    of a line, so hashes or asterisks that appear inside body text survive.
    """
    lines: list[str] = []
    for raw in markdown_text.split("\n"):
        stripped = raw.lstrip()
        heading = _HEADING_RE.match(stripped)
        bullet = _BULLET_RE.match(stripped)
        if heading:
            line = heading.group(2)
        elif bullet:
            line = bullet.group(1)
        else:
            line = raw
        lines.append(line.replace("**", ""))
    return "\n".join(lines).strip()


def _opspilot_roi_text(roi: dict) -> str:
    payback = roi.get("payback_months")
    if payback is None or payback == float("inf"):
        payback_text = "the build does not pay back within year one at these assumptions"
    elif payback == 0:
        payback_text = "payback is immediate (no build cost assumed)"
    else:
        payback_text = f"payback is about {payback:.1f} months"
    return (
        f"The proposed automation saves an estimated {roi['monthly_hours_saved']:,.1f} hours per month, "
        f"or ${roi['monthly_labor_savings']:,.0f} in monthly labor value and ${roi['annual_labor_savings']:,.0f} annually. "
        f"Net of an assumed build and maintenance cost, first-year net savings are ${roi['annual_net_savings']:,.0f} and "
        f"{payback_text}. {roi['qualitative_business_value']}"
    )


def _rescueops_roi_text(roi: dict) -> str:
    return (
        f"The proposed rescue workflow saves an estimated {roi['volunteer_hours_saved']:,.1f} volunteer hours per month, "
        f"equivalent to ${roi['monthly_volunteer_value']:,.0f} in volunteer time value. It could help about "
        f"{roi['estimated_inquiries_handled_faster']:,.0f} inquiries receive faster handling each month. "
        f"{roi['mission_impact_summary']}"
    )
