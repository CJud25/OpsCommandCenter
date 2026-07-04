# OpsPilot Command Center

## Process Improvement & Automation Intelligence Platform

OpsPilot Command Center is a promotion-level portfolio MVP that demonstrates how messy operational data can be turned into bottleneck analysis, automation recommendations, ROI estimates, and executive-ready action plans.

The app includes two demo modes:

- **OpsPilot**: a general business operations process-improvement and automation command center.
- **RescueOps**: a nonprofit dog rescue operations and automation command center.

The goal is to show that the same process-improvement framework can work across multiple real-world domains.

## Executive Overview

OpsPilot analyzes operational activity, identifies bottlenecks, ranks automation opportunities, estimates ROI, and generates leadership-ready improvement recommendations.

The audience should quickly understand that the builder can:

- diagnose operational problems
- identify bottlenecks and risk
- prioritize automation opportunities
- estimate business or mission value
- communicate recommendations clearly to leadership
- design a scalable MVP without fake integrations

## Problem Statement

Many teams operate with fragmented intake forms, manual follow-up, delayed approvals, missing documentation, duplicate work, aging backlogs, and limited visibility. Nonprofit operations face the same pattern through a different lens: unanswered inquiries, foster gaps, medical funding needs, limited volunteer capacity, and founder coordination load.

OpsPilot Command Center demonstrates a practical way to turn that operational noise into a structured improvement roadmap.

## Demo Modes

### OpsPilot

The fictional company, **Summit Services Group**, is a mid-sized organization struggling with delayed internal requests, approval bottlenecks, missing documentation, duplicate work, and poor workload visibility.

The demo analyzes synthetic operational requests and surfaces:

- total and open requests
- cycle time
- SLA breach rate
- manual effort
- bottleneck stages
- top automation candidates
- ROI estimates
- automation blueprints

### RescueOps

The fictional nonprofit rescue, **Rosalie and Friends**, is an all-volunteer organization managing dogs, fosters, adoption inquiries, medical needs, volunteer tasks, and donation priorities.

The demo analyzes synthetic rescue operations data and surfaces:

- dogs in care
- foster gaps
- adoption-ready dogs
- urgent medical cases
- unanswered inquiries
- volunteer capacity
- medical funding needs
- foster match recommendations
- weekly founder brief

## Screenshots Placeholder

Recommended screenshots for a portfolio README:

- Home / Executive Overview
- OpsPilot executive dashboard
- OpsPilot bottleneck analysis
- Automation Opportunity Ranker
- Automation blueprint generator
- RescueOps executive dashboard
- RescueOps inquiry triage
- RescueOps founder brief
- ROI & Business Case page
- Executive Report Generator

## Features

- Streamlit executive dashboard
- Synthetic data generation on first run
- OpsPilot request analytics
- RescueOps dog, inquiry, volunteer, and medical analytics
- Bottleneck detection logic
- Automation opportunity scoring from 0 to 100
- Automation blueprint generator
- ROI and mission-impact calculators
- Rescue inquiry triage
- Foster matching recommendations
- Medical priority scoring
- Dog bio and social post generator using structured data
- Weekly founder brief
- Downloadable executive reports in Markdown, text, and HTML
- Rule-based recommendation mode
- Optional AI-enhanced polish path if an API key and SDK are available

## Business Value

This MVP answers the executive questions that matter:

1. What problem does this solve?
2. Where is operational waste showing up?
3. What should be automated first?
4. How much time or money could be saved?
5. What workflow would actually be built?
6. What controls are needed before production?
7. How does the same framework apply across industries?

## Tech Stack

- Python
- Streamlit
- pandas
- numpy
- Plotly
- Local CSV storage
- Optional OpenAI SDK support for report polish if installed separately

## How To Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app generates all required CSV files automatically in the `data/` folder on first run.

## Folder Structure

```text
opspilot-command-center/
|-- app.py
|-- requirements.txt
|-- README.md
|-- .streamlit/
|   `-- config.toml
|-- data/
|   |-- opspilot_requests.csv
|   |-- rescueops_dogs.csv
|   |-- rescueops_inquiries.csv
|   |-- rescueops_volunteers.csv
|   `-- rescueops_medical_costs.csv
|-- assets/
|   `-- screenshots_or_logo_placeholder.png
`-- modules/
    |-- data_generator.py
    |-- opspilot_analyzer.py
    |-- rescueops_analyzer.py
    |-- automation_ranker.py
    |-- roi_calculator.py
    |-- report_generator.py
    `-- ui_components.py
```

## Synthetic Data Explanation

All data is synthetic and generated locally. The generated records intentionally include realistic operational issues:

- delayed approvals
- missing documentation
- duplicate requests
- rework
- SLA breaches
- overloaded departments
- foster gaps
- unanswered rescue inquiries
- urgent medical cases
- unfunded medical expenses
- limited volunteer capacity

No real customer, employee, volunteer, donor, applicant, or animal rescue data is included.

## Portfolio Talking Points

- Built as a solo-developer-friendly MVP with modular architecture.
- Demonstrates process improvement and automation strategy, not only dashboarding.
- Uses explainable scoring so recommendations can be defended to leadership.
- Shows cross-domain thinking by applying the same framework to business operations and nonprofit rescue operations.
- Avoids fake integrations while clearly explaining production pathways.
- Includes responsible boundaries for rescue workflows and human review.

## Future Roadmap

- Authentication and role-based access
- SQLite or Postgres backend
- Microsoft 365, Gmail, shared inbox, CRM, or donation platform integrations
- Scheduled automations
- Human approval workflows
- Audit logs
- Secure file storage
- Cloud deployment
- Real API-driven AI summaries with governance controls

## Disclaimer

This project uses synthetic and mock data for portfolio demonstration purposes. ROI, savings, and mission-impact estimates are illustrative and should be validated with real operational data before business use.
