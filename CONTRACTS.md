# Internal interface contracts

Frozen interfaces the analytics, ranker, ROI, and report layers build against.
Values may change; the names and shapes below must not, because `app.py` and
`report_generator.py` index them by name.

## summarize_opspilot(df) -> dict

Keys (stable): `total_requests`, `open_requests`, `average_cycle_time`,
`sla_breach_rate`, `oldest_open_request`, `estimated_manual_hours`,
`estimated_monthly_waste`, `top_bottleneck_stage`, `top_automation_candidate`,
`potential_monthly_savings`. May add `reference_date`.

## summarize_rescueops(dogs, inquiries, volunteers, medical) -> dict

Keys (stable): `dogs_in_care`, `dogs_needing_foster`, `dogs_adoption_ready`,
`urgent_medical_cases`, `open_adoption_inquiries`, `unanswered_messages`,
`monthly_medical_costs`, `unfunded_medical_need`, `volunteer_capacity`,
`highest_priority_dog`. May add `reference_date`.

## roi dicts (roi_calculator.py) -- post-fix

`calculate_opspilot_roi(...)` keys: `monthly_hours_saved`, `monthly_labor_savings`,
`annual_labor_savings`, `monthly_net_savings`, `annual_net_savings`,
`payback_months`, `first_year_roi_pct`, `qualitative_business_value`.
REMOVED (undefensible under scrutiny): `estimated_cycle_time_improvement` and
`new_cycle_time_estimate` (a slider echoed back as a finding) and
`sla_breach_reduction_estimate` (an invented coefficient formula). Replaced with a
real cost side: build cost, maintenance, payback, and first-year ROI.

`calculate_rescueops_roi(...)` keys after Fix #6: `volunteer_hours_saved`,
`monthly_volunteer_value`, `estimated_inquiries_handled_faster`,
`mission_impact_summary`. REMOVED: `improved_response_capacity`,
`estimated_admin_burden_reduced`, `medical_funding_visibility_improvement`.

File ownership to keep workstreams disjoint: `roi_calculator.py` is owned by
Workstream B; `report_generator.py` (including the `_opspilot_roi_text` /
`_rescueops_roi_text` formatters) is owned by Workstream C. B does NOT edit
`report_generator.py`. C aligns the two formatters to the ROI keys above using this
contract -- no code moves across the B/C boundary.

## automations DataFrame (automation_ranker.py builders)

Display columns (stable, indexed by name in app.py and report_generator.py):
`Rank`, `Domain`, `Automation Candidate`, `Problem Solved`, `Volume`,
`Estimated Hours Saved`, `Complexity`, `Risk`, `Business/Mission Impact`,
`Automation Score`, `Recommended First Step`, `Recommended Implementation Tool`.

## classification.py (implemented in Phase 0)

- `candidate_membership(df) -> DataFrame` boolean matrix, one column per row-level
  OpsPilot candidate; multi-membership; rows may match 0.
- `aggregate_candidate_impact(df, membership=None) -> DataFrame` columns
  `automation_name, volume, manual_hours, sla_breaches`. Overlapping -- opportunity
  sizing only; do NOT sum manual_hours across candidates.
- `primary_candidate(df, membership=None) -> Series` unique attribution (highest
  save rate wins; else "Unclassified"). Safe to sum hours.
- `blended_save_rate(df, membership=None) -> float` manual-hours-weighted mean save
  rate over primary attribution.

Portfolio totals and `estimated_monthly_waste` / `potential_monthly_savings` use
`primary_candidate` / `blended_save_rate` (hours counted once). Per-candidate ranker
sizing uses `aggregate_candidate_impact` (overlap allowed).

## scoring.py (implemented in Phase 0)

- `PRIORITY_ORDER`, `_normalize`, `data_today(df, col)`.
- `OPSPILOT_SAVE_RATES`, `ASSUMED_AUTOMATION_COVERAGE`.
- `absolute_automation_score(net_hours_saved, impact_0_100, repeatability, rule_clarity, complexity) -> float`
  and `sla_impact_score(sla_breaches) -> float`. Both ranker builders feed the SAME
  shared, data-derived quantity -- net monthly hours saved (gross manual hours x save
  rate) -- through one diminishing-returns curve (no hard saturation), so the effort
  anchor is on one comparable scale across domains and scores respond to volume. The
  impact term is domain-specific by design (measured SLA-breach signal for OpsPilot,
  leadership mission weight for RescueOps).

## Data reliability

Recency windows anchor to `scoring.data_today(df, date_col)`, never `date.today()`.
The generator emits raw facts only -- no `triage_category`, `priority_score`,
`recommended_action`, or `automation_candidate_type` columns in the CSVs.
