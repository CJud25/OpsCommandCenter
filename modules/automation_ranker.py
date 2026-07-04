from __future__ import annotations

import pandas as pd

from modules import classification, scoring


OPSPILOT_AUTOMATION_SPECS = {
    "Missing Document Follow-Up": {
        "problem": "Requests stall because required documentation is missing during intake.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Reduces waiting time, rework, and requester follow-up burden.",
        "tool": "Power Automate, SharePoint Lists, Teams, email automation",
        "first_step": "Define required fields by request type and create a follow-up template.",
        "repeatability": 92,
        "rule_clarity": 90,
        "save_rate": 0.62,
    },
    "Approval Reminder Automation": {
        "problem": "Approvals sit in queues without timely nudges or escalation.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Improves cycle time and SLA performance for approval-heavy work.",
        "tool": "Power Automate, Teams approvals, scheduled Python job",
        "first_step": "Map approval owners, escalation windows, and exception paths.",
        "repeatability": 86,
        "rule_clarity": 82,
        "save_rate": 0.48,
    },
    "Duplicate Request Detection": {
        "problem": "Teams spend time reviewing duplicate or near-duplicate requests.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Reduces duplicate work and improves intake quality.",
        "tool": "Python matching rules, database constraints, form validation",
        "first_step": "Create duplicate checks using requester, request type, and recent submission window.",
        "repeatability": 78,
        "rule_clarity": 74,
        "save_rate": 0.52,
    },
    "Auto-Routing by Request Type": {
        "problem": "Requests are manually routed even when assignment rules are stable.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Shortens intake time and improves queue visibility.",
        "tool": "Streamlit admin rules, Power Automate, service desk routing rules",
        "first_step": "Build a request-type-to-owner routing matrix.",
        "repeatability": 94,
        "rule_clarity": 88,
        "save_rate": 0.55,
    },
    "SLA Escalation Alerts": {
        "problem": "Aging work is not escalated until it is already late.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves responsiveness and reduces surprise escalations.",
        "tool": "Scheduled Python job, Teams alerts, email digest",
        "first_step": "Define alert thresholds by priority and process stage.",
        "repeatability": 88,
        "rule_clarity": 86,
        "save_rate": 0.44,
    },
    "Request Intake Validation": {
        "problem": "Incomplete requests enter the workflow and create downstream rework.",
        "complexity": "Medium",
        "risk": "Low",
        "impact": "Improves quality at the source and reduces back-and-forth.",
        "tool": "Microsoft Forms, form validation, SharePoint Lists",
        "first_step": "Identify required fields and validation rules for the top request types.",
        "repeatability": 90,
        "rule_clarity": 84,
        "save_rate": 0.58,
    },
    "Recurring Status Summary": {
        "problem": "Leaders lack predictable visibility into work volume and aging.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves management visibility without manual status gathering.",
        "tool": "Scheduled email, Streamlit export, Teams digest",
        "first_step": "Create weekly summary fields and audience list.",
        "repeatability": 84,
        "rule_clarity": 80,
        "save_rate": 0.36,
    },
    "Rework Prevention Checklist": {
        "problem": "Common quality misses cause requests to bounce between teams.",
        "complexity": "Medium",
        "risk": "Low",
        "impact": "Reduces rework, touches, and owner frustration.",
        "tool": "Checklist workflow, form validation, Teams reminder",
        "first_step": "Identify the top five rework causes and convert them into validation checks.",
        "repeatability": 82,
        "rule_clarity": 78,
        "save_rate": 0.5,
    },
}


RESCUEOPS_AUTOMATION_SPECS = {
    "Adoption Inquiry Triage": {
        "problem": "Adoption inquiries wait too long and require manual prioritization.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Improves response time while routing sensitive decisions to humans.",
        "tool": "Streamlit rules engine, Airtable/Sheets, email templates",
        "first_step": "Define triage categories and human-review rules.",
        "repeatability": 88,
        "rule_clarity": 82,
    },
    "Foster Match Recommendation": {
        "problem": "Foster placement depends on manual memory of capacity and capabilities.",
        "complexity": "Medium",
        "risk": "Medium",
        "impact": "Improves foster fit and reduces emergency placement scrambling.",
        "tool": "Rules engine, volunteer database, scheduled digest",
        "first_step": "Capture foster capacity, constraints, and dog needs in one table.",
        "repeatability": 80,
        "rule_clarity": 74,
    },
    "Medical Funding Priority Alert": {
        "problem": "Medical needs compete for attention without a consistent priority view.",
        "complexity": "Low",
        "risk": "Medium",
        "impact": "Improves donor focus and leadership visibility into urgent needs.",
        "tool": "Scheduled report, donation tracker, Streamlit dashboard",
        "first_step": "Map urgency, funding gap, and adoption-readiness impact into a priority score.",
        "repeatability": 84,
        "rule_clarity": 80,
    },
    "Dog Bio/Social Post Generator": {
        "problem": "Adoption-ready dogs wait for bios and social posts.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Increases visibility for adoption-ready dogs and foster needs.",
        "tool": "Template generator, optional AI copy assistant, social queue",
        "first_step": "Create safe copy templates using only approved dog profile fields.",
        "repeatability": 90,
        "rule_clarity": 86,
    },
    "Volunteer Task Reminder": {
        "problem": "Volunteer tasks can fall through when capacity is limited.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves follow-through and reduces founder coordination load.",
        "tool": "Email digest, Teams/Slack reminders, Google Sheets",
        "first_step": "Define task owners, due dates, and escalation reminders.",
        "repeatability": 86,
        "rule_clarity": 82,
    },
    "Weekly Founder Brief": {
        "problem": "Founders need a concise view of dogs, gaps, inquiries, and funding.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Creates leadership visibility without manual spreadsheet review.",
        "tool": "Streamlit report export, scheduled email, Google Docs",
        "first_step": "Standardize the weekly brief sections and source metrics.",
        "repeatability": 92,
        "rule_clarity": 88,
    },
    "Unanswered Message Escalation": {
        "problem": "Messages age past acceptable response windows.",
        "complexity": "Low",
        "risk": "Low",
        "impact": "Improves applicant experience and reduces missed opportunities.",
        "tool": "Email alerts, shared inbox labels, scheduled digest",
        "first_step": "Set response thresholds and escalation owners by inquiry type.",
        "repeatability": 90,
        "rule_clarity": 90,
    },
}


# Org-level assumption for "Recurring Status Summary". Unlike the seven row-level
# candidates it has no per-request trigger, so classification carries no volume for
# it. We model a modest weekly reporting cadence: one summary per week (~4/month)
# and ~2 hours of manual status-gathering per summary (~8 hours/month), with no SLA
# breaches (it is a reporting job, not SLA-bearing work). Kept deliberately
# conservative so this synthetic row never dominates the ranking.
_RECURRING_SUMMARY_ASSUMED_VOLUME = 4
_RECURRING_SUMMARY_ASSUMED_MANUAL_HOURS = 8.0
_RECURRING_SUMMARY_ASSUMED_SLA_BREACHES = 0


def build_opspilot_automation_ranker(df: pd.DataFrame) -> pd.DataFrame:
    # Fix #9: absolute, cross-domain-comparable scoring. Candidacy comes from the
    # classification layer (derived from raw request fields) -- we never read the
    # generator's ``automation_candidate_type`` column, which Workstream A removes.
    impact = classification.aggregate_candidate_impact(df)

    sized: list[dict] = [
        {
            "automation_name": row["automation_name"],
            "volume": int(row["volume"]),
            "manual_hours": float(row["manual_hours"]),
            "sla_breaches": int(row["sla_breaches"]),
        }
        for _, row in impact.iterrows()
    ]

    # The org-level 8th candidate is not in classification membership; add it as a
    # synthetic row with documented modest assumptions (see constants above).
    sized.append(
        {
            "automation_name": "Recurring Status Summary",
            "volume": _RECURRING_SUMMARY_ASSUMED_VOLUME,
            "manual_hours": _RECURRING_SUMMARY_ASSUMED_MANUAL_HOURS,
            "sla_breaches": _RECURRING_SUMMARY_ASSUMED_SLA_BREACHES,
        }
    )

    rows: list[dict] = []
    for item in sized:
        spec = OPSPILOT_AUTOMATION_SPECS[item["automation_name"]]
        impact_score = scoring.sla_impact_score(item["sla_breaches"])
        score = scoring.absolute_automation_score(
            manual_hours=item["manual_hours"],
            impact_0_100=impact_score,
            repeatability=spec["repeatability"],
            rule_clarity=spec["rule_clarity"],
            complexity=spec["complexity"],
        )
        rows.append(
            {
                "Domain": "OpsPilot",
                "Automation Candidate": item["automation_name"],
                "Problem Solved": spec["problem"],
                "Volume": int(item["volume"]),
                "Estimated Hours Saved": round(item["manual_hours"] * spec["save_rate"], 1),
                "Complexity": spec["complexity"],
                "Risk": spec["risk"],
                "Business/Mission Impact": spec["impact"],
                "Automation Score": score,
                "Recommended First Step": spec["first_step"],
                "Recommended Implementation Tool": spec["tool"],
            }
        )

    return _rank(pd.DataFrame(rows))


def build_rescueops_automation_ranker(
    dogs: pd.DataFrame, inquiries: pd.DataFrame, volunteers: pd.DataFrame, medical: pd.DataFrame
) -> pd.DataFrame:
    foster_need = len(
        dogs[
            (dogs["current_status"].isin(["Foster Needed", "Intake", "Medical Hold"]))
            | (dogs["foster_status"].isin(["Needs Foster", "Needs Backup", "Boarding"]))
        ]
    )
    medical_priority_cases = len(
        medical[(medical["urgency"].isin(["High", "Critical"])) | (medical["funded_status"] != "Funded")]
    )
    bio_social_need = int((dogs["bio_needed"] | dogs["social_post_needed"]).sum())
    overdue_messages = len(inquiries[inquiries["days_waiting"] > 3])
    open_adoption_inquiries = len(
        inquiries[
            (inquiries["inquiry_type"] == "Adoption Inquiry")
            & (inquiries["response_status"].isin(["New", "In Review", "Overdue", "Escalated"]))
        ]
    )
    active_volunteer_tasks = int(volunteers["current_assignments"].sum())

    base = pd.DataFrame(
        [
            ("Adoption Inquiry Triage", max(open_adoption_inquiries, 1), open_adoption_inquiries * 0.18 + 8, 88),
            ("Foster Match Recommendation", max(foster_need, 1), foster_need * 0.45 + 6, 86),
            ("Medical Funding Priority Alert", max(medical_priority_cases, 1), medical_priority_cases * 0.14 + 5, 92),
            ("Dog Bio/Social Post Generator", max(bio_social_need, 1), bio_social_need * 0.42 + 4, 82),
            ("Volunteer Task Reminder", max(active_volunteer_tasks, 1), active_volunteer_tasks * 0.18 + 5, 74),
            ("Weekly Founder Brief", 4, 7.0, 90),
            ("Unanswered Message Escalation", max(overdue_messages, 1), overdue_messages * 0.15 + 4, 84),
        ],
        columns=["automation_name", "volume", "estimated_hours_saved", "mission_impact_score"],
    )
    rows: list[dict] = []
    for _, row in base.iterrows():
        spec = RESCUEOPS_AUTOMATION_SPECS[row["automation_name"]]
        # Fix #9: same absolute scorer as OpsPilot so the two domains are directly
        # comparable. RescueOps effort is already expressed as monthly hours saved,
        # and mission_impact_score is already on a 0-100-ish scale, so both feed the
        # scorer without per-domain min-max normalization.
        score = scoring.absolute_automation_score(
            manual_hours=float(row["estimated_hours_saved"]),
            impact_0_100=float(row["mission_impact_score"]),
            repeatability=spec["repeatability"],
            rule_clarity=spec["rule_clarity"],
            complexity=spec["complexity"],
        )
        rows.append(
            {
                "Domain": "RescueOps",
                "Automation Candidate": row["automation_name"],
                "Problem Solved": spec["problem"],
                "Volume": int(row["volume"]),
                "Estimated Hours Saved": round(float(row["estimated_hours_saved"]), 1),
                "Complexity": spec["complexity"],
                "Risk": spec["risk"],
                "Business/Mission Impact": spec["impact"],
                "Automation Score": score,
                "Recommended First Step": spec["first_step"],
                "Recommended Implementation Tool": spec["tool"],
            }
        )

    return _rank(pd.DataFrame(rows))


def build_combined_automation_ranker(
    opspilot_df: pd.DataFrame,
    dogs: pd.DataFrame,
    inquiries: pd.DataFrame,
    volunteers: pd.DataFrame,
    medical: pd.DataFrame,
) -> pd.DataFrame:
    return _rank(
        pd.concat(
            [
                build_opspilot_automation_ranker(opspilot_df),
                build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical),
            ],
            ignore_index=True,
        ).drop(columns=["Rank"], errors="ignore")
    )


def _rank(df: pd.DataFrame) -> pd.DataFrame:
    ranked = df.sort_values("Automation Score", ascending=False).reset_index(drop=True)
    ranked.insert(0, "Rank", ranked.index + 1)
    return ranked


def get_automation_blueprint(automation_name: str, domain: str, estimated_hours_saved: float | None = None) -> dict:
    spec = (
        OPSPILOT_AUTOMATION_SPECS.get(automation_name)
        if domain == "OpsPilot"
        else RESCUEOPS_AUTOMATION_SPECS.get(automation_name)
    )
    if spec is None:
        spec = {
            "problem": "A repeatable workflow is consuming manual coordination time.",
            "complexity": "Medium",
            "risk": "Medium",
            "impact": "Improves speed, quality, and management visibility.",
            "tool": "Python, Streamlit, workflow automation, and a lightweight database",
            "first_step": "Define the process trigger, owner, rules, and exception path.",
        }

    if domain == "OpsPilot":
        trigger = _opspilot_trigger(automation_name)
        inputs = [
            "request_id",
            "request_type",
            "process_stage",
            "priority",
            "owner",
            "submitted_date",
            "sla_days",
            "required_documents_missing",
            "approval_status",
        ]
        audit = "Log request id, rule triggered, prior status, new status, notification recipient, timestamp, and escalation outcome."
        production = "Connect to Microsoft Graph, SharePoint or service desk data, Teams notifications, role-based access, and durable audit tables."
    else:
        trigger = _rescueops_trigger(automation_name)
        inputs = [
            "dog profile",
            "inquiry details",
            "volunteer capacity",
            "medical status",
            "funding status",
            "human-review flags",
        ]
        audit = "Log case id, recommendation, source fields used, volunteer or founder owner, timestamp, and human decision."
        production = "Connect to the rescue CRM, shared inbox, donation platform, volunteer database, and secure file storage with human approval workflows."

    return {
        "Automation Name": automation_name,
        "Business Problem": spec["problem"],
        "Trigger": trigger,
        "Required Inputs": inputs,
        "Decision Rules": _decision_rules(automation_name, domain),
        "Workflow Steps": _workflow_steps(automation_name, domain),
        "Exception Handling": _exception_handling(automation_name, domain),
        "Notification Logic": _notification_logic(automation_name, domain),
        "Audit Log Requirements": audit,
        "Estimated Hours Saved": f"{estimated_hours_saved:.1f} hours/month" if estimated_hours_saved is not None else "Estimate from current volume and manual effort.",
        "Recommended Tooling": spec["tool"],
        "Implementation Difficulty": spec["complexity"],
        "MVP Build Version": _mvp_version(automation_name, domain),
        "Production Version": production,
    }


def blueprint_to_markdown(blueprint: dict) -> str:
    lines = [f"## {blueprint['Automation Name']}"]
    for key, value in blueprint.items():
        if key == "Automation Name":
            continue
        lines.append(f"\n### {key}")
        if isinstance(value, list):
            lines.extend([f"{idx}. {item}" for idx, item in enumerate(value, start=1)])
        else:
            lines.append(str(value))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fix #8: per-candidate blueprint content.
#
# Previously the blueprint helpers branched only on ``domain`` and returned the
# same generic paragraph for every candidate. The tables below carry concrete,
# field-level content for all 15 candidates (8 OpsPilot + 7 RescueOps): decision
# rules in "if field = value -> action" form, real per-candidate workflow steps,
# targeted exception handling, and notification logic. Idempotency and
# flow-failure language is included where it matters (reminders suppressed once
# satisfied; notifications keyed on a stable id so re-runs never double-send;
# flow failures alert the automation owner via run-history monitoring).
# ---------------------------------------------------------------------------

_TRIGGERS: dict[str, str] = {
    # OpsPilot
    "Missing Document Follow-Up": "New or updated request where required_documents_missing = true and current_status is not Closed.",
    "Approval Reminder Automation": "Approval-required request stays approval_status = Pending beyond its reminder window.",
    "Duplicate Request Detection": "New request whose requester + request_type match a recent request inside the dedup window, or duplicate_flag = true.",
    "Auto-Routing by Request Type": "Request enters process_stage = Intake with a request_type that has a routing rule.",
    "SLA Escalation Alerts": "Scheduled scan finds an open request crossing 75%, 100%, or 125% of its sla_days target.",
    "Request Intake Validation": "Request is submitted or resubmitted at process_stage = Intake.",
    "Recurring Status Summary": "Scheduled weekly run (org-level reporting job); no per-request trigger.",
    "Rework Prevention Checklist": "Request reaches a stage gate for a request_type with known rework causes, or rework_flag = true on a related request.",
    # RescueOps
    "Adoption Inquiry Triage": "New adoption inquiry received, or an unanswered inquiry exceeds its response threshold.",
    "Foster Match Recommendation": "Dog is marked current_status in {Foster Needed, Intake, Medical Hold} or foster_status needs foster/backup/boarding.",
    "Medical Funding Priority Alert": "Medical expense is added, funded_status/urgency changes, or the scheduled priority run fires.",
    "Dog Bio/Social Post Generator": "Dog is marked bio_needed = true or social_post_needed = true.",
    "Volunteer Task Reminder": "Volunteer task nears or passes its due date.",
    "Weekly Founder Brief": "Scheduled weekly run compiling rescue operations data.",
    "Unanswered Message Escalation": "Scheduled scan finds an inquiry aging past its response threshold for its type.",
}


_DECISION_RULES: dict[str, list[str]] = {
    # ---- OpsPilot ----
    "Missing Document Follow-Up": [
        "If required_documents_missing = true and current_status != Closed -> set status to Waiting on Requester and open a follow-up.",
        "If request_type has a defined checklist -> attach the request-type-specific list of missing items to the message.",
        "If priority in {High, Critical} -> shorten the reminder window from 48h to 24h.",
        "If required_documents_missing flips to false (documents received) -> suppress pending reminders and return the request to its prior stage.",
        "If no documents arrive after 5 business days -> escalate to the assigned owner.",
    ],
    "Approval Reminder Automation": [
        "If approval_required = true and approval_status = Pending and days_open > reminder_window -> nudge the current approver.",
        "If approval_status = Pending and days_open > escalation_window -> escalate to the approver's manager.",
        "If business_impact in {High, Critical} -> use the expedited reminder and escalation windows.",
        "If approval_status changes to Approved or Rejected -> cancel outstanding reminders.",
    ],
    "Duplicate Request Detection": [
        "If duplicate_flag = true, or a new request matches an open request on requester + request_type within a 14-day window -> mark suspected duplicate and hold.",
        "If a suspected duplicate matches an already-Closed request -> link to the prior resolution and notify the requester.",
        "If the match is a partial-key (ambiguous) match -> route to the owner for confirmation instead of auto-closing.",
    ],
    "Auto-Routing by Request Type": [
        "If request_type in {Access Request, Training Assignment, Equipment Request} and process_stage = Intake -> assign owner/team from the routing matrix.",
        "If request_type has no routing rule -> leave the request in the manual triage queue.",
        "If priority = Critical -> assign to the on-call owner regardless of the standard rotation.",
        "If the mapped team is at capacity -> fall back to the secondary owner defined in the matrix.",
    ],
    "SLA Escalation Alerts": [
        "If days_open >= 0.75 * sla_days and current_status != Closed -> send an at-risk warning to the owner.",
        "If days_open >= sla_days (sla_breached = true) -> escalate to the owner's manager.",
        "If days_open >= 1.25 * sla_days -> escalate to the department lead.",
        "If priority in {High, Critical} -> raise each threshold's response one urgency level.",
    ],
    "Request Intake Validation": [
        "If process_stage = Intake and any required field for the request_type is blank -> reject the submission and list the specific missing fields.",
        "If required_documents_missing = true at intake -> block advancement to review.",
        "If request_type is unrecognized -> route to triage for classification rather than hard-failing.",
        "If all required fields and attachments pass -> advance the request to the first review stage.",
    ],
    "Recurring Status Summary": [
        "If the scheduled run time is reached -> compile the summary for the reporting period.",
        "If open volume, aging, or SLA breach rate exceeds its threshold -> flag that section as needs-attention.",
        "If the distribution audience is empty -> hold the send and alert the report owner instead of sending an empty brief.",
    ],
    "Rework Prevention Checklist": [
        "If a request_type has known rework causes (or rework_flag = true on a related request) -> attach the matching pre-submission checklist.",
        "If a checklist item is unmet at a stage gate -> block advancement until it is resolved.",
        "If touches_count exceeds the request_type's expected threshold -> flag the request for quality review.",
        "If every checklist item passes -> allow the request to proceed.",
    ],
    # ---- RescueOps ----
    "Adoption Inquiry Triage": [
        "If inquiry_type = Adoption Inquiry and required applicant fields are complete -> classify the triage category and queue by priority_score then days_waiting.",
        "If has_children = true and the dog's good_with_children in {No, Unknown} -> flag for human review; do not auto-advance.",
        "If has_other_pets = true and good_with_dogs/good_with_cats in {No, Unknown} -> flag for human review.",
        "If the message indicates a medical or safety concern -> escalate to rescue leadership.",
        "If days_waiting > 3 -> mark the inquiry overdue and prepend an apology to the drafted response.",
    ],
    "Foster Match Recommendation": [
        "If current_status in {Foster Needed, Intake, Medical Hold} or foster_status in {Needs Foster, Needs Backup, Boarding} -> add the dog to the foster-need list.",
        "If volunteer can_foster = true and (foster_capacity - current_assignments) > 0 -> include the volunteer as a candidate.",
        "If medical_status in {Emergency, Surgery Needed} and volunteer can_handle_medical = false -> exclude that match.",
        "If age_group = Senior -> prefer volunteers with can_handle_seniors = true.",
        "Rank candidates by available capacity, reliability_score, and capability fit.",
    ],
    "Medical Funding Priority Alert": [
        "If urgency in {High, Critical} or funded_status != Funded -> include the case in the priority view.",
        "If funded_status = Unfunded -> count the full amount as the funding gap; if Partially Funded -> count 50%.",
        "If medical_status in {Emergency, Surgery Needed} and adoption_ready = false -> raise the priority weight (care is blocking adoption).",
        "Rank cases by urgency, funding gap, and adoption-readiness impact.",
    ],
    "Dog Bio/Social Post Generator": [
        "If bio_needed = true or social_post_needed = true -> queue the dog for content generation.",
        "Use only approved profile fields (age_group, breed_mix, energy_level, structured compatibility); never assert unverified medical or behavioral claims.",
        "If medical_status != Clear -> use the safe, non-diagnostic medical phrasing.",
        "If adoption_ready = false -> generate a foster/support post rather than an adoption-ready post.",
    ],
    "Volunteer Task Reminder": [
        "If a volunteer task is open and its due_date is within the reminder window -> remind the assigned volunteer.",
        "If a task is past due -> escalate to the volunteer coordinator.",
        "If a volunteer's current_assignments >= foster_capacity -> avoid new assignments and flag for load balancing.",
        "If a task is marked complete -> cancel outstanding reminders.",
    ],
    "Weekly Founder Brief": [
        "If the scheduled brief day is reached -> compile dogs in care, foster gaps, urgent medical, inquiries, and funding needs for the week.",
        "If a section's metric exceeds its threshold (unanswered messages, foster gaps, urgent medical) -> flag it as needs-attention.",
        "If a data source is missing -> include a clearly-labeled gap note rather than silently omitting the section.",
    ],
    "Unanswered Message Escalation": [
        "If response_status in {New, In Review} and days_waiting > threshold -> mark the inquiry Overdue and notify the owner.",
        "If days_waiting exceeds the escalation threshold -> set Escalated and notify leadership.",
        "If inquiry_type in {Surrender, Medical/Safety} -> apply a shorter response threshold.",
        "If a response is recorded (response_status -> Responded) -> clear the escalation state.",
    ],
}


_WORKFLOW_STEPS: dict[str, list[str]] = {
    # ---- OpsPilot ----
    "Missing Document Follow-Up": [
        "Detect the missing required document(s) for the request_type.",
        "Move the request to Waiting on Requester.",
        "Generate a follow-up message listing the specific missing items.",
        "Notify the requester and copy the assigned owner.",
        "Wait the reminder window (48h standard, 24h for High/Critical).",
        "Send one reminder if documents are still missing.",
        "Escalate to the owner after 5 business days.",
        "Suppress reminders and log all actions once documents arrive.",
    ],
    "Approval Reminder Automation": [
        "Detect a pending approval past its reminder window.",
        "Identify the current approver and the escalation manager.",
        "Send a reminder with the request summary and an approve/reject link.",
        "Wait the escalation window.",
        "Escalate to the manager if the approval is still pending.",
        "Record the approval outcome and cancel any pending reminders.",
    ],
    "Duplicate Request Detection": [
        "Compute a match key from requester, request_type, and submission window.",
        "Compare the new request against recent open and closed requests.",
        "Flag suspected duplicates and place them on hold.",
        "Present the candidate match to the owner for confirmation.",
        "Merge or close confirmed duplicates and link the records.",
        "Log the decision and notify the requester on a confirmed merge.",
    ],
    "Auto-Routing by Request Type": [
        "Read request_type and process_stage on intake.",
        "Look up the owner/team in the routing matrix.",
        "Assign the request and set process_stage to the first working stage.",
        "Apply the capacity fallback if the primary owner is unavailable.",
        "Notify the assigned owner.",
        "Log the routing decision and the matrix version used.",
    ],
    "SLA Escalation Alerts": [
        "Scan open requests on the schedule.",
        "Compute SLA consumption from days_open and sla_days.",
        "Emit at-risk, breach, and severe-breach alerts at the thresholds.",
        "Escalate to the appropriate management tier.",
        "Suppress further alerts once the request closes.",
        "Log each threshold crossing.",
    ],
    "Request Intake Validation": [
        "Load the required-field schema for the request_type.",
        "Validate submitted fields and attachments.",
        "Return actionable errors for each failed validation.",
        "Block advancement until validation passes.",
        "Advance clean requests to the first review stage.",
        "Log validation outcomes and the fields that failed.",
    ],
    "Recurring Status Summary": [
        "Trigger on the weekly schedule.",
        "Aggregate volume, aging, SLA breaches, and the top bottleneck stage for the period.",
        "Compare each metric against its threshold and annotate exceptions.",
        "Render the summary from the report template.",
        "Distribute it to the leadership audience.",
        "Archive the summary and log the run.",
    ],
    "Rework Prevention Checklist": [
        "Identify the top rework causes for the request_type.",
        "Present the checklist at the relevant stage gate.",
        "Verify each item before allowing advancement.",
        "Block and annotate any unmet items.",
        "Advance requests that clear the checklist.",
        "Log checklist results and recurring failure patterns.",
    ],
    # ---- RescueOps ----
    "Adoption Inquiry Triage": [
        "Receive the inquiry.",
        "Match the inquiry to a dog profile when available.",
        "Classify the triage category from the applicant and dog fields.",
        "Generate follow-up questions for gaps or compatibility flags.",
        "Flag human-review cases (children/pets/medical/safety).",
        "Create a response queue ordered by priority_score and days_waiting.",
        "Log the drafted recommendation and the reviewer's decision.",
    ],
    "Foster Match Recommendation": [
        "Build the foster-need list from dog status fields.",
        "Filter volunteers with open, willing foster capacity.",
        "Score each dog-volunteer pair on capability fit.",
        "Recommend the top match with reasons and cautions.",
        "Route the recommendation to a human for confirmation.",
        "Log the recommendation and the coordinator's decision.",
    ],
    "Medical Funding Priority Alert": [
        "Aggregate medical expenses and funding gaps per dog.",
        "Score each case by urgency, funding gap, and adoption impact.",
        "Rank cases into a donor-focus priority list.",
        "Recommend a campaign focus for each top case.",
        "Route the list to the founder for donor outreach.",
        "Log the priority list and outreach decisions.",
    ],
    "Dog Bio/Social Post Generator": [
        "Detect dogs flagged bio_needed or social_post_needed.",
        "Pull only the approved profile fields.",
        "Generate bio and social copy from safe templates.",
        "Route drafts to a human for review and approval.",
        "Publish approved content and clear the flag.",
        "Log the generated content and the approver.",
    ],
    "Volunteer Task Reminder": [
        "Read open volunteer tasks and their due dates.",
        "Send reminders inside the reminder window.",
        "Escalate overdue tasks to the coordinator.",
        "Suppress reminders for completed tasks.",
        "Balance load away from over-committed volunteers.",
        "Log reminders, completions, and escalations.",
    ],
    "Weekly Founder Brief": [
        "Trigger on the weekly schedule.",
        "Aggregate dogs, foster gaps, medical priorities, inquiries, and funding.",
        "Annotate the sections that breach their thresholds.",
        "Render the brief from the standard template.",
        "Distribute it to the founder/leadership.",
        "Archive the brief and log the run.",
    ],
    "Unanswered Message Escalation": [
        "Scan inquiries for aging past their response thresholds.",
        "Mark overdue and escalated states by age and inquiry_type.",
        "Notify the owner, then leadership, at each tier.",
        "Clear the escalation once a response is recorded.",
        "Track response times for reporting.",
        "Log each state change.",
    ],
}


_EXCEPTION_HANDLING: dict[str, str] = {
    # ---- OpsPilot ----
    "Missing Document Follow-Up": (
        "If the requester is unreachable or the required-document list is undefined for the request_type, route to the owner "
        "for manual handling. Reminders are suppressed once documents are received (idempotent), so a re-run never re-chases a "
        "satisfied request. Flow failures alert the automation owner via run-history monitoring."
    ),
    "Approval Reminder Automation": (
        "If the approver is out of office or unassigned, route to the backup approver or owner; a Rejected approval notifies the "
        "requester with the reason. Reminders are keyed on request_id + approver_id so re-runs do not double-nudge, and are "
        "cancelled on decision. Flow failures alert the automation owner via run-history monitoring."
    ),
    "Duplicate Request Detection": (
        "Never auto-close on a partial-key match; ambiguous matches always go to a human. Merges are idempotent -- re-running "
        "does not re-merge an already-linked pair. Flow failures alert the automation owner via run-history monitoring."
    ),
    "Auto-Routing by Request Type": (
        "Unmapped request_types and capacity-exhausted routes fall back to the manual triage queue. Assignment is idempotent "
        "(a re-run does not reassign an already-owned request). Flow failures alert the automation owner via run-history monitoring."
    ),
    "SLA Escalation Alerts": (
        "Requests missing sla_days use the request_type default SLA; Closed requests are excluded. Each threshold fires once per "
        "request (idempotent), keyed on request_id + threshold, so repeated scans never re-alert. Flow failures alert the "
        "automation owner via run-history monitoring."
    ),
    "Request Intake Validation": (
        "Unknown request_types route to triage rather than hard-failing. Validation is idempotent and re-runs safely on "
        "resubmission. Flow failures alert the automation owner via run-history monitoring."
    ),
    "Recurring Status Summary": (
        "If source data is unavailable or stale, send a clearly-labeled partial summary and alert the owner; a missed schedule "
        "triggers a catch-up run. Runs are idempotent per reporting period (keyed on period_id) so a retry does not double-send. "
        "Flow failures alert the automation owner via run-history monitoring."
    ),
    "Rework Prevention Checklist": (
        "Items that cannot be auto-verified are marked for owner attestation rather than blocking indefinitely. Checklist state is "
        "idempotent across re-runs. Flow failures alert the automation owner via run-history monitoring."
    ),
    # ---- RescueOps ----
    "Adoption Inquiry Triage": (
        "Medical, safety, compatibility, and surrender concerns are always routed to a human reviewer; the automation only drafts "
        "and prioritizes, it never sends an adoption decision. Draft generation is idempotent per inquiry_id. Flow failures alert "
        "the automation owner via run-history monitoring."
    ),
    "Foster Match Recommendation": (
        "When no open capacity exists, escalate the foster gap in the weekly brief rather than forcing a placement; medical cases "
        "without a qualified foster always route to a coordinator. Recommendations are idempotent per dog_id until status changes. "
        "Flow failures alert the automation owner via run-history monitoring."
    ),
    "Medical Funding Priority Alert": (
        "Funding figures use only structured expense records; no medical claims are generated and fully-funded cases drop off "
        "automatically. The alert is idempotent per run (keyed on dog_id + run_id). Flow failures alert the automation owner via "
        "run-history monitoring."
    ),
    "Dog Bio/Social Post Generator": (
        "Any field outside the approved set is omitted, and every draft requires human approval before publishing. Generation is "
        "idempotent per dog_id until the flag clears, so a re-run does not duplicate drafts. Flow failures alert the automation "
        "owner via run-history monitoring."
    ),
    "Volunteer Task Reminder": (
        "Unassigned or ownerless tasks route to the coordinator; reminders are suppressed once a task is complete. Reminders are "
        "keyed on task_id + volunteer_id to prevent duplicates. Flow failures alert the automation owner via run-history monitoring."
    ),
    "Weekly Founder Brief": (
        "Missing or stale sources produce labeled gaps, not silent omissions; a missed schedule triggers a catch-up run. The brief "
        "is idempotent per week (keyed on week_id) so a retry does not double-send. Flow failures alert the automation owner via "
        "run-history monitoring."
    ),
    "Unanswered Message Escalation": (
        "Type-specific thresholds apply (surrender/safety are shortest) and Responded inquiries are excluded. Each tier fires once "
        "per inquiry (idempotent), keyed on inquiry_id + tier, so repeat scans never re-alert. Flow failures alert the automation "
        "owner via run-history monitoring."
    ),
}


_NOTIFICATION_LOGIC: dict[str, str] = {
    # ---- OpsPilot ----
    "Missing Document Follow-Up": (
        "The requester gets the missing-items list on trigger and one reminder at the window; the owner is copied on escalation. "
        "Notifications are keyed on request_id + rule_id so a re-run never double-sends."
    ),
    "Approval Reminder Automation": (
        "The approver gets reminders, the manager gets the escalation, and the requester is notified on the final decision. "
        "Reminders are keyed on request_id + approver_id to prevent duplicate nudges."
    ),
    "Duplicate Request Detection": (
        "The owner receives the duplicate candidates for confirmation; the requester is notified only after a confirmed merge or "
        "close. Alerts are keyed on the request_id pair to avoid repeat notifications."
    ),
    "Auto-Routing by Request Type": (
        "The assigned owner is notified on routing and the triage lead is notified for unmapped types. Notifications are keyed on "
        "request_id so re-runs do not re-notify."
    ),
    "SLA Escalation Alerts": (
        "The owner is alerted at 75%, the manager at 100%, and the department lead at 125%. One alert per threshold crossing, "
        "keyed on request_id + threshold, so repeated scans never re-alert."
    ),
    "Request Intake Validation": (
        "The requester receives inline validation errors; the owner is notified only when a request repeatedly fails validation. "
        "Notifications are keyed on request_id + submission attempt."
    ),
    "Recurring Status Summary": (
        "The leadership audience receives the scheduled summary; the report owner is alerted on an empty audience, stale data, or "
        "a failed send. Sends are keyed on period_id."
    ),
    "Rework Prevention Checklist": (
        "The owner is notified on blocked checklist items and on repeated checklist failures for a request_type. Notifications are "
        "keyed on request_id + checklist_id."
    ),
    # ---- RescueOps ----
    "Adoption Inquiry Triage": (
        "The volunteer owner receives the prioritized response queue; leadership is alerted on safety or medical escalations. "
        "Follow-ups are keyed on inquiry_id to avoid duplicates."
    ),
    "Foster Match Recommendation": (
        "The foster coordinator receives the ranked matches; leadership is alerted when a high-need dog has no viable match. "
        "Notifications are keyed on dog_id."
    ),
    "Medical Funding Priority Alert": (
        "The founder/leadership receive the ranked funding priorities; no automated donor-facing messages are sent. Notifications "
        "are keyed on dog_id + run_id."
    ),
    "Dog Bio/Social Post Generator": (
        "The content/social owner receives drafts for approval; nothing auto-publishes. Drafts are keyed on dog_id so a re-run "
        "does not duplicate them."
    ),
    "Volunteer Task Reminder": (
        "The assigned volunteer gets task reminders and the coordinator gets overdue escalations. Reminders are keyed on "
        "task_id + volunteer_id."
    ),
    "Weekly Founder Brief": (
        "The founder/leadership receive the weekly brief; the brief owner is alerted on data gaps or a failed send. Sends are "
        "keyed on week_id."
    ),
    "Unanswered Message Escalation": (
        "The owner is alerted at overdue and leadership at escalation. One alert per tier, keyed on inquiry_id + tier, so repeat "
        "scans never re-alert."
    ),
}


def _opspilot_trigger(name: str) -> str:
    return _TRIGGERS.get(name, "New request enters the workflow or a scheduled monitoring job runs.")


def _rescueops_trigger(name: str) -> str:
    return _TRIGGERS.get(name, "Scheduled weekly review or a change in rescue operations data.")


def _decision_rules(name: str, domain: str) -> list[str]:
    rules = _DECISION_RULES.get(name)
    if rules is not None:
        return rules
    if domain == "OpsPilot":
        return [
            "Evaluate the request against SLA age, status, stage, missing-document, duplicate, and approval fields.",
            "Route standard cases through deterministic rules and flag ambiguous cases for human owner review.",
            "Escalate high-priority or critical business-impact work faster than standard-priority work.",
        ]
    return [
        "Use only structured rescue data and avoid unsupported medical or behavioral claims.",
        "Route medical, safety, adoption, and foster-placement decisions to a human reviewer.",
        "Prioritize cases by urgency, days waiting, funding gap, foster gap, and mission impact.",
    ]


def _workflow_steps(name: str, domain: str) -> list[str]:
    steps = _WORKFLOW_STEPS.get(name)
    if steps is not None:
        return steps
    return [
        "Monitor source data for the trigger condition.",
        "Apply the scoring or routing rules.",
        "Generate the recommended action.",
        "Notify the responsible owner.",
        "Track completion, exceptions, and outcomes.",
        "Summarize results in the leadership reporting cadence.",
    ]


def _exception_handling(name: str, domain: str) -> str:
    text = _EXCEPTION_HANDLING.get(name)
    if text is not None:
        return text
    if domain == "OpsPilot":
        return (
            "High-priority, critical-impact, rejected-approval, or ambiguous-duplicate cases notify the assigned owner "
            "immediately. Flow failures alert the automation owner via run-history monitoring."
        )
    return (
        "Medical, safety, compatibility, surrender, and placement concerns are routed to rescue leadership or the appropriate "
        "licensed professional. Flow failures alert the automation owner via run-history monitoring."
    )


def _notification_logic(name: str, domain: str) -> str:
    text = _NOTIFICATION_LOGIC.get(name)
    if text is not None:
        return text
    if domain == "OpsPilot":
        return (
            "Send requester updates for standard cases, owner alerts for aging work, and manager escalations for SLA breach "
            "risk. Notifications are keyed on request_id to prevent duplicates."
        )
    return (
        "Send volunteer task notifications for routine work and founder/leadership alerts for urgent medical, foster, or safety "
        "cases. Notifications are keyed on the case id to prevent duplicates."
    )


def _mvp_version(name: str, domain: str) -> str:
    if domain == "OpsPilot":
        return "Use CSV or SQLite data, scheduled rule checks, Streamlit review queue, and downloadable leadership report."
    return "Use local rescue CSV data, Streamlit review queue, safe template generation, and weekly founder brief export."
