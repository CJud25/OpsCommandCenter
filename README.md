# OpsPilot Command Center

### [Live demo](https://opscommandcenter.streamlit.app/) &nbsp;|&nbsp; built with Streamlit

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://opscommandcenter.streamlit.app/)
[![CI](https://github.com/CJud25/OpsCommandCenter/actions/workflows/ci.yml/badge.svg)](https://github.com/CJud25/OpsCommandCenter/actions/workflows/ci.yml)

OpsPilot turns raw operational data into a ranked, ROI-backed automation roadmap -- and then acts on it -- proven across two very different operations: a business service desk and a nonprofit dog rescue.

Runs fully locally with no external API calls: no data ever leaves the machine.

![Automation Ranker](assets/ranker.png)

## Analytical Integrity Review

Before shipping, every analytic in this app was put through an adversarial review. Anything that could not survive an executive's first skeptical question was removed or rebuilt. Here is what changed.

| Area | Before | After | Why it matters to a decision-maker |
| --- | --- | --- | --- |
| Bottleneck headline | Could name a stage as "primary bottleneck" that was not the largest source of delay -- the headline contradicted its own table | Stages ranked by measured delay contribution; headline and detail always agree | A wrong "fix this first" misdirects budget and headcount |
| ROI metrics | 4 headline metrics, 3 fabricated or circular: one echoed the user's own cycle-time slider back as a finding, one was an invented SLA-reduction formula with coefficients from nowhere | Those two are deleted; the labor-savings model stays and gains a real cost side -- build cost, maintenance, payback period, first-year ROI -- with an Assumptions panel and sensitivity band | A benefits number with no cost line is not an ROI; a figure that survives the CFO's first question is worth ten that do not |
| Priority and automation scores | "Analysis" re-displayed labels hardcoded into the demo-data generator | Analyzer computes scores from raw fields -- the same code works on real data | Insight must be earned from the data, not smuggled in with it |
| KPI freshness | "Last 30 days" metrics silently decayed to $0 as the committed demo data aged | KPIs anchored to the dataset's own timeline; stable on any day it is opened | A dashboard that quietly reads zero destroys trust in everything else on it |
| Opportunity score | Relative min-max normalization: unstable, double-counted volume, not comparable across domains. A later hard saturation ceiling then pinned most candidates to the same effort value -- so the "data-driven" ranking barely moved with the data | Absolute anchor bands on net hours saved, fed through a diminishing-returns curve (no hard ceiling) so both domains use one comparable scale and the score genuinely responds to volume -- a property test proves it | A score of 80 means the same thing in both operations, and doubling the work actually changes the ranking |
| Home vs ROI savings | The home-page savings figure and the ROI page used different effective save rates, so the two views disagreed | The ROI page defaults its time-saved lever to the same blended save rate the home page uses -- the two tell one story | "Why does your dashboard say one number and your ROI page another?" is a credibility-ender |
| Severity ordering | Alphabetical sort ranked "Medium" above "Critical" | Severity-ordered | In operations, an ordering error becomes a response-time error |
| Implementation blueprints | 8 of 14 sections were identical boilerplate across every candidate | Candidate-specific plans, including idempotency and failure handling | A plan a team could actually execute, not a template |
| Dashboard to action | Insight ended at the screen | A runnable micro-automation detects missing-document requests, writes follow-ups to an outbox, and audit-logs each action with an idempotency key | Proof the system executes, not just reports |

## What Each Module Does

- `modules/scoring.py`: shared scoring primitives -- absolute automation-score anchors, SLA impact, save rates, and the dataset-anchored recency helper so scores mean the same thing across both domains.
- `modules/classification.py`: rule-based OpsPilot candidate membership and impact aggregation from raw fields, with unique primary attribution so portfolio hours are counted once.
- `modules/data_generator.py`: generates the synthetic CSVs with realistic operational issues, emitting raw facts only (no pre-baked scores or labels).
- `modules/opspilot_analyzer.py`: OpsPilot request analytics -- summary KPIs, measured bottleneck detection by delay contribution, and chart data.
- `modules/rescueops_analyzer.py`: RescueOps analytics -- dogs, fosters, inquiries, medical priority scoring, foster matching, and the weekly founder brief.
- `modules/automation_ranker.py`: builds the cross-domain automation opportunity ranking using the absolute scoring anchors.
- `modules/roi_calculator.py`: the conservative labor-savings ROI (with a real cost/payback side) and mission-impact models behind the ROI page.
- `modules/report_generator.py`: turns analyzer output into stakeholder-ready Markdown, text, and real HTML briefs -- fully deterministic, no external calls.
- `modules/ui_components.py`: shared Streamlit UI helpers (headers, metric tiles, and layout) used across pages.
- `app.py`: the Streamlit entry point that wires the pages, demos, and downloads together.
- `automations/`: runnable micro-automations that turn dashboard insight into action -- starting with the missing-document follow-up writer.
- `tests/`: a headless pipeline smoke test, ranker/ROI property tests (including a score-stability and a volume-sensitivity proof), and micro-automation idempotency/safety tests -- run in CI on every push.

All data is synthetic and generated to be analytically honest -- scores and priorities are computed by the analyzer, never pre-baked into the data.

## What I Would Build Next

- Real data connectors (Microsoft 365, service desk, shared inbox, adoption/donation platforms) to replace the synthetic CSVs.
- Alert thresholds on the KPIs so aging, breaches, and funding gaps trigger notifications instead of waiting for someone to open the dashboard.
- Closing the micro-automation loop -- actually send the follow-ups (email/inbox integration), not just write them to an outbox.

## Demo Modes

The app includes two demo modes:

- OpsPilot: a general business operations process-improvement and automation command center. The fictional company, Summit Services Group, struggles with delayed internal requests, approval bottlenecks, missing documentation, duplicate work, and poor workload visibility.
- RescueOps: a nonprofit dog rescue operations and automation command center. The fictional rescue, Rosalie and Friends, is an all-volunteer organization managing dogs, fosters, adoption inquiries, medical needs, volunteer tasks, and donation priorities.

The goal is to show that the same process-improvement framework works across multiple real-world domains.

## Features

- Streamlit executive dashboard for two domains, with a KPI strip that leads with the four headline numbers
- Synthetic data generation on first run (seeded, reproducible)
- Measured bottleneck detection and cross-domain automation scoring on a 0-100 absolute scale, charted in-app
- Candidate-specific automation blueprints (idempotency and failure handling included)
- Conservative labor-savings ROI with a real cost side -- build cost, maintenance, payback period, and first-year ROI -- plus an Assumptions panel and a sensitivity band
- Rescue inquiry triage, foster matching, medical priority scoring, and a weekly founder brief
- Downloadable executive reports in Markdown, text, and real HTML, rendered on screen
- A runnable micro-automation that writes missing-document follow-ups and audit-logs each action, with `--dry-run` and a `--max-actions` circuit breaker
- Rule-based throughout -- no external API calls, no keys, no data egress
- Tests run in GitHub Actions CI on every push

## Tech Stack

- Python
- Streamlit
- pandas
- numpy
- Plotly
- Local CSV storage
- GitHub Actions (CI)

### Privacy note

The app is fully local and makes no network calls: no data leaves the machine, and
there are no API keys to configure. (An optional AI report-polish path was
prototyped earlier and deliberately removed from the shipped app, so the report
pipeline stays fully deterministic and auditable -- a report that could silently
alter its own numbers has no place in an integrity-first tool.) A production
deployment on real data would add encrypted storage and access controls before
writing any personal information to disk (for example the follow-up messages the
sample automation produces).

### Tested Versions

- Developed on Python 3.14 with Streamlit 1.58, pandas 3.0, numpy 2.5, plotly 6.8
- CI validates the pinned dependency ranges on Python 3.12 and 3.13 (which resolve pandas 2.3.x); the same test suite passes on all three

## How To Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app generates all required CSV files automatically in the `data/` folder on first run. To regenerate the synthetic data at any time, run:

```bash
py -m modules.data_generator --force
```

## Run the Tests

```bash
py tests/smoke.py          # headless end-to-end pipeline
py tests/test_ranker.py    # ranker + ROI property tests
py tests/test_automation.py  # micro-automation idempotency + safety
```

These are the same checks GitHub Actions runs on every push (see the CI badge above).

## Run the Micro-Automation

From the project root:

```bash
py automations/missing_document_followup.py
py automations/missing_document_followup.py --dry-run       # preview without writing
py automations/missing_document_followup.py --max-actions 5 # circuit breaker
```

It scans `data/opspilot_requests.csv`, writes one follow-up message per missing-document request into `outbox/`, and appends an action row to `audit_log.csv`. Each action carries an idempotency key (request id plus rule name), and the audit row is written immediately after each file, so re-running it creates zero new files and zero new audit rows even if a previous run was interrupted. `--window-days N` allows a request to be chased again once its last follow-up is older than N days (a reminder ladder). Use `--help` for all options.

## Folder Structure

```text
opspilot-command-center/
|-- app.py
|-- requirements.txt
|-- README.md
|-- CONTRACTS.md
|-- CHANGES.md
|-- LICENSE
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- .devcontainer/
|   `-- devcontainer.json
|-- .streamlit/
|   `-- config.toml
|-- docs/
|   `-- DEMO_SCRIPT.md
|-- data/
|   |-- opspilot_requests.csv
|   |-- rescueops_dogs.csv
|   |-- rescueops_inquiries.csv
|   |-- rescueops_volunteers.csv
|   `-- rescueops_medical_costs.csv
|-- assets/
|   `-- ranker.png
|-- automations/
|   `-- missing_document_followup.py
|-- tests/
|   |-- smoke.py
|   |-- test_ranker.py
|   `-- test_automation.py
`-- modules/
    |-- scoring.py
    |-- classification.py
    |-- data_generator.py
    |-- opspilot_analyzer.py
    |-- rescueops_analyzer.py
    |-- automation_ranker.py
    |-- roi_calculator.py
    |-- report_generator.py
    `-- ui_components.py
```

## Synthetic Data Explanation

All data is synthetic and generated locally. The generated records intentionally include realistic operational issues: delayed approvals, missing documentation, duplicate requests, rework, SLA breaches, overloaded departments, foster gaps, unanswered rescue inquiries, urgent medical cases, unfunded medical expenses, and limited volunteer capacity.

No real customer, employee, volunteer, donor, applicant, or animal rescue data is included.

## Disclaimer

This project uses synthetic and mock data for portfolio demonstration purposes. ROI, savings, and mission-impact estimates are illustrative and should be validated with real operational data before business use.

## License

Released under the MIT License. See [LICENSE](LICENSE). Copyright (c) 2026 Chris Judkins.
