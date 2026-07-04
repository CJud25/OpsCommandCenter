from __future__ import annotations

import html
import os
from datetime import date

import pandas as pd


def generate_opspilot_report(
    summary: dict,
    bottlenecks: pd.DataFrame,
    automations: pd.DataFrame,
    roi: dict | None = None,
    recommendation_mode: str = "Rule-Based",
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

    return f"""# OpsPilot Command Center Leadership Brief

Generated: {date.today().isoformat()}
Recommendation mode: {recommendation_mode}

## Executive Summary
Summit Services Group is experiencing delayed internal requests, approval bottlenecks, missing documentation, duplicate work, and limited workload visibility. OpsPilot identified {summary['open_requests']:,} open requests, a {summary['sla_breach_rate'] * 100:.0f}% SLA breach rate, and an estimated ${summary['estimated_monthly_waste']:,.0f} in monthly manual-work waste. The strongest automation opportunity is {summary['top_automation_candidate']}.

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

## Recommended 30-Day MVP Implementation Plan
1. Validate the top three bottleneck findings with operations owners.
2. Launch a rule-based automation for the highest-scoring candidate.
3. Add SLA aging alerts and a weekly executive digest.
4. Track time saved, breach reduction, and owner adoption.

## Recommended 90-Day Production Roadmap
1. Move from CSV data to a database-backed workflow tracker.
2. Integrate Microsoft 365, service desk, or intake form data.
3. Add role-based access, audit logs, and human approval controls.
4. Expand automation coverage to approvals, routing, duplicate detection, and recurring status summaries.

## Risks and Controls
- Keep human review for high-risk approvals and ambiguous duplicates.
- Maintain audit logs for every automated status change.
- Use clear escalation rules by priority and business impact.
- Validate automation rules with process owners before production release.

## Final Recommendation
Build the first MVP around {summary['top_automation_candidate']} and pair it with SLA escalation reporting. This creates fast, visible value while establishing a scalable operating model for future automation.
"""


def generate_rescueops_report(
    summary: dict,
    medical_priority: pd.DataFrame,
    automations: pd.DataFrame,
    weekly_brief: str,
    roi: dict | None = None,
    recommendation_mode: str = "Rule-Based",
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

    return f"""# RescueOps Leadership Brief

Generated: {date.today().isoformat()}
Recommendation mode: {recommendation_mode}

## Executive Summary
Rosalie and Friends has {summary['dogs_in_care']} dogs in care, {summary['dogs_needing_foster']} dogs needing foster support, {summary['urgent_medical_cases']} urgent medical cases, and {summary['unanswered_messages']} unanswered messages. RescueOps recommends prioritizing inquiry triage, foster matching, and medical funding visibility.

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

## Recommended 30-Day MVP Implementation Plan
1. Launch inquiry triage with human-review categories.
2. Build a foster matching queue using structured dog and volunteer data.
3. Publish a weekly founder brief with medical, foster, inquiry, and social priorities.
4. Use safe profile templates for bios and social posts.

## Recommended 90-Day Production Roadmap
1. Connect the shared inbox, adoption form, volunteer tracker, and donation tracker.
2. Add secure volunteer roles and human approval workflow.
3. Create audit logs for recommendations and placement decisions.
4. Schedule weekly briefs and urgent alerts.

## Risks and Controls
- This tool does not provide veterinary medical advice.
- Medical concerns should be routed to a licensed veterinarian or emergency vet.
- Foster and adoption decisions require human review.
- The app should use secure data handling in any production version.

## Weekly Founder Brief Snapshot
{weekly_brief}

## Final Recommendation
Start with Adoption Inquiry Triage and Weekly Founder Brief. Together they reduce founder coordination load, protect human review, and create immediate operational clarity.
"""


def markdown_to_html(markdown_text: str, title: str) -> str:
    escaped = html.escape(markdown_text)
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
    pre {{
      white-space: pre-wrap;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 15px;
    }}
  </style>
</head>
<body>
  <main>
    <pre>{escaped}</pre>
  </main>
</body>
</html>"""


def markdown_to_text(markdown_text: str) -> str:
    return markdown_text.replace("#", "").replace("**", "").strip()


def optional_ai_polish(prompt: str, system_message: str) -> str | None:
    """Use OpenAI only when the user has installed the SDK and provided a key."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception:
        return None


def _opspilot_roi_text(roi: dict) -> str:
    return (
        f"The proposed automation saves an estimated {roi['monthly_hours_saved']:,.1f} hours per month, "
        f"or ${roi['monthly_labor_savings']:,.0f} monthly and ${roi['annual_labor_savings']:,.0f} annually. "
        f"Expected cycle-time improvement is {roi['estimated_cycle_time_improvement']:.1f} days, with an estimated "
        f"{roi['sla_breach_reduction_estimate']:.0f}% reduction in SLA breach risk. {roi['qualitative_business_value']}"
    )


def _rescueops_roi_text(roi: dict) -> str:
    return (
        f"The proposed rescue workflow saves an estimated {roi['volunteer_hours_saved']:,.1f} volunteer hours per month, "
        f"equivalent to ${roi['monthly_volunteer_value']:,.0f} in volunteer time value. It could help "
        f"{roi['estimated_inquiries_handled_faster']:,.0f} inquiries receive faster handling while improving medical funding "
        f"visibility by about {roi['medical_funding_visibility_improvement']:.0f}%. {roi['mission_impact_summary']}"
    )
