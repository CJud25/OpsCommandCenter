# Calibration Plan: What Real Data the ROI Numbers Need

Every dollar, hour, and percentage this app displays is **illustrative and driven
by synthetic data**. The ROI and mission-impact models are deliberately simple and
honest (labor savings net of a build/maintenance cost), but they are only as good
as their inputs. Before any figure here is used to justify a real budget decision,
replace the synthetic defaults and baked-in planning assumptions below with
measured values from the specific operation.

This page is the checklist for that calibration. It lists the **exact fields the
models consume**, the assumption each currently uses, and the **real-world source
and historical baseline** that must replace it.

> Nothing on this page changes the code. It documents the gap between a portfolio
> demonstration and a defensible business case, so the two are never confused.

---

## 1. OpsPilot ROI inputs (`calculate_opspilot_roi`)

| Model input | Current value in the demo | Real-world source | Historical baseline required |
| --- | --- | --- | --- |
| Average staff hourly rate | Slider default `$45/hr` | Payroll / finance: **fully-loaded** cost by role (base pay + benefits + overhead), not just salary | Actual loaded rates for the roles that touch these requests, weighted by who does the work |
| Manual minutes per request | Mean of a **synthetic** `estimated_manual_minutes` column | A time study or the service-desk system's own timestamps | Measured handle time per request type (open→resolved minus wait/queue time), 6–12 months, by request type |
| Monthly request volume | Recent volume from **synthetic** tickets | Ticketing / ITSM system (e.g. Jira SM, ServiceNow, Zendesk) | 6–12 months of monthly counts, with seasonality, by request type |
| Percent automated (coverage) | Slider default `35%` | A pilot of the actual automation | Measured share of eligible requests the automation successfully handles end-to-end (not a guess) |
| Time saved per automated request | Defaults to the blended save rate (~`54%`) | Before/after time study on the automated path | Measured minutes removed per automated request vs. the manual baseline |
| One-time build cost | Slider default `$12,000` | Engineering estimate | Developer-hours × loaded rate + tooling/licensing + integration/testing effort |
| Monthly maintenance cost | Slider default `$400/mo` | Ops/engineering estimate | Ongoing monitoring, incident handling, change maintenance, and license renewals |

**Not dollarized (by design):** error-rate reduction, faster response, and morale.
If these are claimed as value, each needs its own measured before/after baseline.

---

## 2. RescueOps mission-impact inputs (`calculate_rescueops_roi`)

| Model input | Current value in the demo | Real-world source | Historical baseline required |
| --- | --- | --- | --- |
| Volunteer hourly value | Slider default `$28/hr` (**illustrative, not paid wages**) | A published volunteer-time value (e.g. Independent Sector) **or** the replacement-labor cost | The rate the organization is willing to defend, documented and dated |
| Monthly inquiries | **Synthetic** inquiry volume | Shared inbox / CRM / adoption platform | 6–12 months of adoption-inquiry counts, with seasonality |
| Minutes per manual response | Slider default `14 min` | Time study on real replies | Measured minutes to triage and respond to one inquiry |
| Dogs in care | **Synthetic** census (context only; not in the ROI math) | Intake/foster records | Current and trailing census |
| Monthly medical expenses | **Synthetic** figure (context only; not in the ROI math) | Actual vet invoices | Trailing 12 months of medical spend |
| Expected admin reduction | Slider default `35%` | A pilot, not an expectation | Measured admin-time reduction after the change |
| Expected faster response rate | Slider default `45%` | A pilot, not an expectation | Measured improvement in response time / answer rate |

---

## 3. Shared scoring assumptions (`modules/scoring.py`)

The automation **opportunity score** (0–100) and the home-page savings figure lean
on named planning assumptions, not measured values. Calibrate these too:

| Assumption | Current value | What to replace it with |
| --- | --- | --- |
| `OPSPILOT_SAVE_RATES` (per candidate) | `0.36`–`0.62`, sourced from blueprint specs | Measured before/after handle-time reduction for each automation |
| `ASSUMED_AUTOMATION_COVERAGE` | `0.35` | Measured coverage from a pilot, per candidate |
| `EFFORT_SCALE_HOURS` / `SLA_SCALE_BREACHES` | `60` / `40` (diminishing-returns knees) | Tune to how leadership actually weighs effort vs. impact in this operation |
| `EASE_BY_COMPLEXITY` | `Low 100 / Medium 55 / High 25` | Local estimate of build effort by complexity band |

---

## 4. Historical baselines to collect first

These underpin several inputs above; gather them once and reuse:

- **True ticket open/close timestamps** — to derive handle time and cycle time
  (not self-reported durations).
- **Historical resolution and first-response times** — by request/inquiry type.
- **Volume baselines** — 6–12 months per type, with seasonality, so a "monthly"
  figure is a real average and not a single busy month.
- **Labor rates by role** — fully loaded, from finance, weighted by who does the work.
- **SLA definitions and breach history** — the real thresholds and their breach
  counts, to replace synthetic `sla_breached` flags.
- **Automation build and maintenance cost inputs** — a real engineering estimate
  and a real run-cost, so payback and first-year ROI mean something.

---

## Definition of "calibrated"

A figure is calibrated when its inputs trace to **dated, sourced, real operational
records** (not sliders, not synthetic data, not planning assumptions), and a
skeptical reviewer can reproduce it from those records. Until then, treat every
number in this app as illustrative.
