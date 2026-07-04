# OpsPilot Command Center

OpsPilot turns raw operational data into a ranked, ROI-backed automation roadmap -- and then acts on it -- proven across two very different operations: a business service desk and a nonprofit dog rescue.

![Automation Ranker](assets/ranker.png)

## Analytical Integrity Review

Before shipping, every analytic in this app was put through an adversarial review. Anything that could not survive an executive's first skeptical question was removed or rebuilt. Here is what changed.

| Area | Before | After | Why it matters to a decision-maker |
| --- | --- | --- | --- |
| Bottleneck headline | Could name a stage as "primary bottleneck" that was not the largest source of delay -- the headline contradicted its own table | Stages ranked by measured delay contribution; headline and detail always agree | A wrong "fix this first" misdirects budget and headcount |
| ROI metrics | 3 of 4 headline metrics were fabricated or circular (one added dollars to a percentage, one echoed the user's own slider input back as a finding) | Only the defensible labor-savings model remains, with an explicit Assumptions panel and sensitivity analysis | An ROI number that survives the CFO's first question is worth ten that do not |
| Priority and automation scores | "Analysis" re-displayed labels hardcoded into the demo-data generator | Analyzer computes scores from raw fields -- the same code works on real data | Insight must be earned from the data, not smuggled in with it |
| KPI freshness | "Last 30 days" metrics silently decayed to $0 as the committed demo data aged | KPIs anchored to the dataset's own timeline; stable on any day it is opened | A dashboard that quietly reads zero destroys trust in everything else on it |
| Opportunity score | Relative min-max normalization: unstable, double-counted volume, not comparable across domains | Absolute anchor bands -- a score of 80 means the same thing in both operations | Rankings you can compare across business units are the whole point of ranking |
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
- `modules/roi_calculator.py`: the conservative labor-savings ROI and mission-impact models behind the ROI page.
- `modules/report_generator.py`: turns analyzer output into stakeholder-ready Markdown, text, and real HTML briefs, with an optional AI polish path.
- `modules/ui_components.py`: shared Streamlit UI helpers (headers, metric tiles, and layout) used across pages.
- `app.py`: the Streamlit entry point that wires the pages, demos, and downloads together.
- `automations/`: runnable micro-automations that turn dashboard insight into action -- starting with the missing-document follow-up writer.

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

- Streamlit executive dashboard for two domains
- Synthetic data generation on first run
- Measured bottleneck detection and cross-domain automation scoring from 0 to 100
- Candidate-specific automation blueprints
- Conservative ROI and mission-impact calculators with an Assumptions panel
- Rescue inquiry triage, foster matching, medical priority scoring, and a weekly founder brief
- Downloadable executive reports in Markdown, text, and real HTML
- Rule-based recommendation mode, plus an optional AI-enhanced polish path if an API key and SDK are available
- A runnable micro-automation that writes missing-document follow-ups and audit-logs each action

## Tech Stack

- Python
- Streamlit
- pandas
- numpy
- Plotly
- Local CSV storage
- Optional AI polish path: Anthropic (Claude) or OpenAI SDK, used only if a key and the SDK are present

### Privacy note

The default experience is fully local: no data leaves the machine. Enabling
"AI-Enhanced" mode sends the generated report text to Anthropic or OpenAI for
rewriting, so it should only be used with data you are comfortable transmitting to
a third-party API. A production deployment on real data would add encrypted storage
and access controls before writing any personal information to disk (for example the
follow-up messages the sample automation produces).

### Tested Versions

- Python 3.14
- Streamlit 1.58
- pandas 3.0
- numpy 2.5
- plotly 6.8

## How To Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app generates all required CSV files automatically in the `data/` folder on first run. To regenerate the synthetic data at any time, run:

```bash
py -m modules.data_generator --force
```

## Run the Micro-Automation

From the project root:

```bash
py automations/missing_document_followup.py
```

It scans `data/opspilot_requests.csv`, writes one follow-up message per missing-document request into `outbox/`, and appends an action row to `audit_log.csv`. Each action carries an idempotency key (request id plus rule name), so re-running it creates zero new files and zero new audit rows. Use `--help` for options.

## Folder Structure

```text
opspilot-command-center/
|-- app.py
|-- requirements.txt
|-- README.md
|-- docs/
|   `-- DEMO_SCRIPT.md
|-- .streamlit/
|   `-- config.toml
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
