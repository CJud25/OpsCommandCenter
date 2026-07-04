from __future__ import annotations


def calculate_opspilot_roi(
    average_staff_hourly_rate: float,
    manual_minutes_per_request: float,
    monthly_request_volume: int,
    percent_automated: float,
    current_cycle_time: float,
    expected_cycle_time_reduction: float,
    time_saved_per_request_pct: float = 70.0,
) -> dict:
    automation_rate = percent_automated / 100
    cycle_reduction_rate = expected_cycle_time_reduction / 100
    # Fix #6: automating a request does not remove 100% of the manual minutes --
    # a human still spins up the automation, reviews exceptions, and handles the
    # residual judgment work. ``time_saved_per_request_pct`` is the share of the
    # manual time per request that actually disappears once the workflow is
    # automated (default 70%). Coverage (``percent_automated``) and per-request
    # time saved are distinct levers and are multiplied together.
    time_saved_rate = time_saved_per_request_pct / 100
    monthly_hours_saved = (
        monthly_request_volume * manual_minutes_per_request * automation_rate / 60
    ) * time_saved_rate
    monthly_labor_savings = monthly_hours_saved * average_staff_hourly_rate
    annual_labor_savings = monthly_labor_savings * 12
    improved_cycle_time = max(0, current_cycle_time * (1 - cycle_reduction_rate))
    breach_reduction_estimate = min(65, expected_cycle_time_reduction * 0.7 + percent_automated * 0.18)

    return {
        "monthly_hours_saved": monthly_hours_saved,
        "monthly_labor_savings": monthly_labor_savings,
        "annual_labor_savings": annual_labor_savings,
        "estimated_cycle_time_improvement": current_cycle_time - improved_cycle_time,
        "new_cycle_time_estimate": improved_cycle_time,
        "sla_breach_reduction_estimate": breach_reduction_estimate,
        "qualitative_business_value": (
            "Faster request handling, fewer manual touches, better SLA visibility, and a clearer business case "
            "for automating repeatable operational work."
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
