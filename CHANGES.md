# Changes: Analytical Integrity and Delivery Pass

This revision took the OpsPilot Command Center MVP from "runs and looks complete"
to "survives a data-literate reviewer's scrutiny." Every analytic was audited;
anything that could not defend itself was removed or rebuilt, and the tool gained
the stakeholder artifacts (business demo script, integrity table, a runnable
automation) that prove it can move work from dashboard to action.

The refactor was organized into independent, separately testable workstreams --
analytics correctness, ROI model integrity, data reliability, and delivery
artifacts -- so each change could be reviewed and verified in isolation before
integration. A headless smoke test and a full 7-page application test gate every
step.

## Finding -> fix -> verification

1. Circular analytics (priority scores and automation labels were baked into the
   synthetic data and only re-displayed).
   Fix: new `modules/classification.py` derives OpsPilot automation candidacy from
   raw fields; `rescueops_analyzer.triage_adoption_inquiries` computes triage
   category/score from raw fields; the generator emits raw facts only.
   Verify: the regenerated CSVs contain no `automation_candidate_type`,
   `triage_category`, `priority_score`, or `recommended_action` columns.

2. Bottleneck headline could contradict its own table.
   Fix: `detect_bottlenecks` averages days-open over open rows only and ranks on
   measured delay contribution; the insight names the true top-delay stage.
   Verify: top bottleneck corrected from "Waiting on Requester" to "Approval"
   (42% of open-request delay, 94% breach rate); headline and table agree.

3. ROI metrics fabricated or circular (dollars added to a percentage; a slider
   input echoed back as a finding; saved hours double-counted).
   Fix: `calculate_rescueops_roi` drops the three bogus outputs; `calculate_opspilot_roi`
   gains a "time saved per automated request" input; only defensible labor math
   remains, with an Assumptions panel and a sensitivity table on the ROI page.
   Verify: `app.py` and `report_generator.py` no longer reference the removed keys;
   ROI page renders without error.

4. "Last 30 days" KPIs silently decayed to $0 as the committed data aged.
   Fix: recency windows anchor to `scoring.data_today(df, col)` (the dataset's own
   max date), never the wall clock.
   Verify: aging the data 300 days in-memory keeps Estimated Monthly Waste and
   Monthly Medical Costs greater than zero.

5. Automation score used relative min-max normalization (unstable, never reached
   100, double-counted volume, not comparable across domains).
   Fix: `scoring.absolute_automation_score` -- absolute anchor bands, additive
   weights summing to 1.0.
   Verify: scores in [0,100], reach 100 at max inputs, unchanged when another
   candidate is removed; the combined ranker is one descending sort across both
   domains (50.8 to 97.0).

6. One savings figure was a bare 0.42 multiplier; three different savings
   fractions lived in the app.
   Fix: `potential_monthly_savings = waste * ASSUMED_AUTOMATION_COVERAGE *
   blended_save_rate(df)` -- two named, commented constants.
   Verify: effective rate ~0.19 (coverage 0.35 x blended 0.54); savings dropped
   from ~$7,500 to ~$3,400 on the same $17,900 monthly waste.

7. Implementation blueprints were 8 of 14 sections of identical boilerplate.
   Fix: decision rules, workflow steps, exception handling, notifications, and
   triggers are candidate-specific for all 15 candidates, with idempotency and
   flow-failure language.
   Verify: distinct content on every field across all candidates.

8. Priority queue sorted alphabetically (Medium above Critical).
   Fix: sort by `scoring.PRIORITY_ORDER` severity rank.

9. HTML export dumped escaped markdown in a <pre> block.
   Fix: `markdown_to_html` renders real headings, lists, and paragraphs;
   `markdown_to_text` no longer strips every '#'.

10. Dashboard ended at insight.
    Fix: `automations/missing_document_followup.py` reads raw request fields,
    writes follow-up messages to an outbox, and appends to an audit log with an
    idempotency key.
    Verify: a second run writes 0 new files and 0 new audit rows.

11. Missing portfolio deliverables.
    Fix: executive-first README with an Analytical Integrity Review table and a
    per-file map; a 2-minute business demo script (`docs/DEMO_SCRIPT.md`); a real
    ranker chart from live data (`assets/ranker.png`); pinned dependencies;
    business-logic comments on the remaining constants.

12. Engineering hygiene.
    Fix: `use_container_width` replaced with `width="stretch"` (24 sites) ahead of
    the Streamlit removal date; dependency versions pinned; a shared
    `modules/scoring.py` removes three duplicated helpers; empty-input guards;
    an optional Anthropic path added alongside OpenAI for AI-enhanced mode.

## How to verify

    py tests/smoke.py          # headless pipeline: all analyzers/rankers/reports
    py tests/test_ranker.py    # scoring stability, ranges, ROI contract keys
    py -m modules.data_generator --force   # regenerate the synthetic datasets

All figures above are from the committed synthetic data (SEED=42) and are
illustrative for demonstration only.
