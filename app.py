from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.automation_ranker import (
    blueprint_to_markdown,
    build_combined_automation_ranker,
    build_opspilot_automation_ranker,
    build_rescueops_automation_ranker,
    get_automation_blueprint,
)
from modules.data_generator import ensure_data
from modules.opspilot_analyzer import (
    bottleneck_insight,
    detect_bottlenecks,
    get_operational_problem_statement,
    get_opspilot_chart_data,
    load_opspilot_data,
    summarize_opspilot,
)
from modules.report_generator import (
    generate_opspilot_report,
    generate_rescueops_report,
    markdown_to_html,
    markdown_to_text,
)
from modules.rescueops_analyzer import (
    foster_matching,
    generate_dog_content,
    get_rescueops_chart_data,
    load_rescueops_data,
    medical_priority_scoring,
    safety_boundaries,
    summarize_rescueops,
    triage_adoption_inquiries,
    weekly_founder_brief,
)
from modules.roi_calculator import calculate_opspilot_roi, calculate_rescueops_roi
from modules.classification import blended_save_rate
from modules.scoring import PRIORITY_ORDER, data_today
from modules import ui_components as ui


BASE_DIR = Path(__file__).resolve().parent
COLOR_SEQUENCE = ["#0f766e", "#2563eb", "#b7791f", "#be123c", "#4b5563", "#0e7490", "#7c3aed"]
# Bump when the data schema changes so the cached loader below is invalidated.
SCHEMA_VERSION = 2


st.set_page_config(
    page_title="OpsPilot Command Center",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Preparing synthetic operations data...")
def load_demo_data(base_dir: str, schema_version: int = SCHEMA_VERSION):
    paths = ensure_data(Path(base_dir) / "data")
    opspilot = load_opspilot_data(paths["opspilot"])
    dogs, inquiries, volunteers, medical = load_rescueops_data(paths)
    return opspilot, dogs, inquiries, volunteers, medical


def main() -> None:
    ui.inject_css()
    opspilot_df, dogs, inquiries, volunteers, medical = load_demo_data(str(BASE_DIR))

    with st.sidebar:
        st.markdown("## OpsPilot")
        page = st.radio(
            "Navigation",
            [
                "Home / Executive Overview",
                "OpsPilot Demo",
                "RescueOps Demo",
                "Automation Opportunity Ranker",
                "ROI & Business Case",
                "Executive Report Generator",
                "About This Project",
            ],
        )
        st.divider()
        st.caption(
            "Recommendations are rule-based and fully local -- no data leaves the "
            "machine and no external API is called."
        )
        st.caption("All demo data is synthetic and generated locally.")

    if page == "Home / Executive Overview":
        render_home(opspilot_df, dogs, inquiries, volunteers, medical)
    elif page == "OpsPilot Demo":
        render_opspilot_demo(opspilot_df)
    elif page == "RescueOps Demo":
        render_rescueops_demo(dogs, inquiries, volunteers, medical)
    elif page == "Automation Opportunity Ranker":
        render_automation_ranker(opspilot_df, dogs, inquiries, volunteers, medical)
    elif page == "ROI & Business Case":
        render_roi_page(opspilot_df, dogs, inquiries, medical)
    elif page == "Executive Report Generator":
        render_report_generator(opspilot_df, dogs, inquiries, volunteers, medical)
    else:
        render_about_page()


def render_home(
    opspilot_df: pd.DataFrame,
    dogs: pd.DataFrame,
    inquiries: pd.DataFrame,
    volunteers: pd.DataFrame,
    medical: pd.DataFrame,
) -> None:
    ops_summary = summarize_opspilot(opspilot_df)
    rescue_summary = summarize_rescueops(dogs, inquiries, volunteers, medical)
    combined_ranker = build_combined_automation_ranker(opspilot_df, dogs, inquiries, volunteers, medical)

    ui.page_header(
        "OpsPilot Command Center",
        "Turn messy operations into measurable automation opportunities.",
        "Process Improvement & Automation Intelligence Platform",
    )
    st.markdown(
        "OpsPilot analyzes operational activity, identifies bottlenecks, ranks automation opportunities, "
        "estimates ROI, and generates leadership-ready improvement recommendations."
    )

    selected_mode = st.radio(
        "Demo mode selector",
        ["General Operations Demo: OpsPilot", "Nonprofit Rescue Demo: RescueOps"],
        horizontal=True,
    )

    if selected_mode.startswith("General"):
        ui.insight_box(
            "Summit Services Group",
            "A mid-sized organization struggling with delayed internal requests, approval bottlenecks, missing documentation, duplicate work, and poor visibility into operational workload.",
            "info",
        )
    else:
        ui.insight_box(
            "Life's Paw-pose",
            "An all-volunteer rescue managing dogs, fosters, adoption inquiries, medical needs, volunteer tasks, and donation priorities with limited manpower.",
            "success",
        )

    top_auto = combined_ranker.iloc[0] if not combined_ranker.empty else None
    ui.metric_cards(
        [
            ("Ops requests analyzed", ui.number(ops_summary["total_requests"]), "Synthetic operational request volume"),
            ("Ops SLA breach rate", ui.percent(ops_summary["sla_breach_rate"]), "Process reliability signal"),
            ("Rescue dogs in care", ui.number(rescue_summary["dogs_in_care"]), "Active rescue pipeline"),
            ("Rescue unanswered messages", ui.number(rescue_summary["unanswered_messages"]), "Volunteer response burden"),
            (
                "Top automation score",
                f"{top_auto['Automation Score']:.1f}" if top_auto is not None else "n/a",
                top_auto["Automation Candidate"] if top_auto is not None else "No candidates yet",
            ),
            ("Potential ops savings", ui.money(ops_summary["potential_monthly_savings"]), "Estimated monthly opportunity"),
        ],
        columns=3,
    )

    left, right = st.columns(2)
    with left:
        ui.section_title("Cross-Domain Framework")
        st.markdown(
            """
            - Operational volume and backlog
            - Aging, SLA risk, and bottleneck detection
            - Automation opportunity scoring
            - ROI or mission-impact estimate
            - Executive-ready recommendations
            """
        )
    with right:
        ui.section_title("Top Shared Automation Opportunities")
        st.dataframe(
            ui.score_style(
                combined_ranker[
                    [
                        "Rank",
                        "Domain",
                        "Automation Candidate",
                        "Volume",
                        "Estimated Hours Saved",
                        "Automation Score",
                    ]
                ].head(7)
            ),
            width="stretch",
            hide_index=True,
        )


def render_opspilot_demo(opspilot_df: pd.DataFrame) -> None:
    bottlenecks = detect_bottlenecks(opspilot_df)
    summary = summarize_opspilot(opspilot_df, bottlenecks=bottlenecks)
    insight = bottleneck_insight(bottlenecks)
    chart_data = get_opspilot_chart_data(opspilot_df, bottlenecks)
    automations = build_opspilot_automation_ranker(opspilot_df)

    ui.page_header(
        "OpsPilot Demo",
        "Summit Services Group operations intelligence dashboard.",
        "General Operations",
    )
    # Lead with the four tiles that carry the story; the rest are one click away so
    # the headline is not buried under a wall of equal-weight metrics.
    ui.metric_cards(
        [
            ("SLA Breach Rate", ui.percent(summary["sla_breach_rate"]), "Risk and service quality"),
            ("Est. Monthly Manual-Work Cost", ui.money(summary["estimated_monthly_waste"]), "Recent 30-day manual effort"),
            ("Top Bottleneck Stage", summary["top_bottleneck_stage"], "Largest source of delay"),
            ("Potential Monthly Savings", ui.money(summary["potential_monthly_savings"]), "Coverage x blended save rate"),
        ],
        columns=4,
    )
    with st.expander("More operational metrics"):
        ui.metric_cards(
            [
                ("Total Requests", ui.number(summary["total_requests"]), "All synthetic requests"),
                ("Open Requests", ui.number(summary["open_requests"]), "Currently unresolved"),
                ("Average Cycle Time", f"{summary['average_cycle_time']:.1f} days", "Closed-request duration"),
                ("Oldest Open Request", f"{summary['oldest_open_request']} days", "Maximum current age"),
                ("Estimated Manual Hours", ui.number(summary["estimated_manual_hours"], 1), "Total tracked effort"),
                ("Top Automation Candidate", summary["top_automation_candidate"], "Highest manual impact"),
            ],
            columns=3,
        )

    tab_summary, tab_bottlenecks, tab_automations, tab_workflow = st.tabs(
        ["Executive Summary", "Bottleneck Analysis", "Automation Opportunities", "Recommended Workflow"]
    )

    with tab_summary:
        ui.insight_box("Executive Insight", get_operational_problem_statement(summary, insight), "info")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(bar_chart(chart_data["requests_by_department"], "department", "requests", "Requests by Department"), width="stretch")
            st.plotly_chart(horizontal_bar(chart_data["avg_cycle_by_type"], "request_type", "avg_cycle_time", "Average Cycle Time by Request Type"), width="stretch")
        with right:
            st.plotly_chart(bar_chart(chart_data["requests_by_stage"], "process_stage", "requests", "Requests by Process Stage"), width="stretch")
            st.plotly_chart(sla_breach_rate_chart(chart_data["breach_rate_by_department"]), width="stretch")
        st.plotly_chart(weekly_volume_trend(opspilot_df), width="stretch")

    with tab_bottlenecks:
        ui.insight_box("Bottleneck Detection", insight, "warning")
        bottleneck_display = bottlenecks.copy()
        bottleneck_display["breach_rate"] = (bottleneck_display["breach_rate"] * 100).round(1)
        bottleneck_display["delay_contribution"] = (bottleneck_display["delay_contribution"] * 100).round(1)
        bottleneck_display["missing_doc_rate"] = (bottleneck_display["missing_doc_rate"] * 100).round(1)
        st.dataframe(
            bottleneck_display[
                [
                    "process_stage",
                    "volume",
                    "open_count",
                    "avg_days_open",
                    "breach_rate",
                    "delay_contribution",
                    "missing_doc_rate",
                    "bottleneck_score",
                ]
            ].rename(
                columns={
                    "process_stage": "Process Stage",
                    "volume": "Volume",
                    "open_count": "Open Count",
                    "avg_days_open": "Avg Days Open",
                    "breach_rate": "Breach Rate %",
                    "delay_contribution": "Delay Contribution %",
                    "missing_doc_rate": "Missing Doc Rate %",
                    "bottleneck_score": "Bottleneck Score",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        left, right = st.columns(2)
        with left:
            st.plotly_chart(horizontal_bar(bottlenecks, "process_stage", "bottleneck_score", "Bottleneck Stage Breakdown"), width="stretch")
        with right:
            st.plotly_chart(horizontal_bar(chart_data["manual_hours_by_type"], "request_type", "manual_hours", "Manual Hours by Request Type"), width="stretch")

    with tab_automations:
        ui.insight_box(
            "Automation Strategy",
            "Scores combine volume, manual effort, repeatability, SLA impact, rule clarity, and implementation complexity.",
            "success",
        )
        st.dataframe(
            ui.score_style(automations),
            width="stretch",
            hide_index=True,
        )
        st.plotly_chart(
            horizontal_bar(chart_data["automation_impact"], "automation_candidate_type", "manual_hours", "Automation Candidates by Estimated Impact"),
            width="stretch",
        )

    with tab_workflow:
        render_blueprint_picker(automations, "OpsPilot")


def render_rescueops_demo(
    dogs: pd.DataFrame, inquiries: pd.DataFrame, volunteers: pd.DataFrame, medical: pd.DataFrame
) -> None:
    summary = summarize_rescueops(dogs, inquiries, volunteers, medical)
    chart_data = get_rescueops_chart_data(dogs, inquiries, volunteers, medical)
    triage = triage_adoption_inquiries(inquiries, dogs)
    matches = foster_matching(dogs, volunteers)
    medical_priority = medical_priority_scoring(dogs, medical)
    automations = build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical)
    founder_brief = weekly_founder_brief(summary, dogs, inquiries, medical_priority, matches)

    ui.page_header(
        "RescueOps Demo",
        "Life's Paw-pose rescue operations and automation dashboard.",
        "Nonprofit Operations",
    )
    ui.metric_cards(
        [
            ("Dogs in Care", ui.number(summary["dogs_in_care"]), "Active non-adopted dogs"),
            ("Urgent Medical Cases", ui.number(summary["urgent_medical_cases"]), "Leadership review needed"),
            ("Unanswered Messages", ui.number(summary["unanswered_messages"]), "Response backlog"),
            ("Unfunded Medical Need", ui.money(summary["unfunded_medical_need"]), "Estimated visible gap"),
        ],
        columns=4,
    )
    with st.expander("More rescue metrics"):
        ui.metric_cards(
            [
                ("Dogs Needing Foster", ui.number(summary["dogs_needing_foster"]), "Capacity gap signal"),
                ("Dogs Adoption Ready", ui.number(summary["dogs_adoption_ready"]), "Ready for visibility"),
                ("Open Adoption Inquiries", ui.number(summary["open_adoption_inquiries"]), "Adoption queue"),
                ("Monthly Medical Costs", ui.money(summary["monthly_medical_costs"]), "Recent 30-day costs"),
                ("Volunteer Capacity", ui.number(summary["volunteer_capacity"]), "Open foster slots"),
                ("Highest Priority Dog", summary["highest_priority_dog"], "Structured priority view"),
            ],
            columns=3,
        )

    tab_summary, tab_triage, tab_foster, tab_medical, tab_social = st.tabs(
        ["Executive Summary", "Inquiry Triage", "Foster Matching", "Medical Priority", "Social & Founder Brief"]
    )

    with tab_summary:
        ui.insight_box(
            "Mission Operations Insight",
            "The rescue needs faster inquiry response, clearer foster-capacity visibility, medical funding prioritization, and repeatable founder reporting.",
            "success",
        )
        left, right = st.columns(2)
        with left:
            st.plotly_chart(bar_chart(chart_data["dogs_by_status"], "current_status", "dogs", "Dogs by Status"), width="stretch")
            st.plotly_chart(bar_chart(chart_data["adoption_pipeline"], "adoption_status", "dogs", "Adoption Pipeline"), width="stretch")
            st.plotly_chart(bar_chart(chart_data["foster_capacity_vs_need"], "category", "count", "Foster Capacity vs Foster Need"), width="stretch")
        with right:
            st.plotly_chart(horizontal_bar(chart_data["dogs_by_medical_status"], "medical_status", "dogs", "Dogs by Medical Status"), width="stretch")
            st.plotly_chart(bar_chart(chart_data["inquiry_types"], "inquiry_type", "inquiries", "Inquiry Types"), width="stretch")
            st.plotly_chart(horizontal_bar(chart_data["volunteer_role_coverage"], "role", "volunteers", "Volunteer Role Coverage"), width="stretch")

        ui.section_title("Safety & Responsibility Boundaries")
        for boundary in safety_boundaries():
            st.markdown(f"- {boundary}")

    with tab_triage:
        ui.insight_box(
            "Adoption Inquiry Triage",
            "Inquiries are classified by match strength, missing information, compatibility concerns, wait time, and human-review need.",
            "warning",
        )
        triage_display = triage[
            [
                "inquiry_id",
                "dog_name",
                "applicant_name",
                "days_waiting",
                "triage_category",
                "priority_score",
                "recommended_action",
                "follow_up_questions",
            ]
        ].head(60)
        st.dataframe(triage_display, width="stretch", hide_index=True)
        st.plotly_chart(bar_chart(chart_data["inquiry_response_aging"], "aging_bucket", "inquiries", "Inquiry Response Aging"), width="stretch")

    with tab_foster:
        ui.insight_box(
            "Foster Matching",
            "Matches consider capacity, transport, medical handling, senior experience, large-dog comfort, reliability, and availability.",
            "info",
        )
        st.dataframe(matches.head(60), width="stretch", hide_index=True)

    with tab_medical:
        ui.insight_box(
            "Medical Priority Scoring",
            "Scores combine urgency, funding need, medical status, days in care, and adoption-readiness impact.",
            "risk",
        )
        st.dataframe(medical_priority.head(60), width="stretch", hide_index=True)
        left, right = st.columns(2)
        with left:
            st.plotly_chart(horizontal_bar(chart_data["medical_costs_by_dog"], "dog_name", "amount", "Top 15 Dogs by Medical Cost"), width="stretch")
        with right:
            st.plotly_chart(horizontal_bar(chart_data["medical_costs_by_type"], "expense_type", "amount", "Medical Costs by Expense Type"), width="stretch")

    with tab_social:
        content_queue = dogs[(dogs["bio_needed"]) | (dogs["social_post_needed"])].copy()
        # Sort by true severity rank, not the alphabetical string (Medium would
        # otherwise outrank Critical). Drop the helper column before display.
        content_queue["_priority_rank"] = content_queue["priority_level"].map(PRIORITY_ORDER).fillna(0)
        content_queue = content_queue.sort_values(
            ["_priority_rank", "days_in_care"], ascending=False
        ).drop(columns="_priority_rank")
        if content_queue.empty:
            st.info("No dogs are currently flagged for generated bios or social posts.")
        else:
            selected_dog = st.selectbox("Dog content queue", content_queue["dog_name"].tolist())
            dog = dogs[dogs["dog_name"] == selected_dog].iloc[0]
            dog_medical = medical[medical["dog_name"] == selected_dog]
            content = generate_dog_content(dog, dog_medical)
            for tab, (title, body) in zip(st.tabs(list(content.keys())), content.items()):
                with tab:
                    st.markdown(body)

        ui.section_title("Weekly Founder Brief")
        st.markdown(founder_brief)

        ui.section_title("RescueOps Automation Opportunities")
        st.dataframe(ui.score_style(automations), width="stretch", hide_index=True)


def render_automation_ranker(
    opspilot_df: pd.DataFrame,
    dogs: pd.DataFrame,
    inquiries: pd.DataFrame,
    volunteers: pd.DataFrame,
    medical: pd.DataFrame,
) -> None:
    ui.page_header(
        "Automation Opportunity Ranker",
        "Shared scoring model for business operations and nonprofit rescue workflows.",
        "Automation Strategy",
    )
    combined = build_combined_automation_ranker(opspilot_df, dogs, inquiries, volunteers, medical)
    domain_filter = st.selectbox("Domain", ["All", "OpsPilot", "RescueOps"])
    view = combined if domain_filter == "All" else combined[combined["Domain"] == domain_filter]

    ui.insight_box(
        "Scoring Formula",
        "Automation score weighs effort saved, repeatability, impact, rule clarity, and an ease-of-implementation credit on an absolute 0-100 scale, so it is comparable across domains and stable as candidates change.",
        "info",
    )
    if not view.empty:
        st.plotly_chart(automation_score_chart(view), width="stretch")
    st.dataframe(ui.score_style(view), width="stretch", hide_index=True)

    if not view.empty:
        selected = st.selectbox(
            "Blueprint candidate",
            view["Automation Candidate"].tolist(),
            key="ranker_blueprint_candidate",
        )
        row = view[view["Automation Candidate"] == selected].iloc[0]
        blueprint = get_automation_blueprint(selected, row["Domain"], row["Estimated Hours Saved"])
        st.markdown(blueprint_to_markdown(blueprint))


def render_roi_page(
    opspilot_df: pd.DataFrame,
    dogs: pd.DataFrame,
    inquiries: pd.DataFrame,
    medical: pd.DataFrame,
) -> None:
    ui.page_header(
        "ROI & Business Case",
        "Estimate financial value for OpsPilot and mission capacity for RescueOps.",
        "Business Value",
    )
    tab_ops, tab_rescue = st.tabs(["OpsPilot ROI", "RescueOps Mission Impact"])

    with tab_ops:
        recent_volume = monthly_opspilot_volume(opspilot_df)
        default_minutes = float(opspilot_df["estimated_manual_minutes"].mean())
        # Default "time saved per request" is the blended save rate the home page
        # uses, so the ROI page and the headline savings figure agree by default.
        default_time_saved = int(round(blended_save_rate(opspilot_df) * 100))
        left, right = st.columns(2)
        with left:
            hourly_rate = st.number_input("Average staff hourly rate", min_value=10.0, max_value=150.0, value=45.0, step=5.0)
            manual_minutes = st.number_input("Manual minutes per request", min_value=5.0, max_value=180.0, value=round(default_minutes, 1), step=5.0)
            monthly_volume = st.number_input("Monthly request volume", min_value=1, max_value=5000, value=recent_volume, step=25)
        with right:
            percent_automated = st.slider("Percent automated (coverage)", 5, 90, 35)
            time_saved_pct = st.slider("Time saved per automated request", 20, 95, default_time_saved)
            build_cost = st.number_input("One-time build cost", min_value=0.0, max_value=200000.0, value=12000.0, step=1000.0)
            maintenance_cost = st.number_input("Monthly maintenance cost", min_value=0.0, max_value=20000.0, value=400.0, step=100.0)

        roi = calculate_opspilot_roi(
            hourly_rate, manual_minutes, monthly_volume, percent_automated, time_saved_pct, build_cost, maintenance_cost
        )
        payback = roi["payback_months"]
        if payback == float("inf"):
            payback_display = "Not recoverable"
        elif payback == 0.0:
            payback_display = "Immediate"
        else:
            payback_display = f"{payback:.1f} months"
        roi_pct = roi["first_year_roi_pct"]
        roi_display = "n/a" if roi_pct is None else f"{roi_pct:.0f}%"
        ui.metric_cards(
            [
                ("Monthly Hours Saved", ui.number(roi["monthly_hours_saved"], 1), "Estimated labor capacity"),
                ("Monthly Labor Savings", ui.money(roi["monthly_labor_savings"]), "Gross monthly value"),
                ("Annual Labor Savings", ui.money(roi["annual_labor_savings"]), "Gross run-rate"),
                ("First-Year Net Savings", ui.money(roi["annual_net_savings"]), "After build + maintenance"),
                ("Payback Period", payback_display, "Time to recover build cost"),
                ("First-Year ROI", roi_display, "Return on build cost"),
            ],
            columns=3,
        )
        ui.insight_box("Qualitative Business Value", roi["qualitative_business_value"], "success")

        ui.section_title("Sensitivity Analysis")
        st.caption("First-year net savings and payback across conservative / expected / optimistic assumptions.")
        st.dataframe(
            opspilot_sensitivity(hourly_rate, manual_minutes, monthly_volume, percent_automated, build_cost, maintenance_cost),
            width="stretch",
            hide_index=True,
        )
        ui.assumptions_panel(
            [
                f"Staff hourly rate: ${hourly_rate:,.0f}",
                f"Automation coverage (share of volume automated): {percent_automated}%",
                f"Time saved per automated request: {time_saved_pct}% (defaults to the blended save rate)",
                f"Monthly request volume: {monthly_volume:,}",
                f"One-time build cost: ${build_cost:,.0f}; monthly maintenance: ${maintenance_cost:,.0f}",
                "Labor savings only; qualitative benefits (fewer errors, faster response) are not dollarized.",
            ]
        )
        st.caption("ROI is an estimate for demo purposes and should be validated against real operational data.")

    with tab_rescue:
        recent_inquiries = monthly_inquiry_volume(inquiries)
        left, right = st.columns(2)
        with left:
            volunteer_value = st.number_input("Volunteer hourly value", min_value=5.0, max_value=100.0, value=28.0, step=2.0)
            monthly_inquiries = st.number_input("Monthly inquiries", min_value=1, max_value=3000, value=recent_inquiries, step=10)
            response_minutes = st.number_input("Minutes per manual response", min_value=2.0, max_value=90.0, value=14.0, step=2.0)
        with right:
            active_dogs = int((dogs["current_status"] != "Adopted").sum())
            dogs_in_care = st.number_input("Dogs in care", min_value=0, max_value=500, value=active_dogs, step=1)
            medical_expenses = st.number_input("Monthly medical expenses", min_value=0.0, max_value=100000.0, value=float(recent_medical_costs(medical)), step=250.0)
            admin_reduction = st.slider("Expected admin reduction", 5, 80, 35)
            faster_response = st.slider("Expected faster response rate", 5, 90, 45)

        roi = calculate_rescueops_roi(
            volunteer_value,
            monthly_inquiries,
            response_minutes,
            dogs_in_care,
            medical_expenses,
            admin_reduction,
            faster_response,
        )
        ui.metric_cards(
            [
                ("Volunteer Hours Saved", ui.number(roi["volunteer_hours_saved"], 1), "Monthly estimate"),
                ("Monthly Volunteer Value", ui.money(roi["monthly_volunteer_value"]), "Illustrative equivalent"),
                ("Annual Volunteer Value", ui.money(roi["monthly_volunteer_value"] * 12), "Run-rate estimate"),
                ("Inquiries Handled Faster", ui.number(roi["estimated_inquiries_handled_faster"], 0), "Monthly estimate"),
            ],
            columns=2,
        )
        ui.insight_box("Mission Impact Summary", roi["mission_impact_summary"], "success")
        ui.assumptions_panel(
            [
                f"Volunteer time valued at ${volunteer_value:,.0f}/hour (illustrative, not paid wages)",
                f"Monthly inquiries: {monthly_inquiries:,}; minutes per manual response: {response_minutes:.0f}",
                f"Expected admin reduction: {admin_reduction}%; faster response rate: {faster_response}%",
                "Value is volunteer-time and response-capacity only; medical funding needs are tracked separately.",
            ]
        )
        st.caption("Mission impact is an estimate for demo purposes and should be validated with actual rescue operations data.")


def render_report_generator(
    opspilot_df: pd.DataFrame,
    dogs: pd.DataFrame,
    inquiries: pd.DataFrame,
    volunteers: pd.DataFrame,
    medical: pd.DataFrame,
) -> None:
    ui.page_header(
        "Executive Report Generator",
        "Create a leadership-ready brief from the selected demo.",
        "Leadership Communication",
    )
    report_type = st.radio("Report type", ["OpsPilot", "RescueOps"], horizontal=True)

    if report_type == "OpsPilot":
        bottlenecks = detect_bottlenecks(opspilot_df)
        summary = summarize_opspilot(opspilot_df, bottlenecks=bottlenecks)
        automations = build_opspilot_automation_ranker(opspilot_df)
        roi = default_opspilot_roi(opspilot_df, summary)
        report = generate_opspilot_report(summary, bottlenecks, automations, roi)
        title = "opspilot-leadership-brief"
    else:
        summary = summarize_rescueops(dogs, inquiries, volunteers, medical)
        automations = build_rescueops_automation_ranker(dogs, inquiries, volunteers, medical)
        medical_priority = medical_priority_scoring(dogs, medical)
        matches = foster_matching(dogs, volunteers)
        brief = weekly_founder_brief(summary, dogs, inquiries, medical_priority, matches)
        roi = default_rescueops_roi(dogs, inquiries, medical)
        report = generate_rescueops_report(summary, medical_priority, automations, brief, roi)
        title = "rescueops-leadership-brief"

    html_report = markdown_to_html(report, title.replace("-", " ").title())
    txt_report = markdown_to_text(report)

    tab_preview, tab_source = st.tabs(["Rendered Brief", "Markdown Source"])
    with tab_preview:
        with st.container(border=True):
            st.markdown(report)
    with tab_source:
        st.code(report, language="markdown")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("Download Markdown", report, file_name=f"{title}.md", mime="text/markdown")
    with col2:
        st.download_button("Download Text", txt_report, file_name=f"{title}.txt", mime="text/plain")
    with col3:
        st.download_button("Download HTML", html_report, file_name=f"{title}.html", mime="text/html")


def render_about_page() -> None:
    ui.page_header(
        "About This Project",
        "A cross-domain operations intelligence and automation strategy MVP.",
        "Portfolio Value",
    )
    st.markdown(
        """
        OpsPilot Command Center was built as a cross-domain operations intelligence and automation strategy MVP.
        It demonstrates how messy operational data can be transformed into bottleneck analysis, automation
        recommendations, ROI estimates, and executive-ready action plans.

        The project demonstrates Python development, Streamlit dashboarding, process improvement, automation
        architecture, business intelligence, synthetic data generation, domain modeling, executive communication,
        responsible AI-style support, and scalable MVP design.
        """
    )

    left, right = st.columns(2)
    with left:
        ui.section_title("What This MVP Does")
        st.markdown(
            """
            - Analyzes process data
            - Identifies bottlenecks
            - Ranks automation opportunities
            - Estimates time and cost savings
            - Generates automation blueprints
            - Creates executive summaries
            - Demonstrates cross-industry applicability
            """
        )
    with right:
        ui.section_title("What a Production Version Would Add")
        st.markdown(
            """
            - Authentication and role-based access
            - Microsoft 365, Gmail, Facebook, or CRM integrations
            - Database backend and scheduled automations
            - Audit logs and secure file storage
            - API integrations and human approval workflows
            - Cloud deployment and monitoring
            """
        )

    ui.insight_box(
        "Portfolio Talking Point",
        "This app shows the ability to walk into a messy operation, identify what is broken, design practical automation, estimate value, and communicate the business case clearly.",
        "success",
    )


def render_blueprint_picker(automations: pd.DataFrame, domain: str) -> None:
    selected = st.selectbox("Automation candidate", automations["Automation Candidate"].tolist(), key=f"{domain}_blueprint")
    row = automations[automations["Automation Candidate"] == selected].iloc[0]
    blueprint = get_automation_blueprint(selected, domain, row["Estimated Hours Saved"])
    st.markdown(blueprint_to_markdown(blueprint))


def _prettify(name: str) -> str:
    """Turn a raw dataframe column name into a human axis label."""
    overrides = {
        "sla_breaches": "SLA Breaches",
        "avg_cycle_time": "Avg Cycle Time (days)",
        "manual_hours": "Manual Hours",
        "bottleneck_score": "Bottleneck Score",
        "amount": "Cost ($)",
    }
    return overrides.get(name, name.replace("_", " ").title())


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.bar(df, x=x, y=y, title=title, color_discrete_sequence=COLOR_SEQUENCE)
    fig.update_xaxes(title=_prettify(x))
    fig.update_yaxes(title=_prettify(y))
    return style_chart(fig)


def sla_breach_rate_chart(df: pd.DataFrame):
    """SLA breach RATE by department (not raw count), with request volume in the
    hover so a high rate on a small queue is not misread as a big problem."""
    plot_df = df.assign(breach_pct=(df["breach_rate"] * 100).round(1))
    fig = px.bar(
        plot_df,
        x="breach_pct",
        y="department",
        orientation="h",
        title="SLA Breach Rate by Department",
        color_discrete_sequence=COLOR_SEQUENCE,
        custom_data=["volume"],
    )
    fig.update_traces(hovertemplate="%{y}: %{x:.1f}% breach rate<br>%{customdata[0]:,} requests<extra></extra>")
    fig.update_yaxes(categoryorder="total ascending", title="")
    fig.update_xaxes(title="SLA Breach Rate (%)")
    return style_chart(fig)


def automation_score_chart(view: pd.DataFrame):
    """Horizontal automation-score bars, colored by domain. This is the chart the
    README hero shows -- rendering it in-app keeps the screenshot and the live app
    in sync, and makes the cross-domain comparability visible at a glance."""
    chart_df = view.sort_values("Automation Score")
    fig = px.bar(
        chart_df,
        x="Automation Score",
        y="Automation Candidate",
        orientation="h",
        color="Domain",
        text="Automation Score",
        color_discrete_map={"OpsPilot": "#0f766e", "RescueOps": "#b7791f"},
        title="Automation Opportunity Score by Candidate",
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Automation Score (0-100)", range=[0, 105])
    # Force a single interleaved score ranking (not grouped by domain) so the
    # cross-domain comparability is what the eye actually sees.
    fig.update_yaxes(title="", categoryorder="array", categoryarray=chart_df["Automation Candidate"].tolist())
    fig = style_chart(fig)
    fig.update_layout(height=max(340, len(chart_df) * 30 + 90), legend_title_text="")
    return fig


def weekly_volume_trend(df: pd.DataFrame):
    """Weekly submitted-request volume -- a trend an operations director expects
    but the original dashboard never showed (it read as a static snapshot)."""
    weekly = (
        df.set_index("submitted_date")
        .resample("W")["request_id"]
        .count()
        .reset_index(name="requests")
    )
    fig = px.line(weekly, x="submitted_date", y="requests", title="Weekly Request Volume Trend", markers=True)
    fig.update_traces(line_color="#0f766e")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Requests")
    return style_chart(fig)


def horizontal_bar(df: pd.DataFrame, label: str, value: str, title: str):
    fig = px.bar(df, x=value, y=label, orientation="h", title=title, color_discrete_sequence=COLOR_SEQUENCE)
    fig.update_yaxes(categoryorder="total ascending", title=_prettify(label))
    fig.update_xaxes(title=_prettify(value))
    return style_chart(fig)


def style_chart(fig):
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=48, b=10),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        title=dict(font=dict(size=16, color="#172026")),
        font=dict(color="#172026"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e6e9ee", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def monthly_opspilot_volume(opspilot_df: pd.DataFrame) -> int:
    # Anchor the window to the dataset, not the wall clock, so defaults do not
    # decay as the committed synthetic data ages.
    cutoff = data_today(opspilot_df, "submitted_date").normalize() - pd.Timedelta(days=30)
    volume = int((opspilot_df["submitted_date"] >= cutoff).sum())
    return max(volume, int(len(opspilot_df) / 3), 1)


def monthly_inquiry_volume(inquiries: pd.DataFrame) -> int:
    cutoff = data_today(inquiries, "inquiry_date").normalize() - pd.Timedelta(days=30)
    volume = int((inquiries["inquiry_date"] >= cutoff).sum())
    return max(volume, int(len(inquiries) / 3), 1)


def recent_medical_costs(medical: pd.DataFrame) -> float:
    cutoff = data_today(medical, "expense_date").normalize() - pd.Timedelta(days=30)
    return float(medical.loc[medical["expense_date"] >= cutoff, "amount"].sum())


def default_opspilot_roi(opspilot_df: pd.DataFrame, summary: dict) -> dict:
    return calculate_opspilot_roi(
        average_staff_hourly_rate=45.0,
        manual_minutes_per_request=float(opspilot_df["estimated_manual_minutes"].mean()),
        monthly_request_volume=monthly_opspilot_volume(opspilot_df),
        percent_automated=35,
        time_saved_per_request_pct=blended_save_rate(opspilot_df) * 100,
    )


def default_rescueops_roi(dogs: pd.DataFrame, inquiries: pd.DataFrame, medical: pd.DataFrame) -> dict:
    return calculate_rescueops_roi(
        volunteer_hourly_value=28.0,
        monthly_inquiries=monthly_inquiry_volume(inquiries),
        minutes_per_manual_response=14.0,
        dogs_in_care=int((dogs["current_status"] != "Adopted").sum()),
        monthly_medical_expenses=recent_medical_costs(medical),
        expected_admin_reduction=35,
        expected_faster_response_rate=45,
    )


def opspilot_sensitivity(
    hourly_rate: float,
    manual_minutes: float,
    monthly_volume: int,
    percent_automated: int,
    build_cost: float,
    maintenance_cost: float,
) -> pd.DataFrame:
    """Three-scenario ROI sensitivity by flexing coverage and time-saved-per-request.

    Point estimates read as overconfident; a conservative/expected/optimistic band
    is the standard way to present a value case for a decision.
    """
    scenarios = [
        ("Conservative", max(5, percent_automated - 15), 40),
        ("Expected", percent_automated, 54),
        ("Optimistic", min(90, percent_automated + 15), 75),
    ]
    rows = []
    for name, coverage, time_saved in scenarios:
        roi = calculate_opspilot_roi(
            hourly_rate, manual_minutes, monthly_volume, coverage, time_saved, build_cost, maintenance_cost
        )
        payback = roi["payback_months"]
        rows.append(
            {
                "Scenario": name,
                "Coverage": f"{coverage}%",
                "Time Saved / Request": f"{time_saved}%",
                "Monthly Hours Saved": round(roi["monthly_hours_saved"], 1),
                "First-Year Net Savings": ui.money(roi["annual_net_savings"]),
                "Payback": f"{payback:.1f} mo" if payback != float("inf") else "n/a",
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
