from __future__ import annotations


def calculate_opspilot_roi(
    average_staff_hourly_rate: float,
    manual_minutes_per_request: float,
    monthly_request_volume: int,
    percent_automated: float,
    time_saved_per_request_pct: float = 54.0,
    one_time_build_cost: float = 12000.0,
    monthly_maintenance_cost: float = 400.0,
) -> dict:
    """Conservative, labor-savings-only ROI with a real cost side.

    This model deliberately reports ONLY what it can defend from the inputs:
    labor hours removed, their dollar value, and the payback on an assumed build
    and maintenance cost. Two earlier "metrics" were removed because they did not
    survive scrutiny -- a cycle-time "improvement" that merely echoed the user's
    own reduction slider back as a finding, and an SLA-breach-reduction figure
    produced by an invented coefficient formula with no basis in the data.

    ``percent_automated`` (coverage: share of volume automated) and
    ``time_saved_per_request_pct`` (share of manual time removed per automated
    request) are distinct levers and are multiplied together. The default time
    saved matches the blended save rate used on the home page so the two views
    tell one consistent story.
    """
    automation_rate = percent_automated / 100
    time_saved_rate = time_saved_per_request_pct / 100
    monthly_hours_saved = (
        monthly_request_volume * manual_minutes_per_request * automation_rate / 60
    ) * time_saved_rate
    monthly_labor_savings = monthly_hours_saved * average_staff_hourly_rate
    annual_labor_savings = monthly_labor_savings * 12

    # Cost side: net of ongoing maintenance and the one-time build. A benefits
    # estimate without a cost line is not an ROI; this makes the page title honest.
    monthly_net_savings = monthly_labor_savings - monthly_maintenance_cost
    annual_net_savings = monthly_net_savings * 12 - one_time_build_cost
    if one_time_build_cost <= 0:
        # No build cost -> payback is immediate and percentage ROI is undefined.
        payback_months = 0.0
        first_year_roi_pct = None
    elif monthly_net_savings > 0:
        payback_months = one_time_build_cost / monthly_net_savings
        first_year_roi_pct = annual_net_savings / one_time_build_cost * 100
    else:
        # Maintenance exceeds savings -> the build never pays back at these inputs.
        payback_months = float("inf")
        first_year_roi_pct = annual_net_savings / one_time_build_cost * 100

    return {
        "monthly_hours_saved": monthly_hours_saved,
        "monthly_labor_savings": monthly_labor_savings,
        "annual_labor_savings": annual_labor_savings,
        "monthly_net_savings": monthly_net_savings,
        "annual_net_savings": annual_net_savings,
        "payback_months": payback_months,
        "first_year_roi_pct": first_year_roi_pct,
        "qualitative_business_value": (
            "Faster request handling and fewer manual touches, with a defensible labor-savings "
            "business case for automating repeatable operational work -- net of build and maintenance cost."
        ),
    }


def calculate_rescueops_roi(
    volunteer_hourly_value: float,
    monthly_inquiries: int,
    minutes_per_manual_response: float,
    dogs_in_care: int,
    monthly_medical_expenses: float,
    expected_admin_reduction: float,
    expected_faster_response_rate: float,
) -> dict:
    # Fix #6: signature is preserved (the ROI page passes these seven positional
    # args), but ``dogs_in_care`` and ``monthly_medical_expenses`` are no longer
    # used -- they only fed the removed "funding visibility" pseudo-metric, which
    # was a circular restatement of its own inputs rather than a real outcome.
    admin_reduction_rate = expected_admin_reduction / 100
    response_rate = expected_faster_response_rate / 100
    monthly_response_hours = monthly_inquiries * minutes_per_manual_response / 60
    volunteer_hours_saved = monthly_response_hours * admin_reduction_rate
    volunteer_value = volunteer_hours_saved * volunteer_hourly_value
    faster_inquiries = monthly_inquiries * response_rate

    return {
        "volunteer_hours_saved": volunteer_hours_saved,
        "monthly_volunteer_value": volunteer_value,
        "estimated_inquiries_handled_faster": faster_inquiries,
        "mission_impact_summary": (
            "The largest value is not only labor savings. Better triage and visibility help volunteers respond faster, "
            "prioritize urgent care, and keep more dogs moving safely through the rescue pipeline."
        ),
    }
