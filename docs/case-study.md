# OpsPilot Command Center — Case Study

## Problem

Small operations teams know something is slow, but rarely which fix pays back
first. Requests age, approvals stall, documents go missing, and work gets
duplicated — yet the case for automating any one step is usually a hunch, not a
number. The gap is not tooling; it is a defensible way to rank where to spend
limited build hours, plus proof that the tool acts rather than just reports.

OpsPilot Command Center closes that gap with one framework — find the
bottleneck, price the fix, rank the work, generate the brief, run a safe
micro-automation — and, to show it is not tuned to a single business, runs
unchanged across two very different operations: a business service desk and a
nonprofit dog rescue.

## Stakeholders

The primary audience is an operations owner or team lead who has to defend a
budget request to a finance-minded decision-maker. In the business demo
("Summit Services Group"), that is a service-desk manager answering to a CFO
who asks what the automation costs before asking what it saves. In the rescue
demo ("Life's Paw-pose"), it is an all-volunteer founder deciding whether scarce
volunteer hours go to admin or to animals. The design target throughout was a
skeptical reviewer: every headline number has to survive the first hard
question, or it does not ship.

## Data

All data is synthetic, generated locally on first run and seeded for
reproducibility (numpy's default RNG, a fixed seed, and a fixed anchor date),
so the demo reads the same on any day and involves no real people or animals.
The business dataset (`opspilot_requests.csv`) holds 720 request rows; the
rescue census (`rescueops_dogs.csv`) holds 96 dog rows, alongside inquiry,
volunteer, and medical-cost tables. The generator emits raw operational facts
only — no pre-baked scores or labels — so the analytics must be earned from the
data, not smuggled in with it.

## Method

One shared pipeline drives both domains. Analyzer modules detect the bottleneck
by measured delay contribution, so the headline stage and the detail table
always agree. A shared scoring layer places every automation candidate on a
single absolute 0–100 curve anchored on net monthly hours saved, through a
diminishing-returns function with no hard ceiling — so both domains sit on one
comparable scale and doubling the work moves the ranking. A conservative ROI
model then prices the labor savings net of a real
build and maintenance cost, producing a payback period and first-year ROI with
an assumptions panel and a sensitivity band. Analyzer output becomes a
deterministic brief (Markdown, text, and HTML), and a runnable micro-automation
detects missing-document requests, writes one follow-up per request to an
outbox, and audit-logs each action with an idempotency key (request id plus
rule name). The pipeline is fully local and rule-based: no external API calls,
no keys, no data egress.

## Validation

The suite runs 20 pytest tests and all 20 pass (`py -m pytest -q` reports
`20 passed`). This is a real change in testability: before this work, `pytest`
collected zero tests, because the existing checks were `def main()` scripts it
never discovered. Converting them preserved their semantics with room to spare
— 64 pytest assertions against 50 original check call sites (26 in the smoke
test, 24 in the ranker tests, 14 in the automation tests). Measured line
coverage of the analytics and automation code (`modules/` plus `automations/`)
is 75%, over 1006 statements with 256 missed — deliberately conservative: the
Streamlit UI entrypoint (`app.py`) is excluded, and the shared helpers in
`modules/ui_components.py` are counted at 0% rather than dropped. `ruff` reports
clean, and CI runs `ruff` plus the full pytest suite on Python 3.12 and 3.13;
the app boots headless and returns HTTP 200.

## Impact

### Measured (from this run)

- 20 pytest tests pass, up from zero previously collected.
- 64 pytest assertions preserve the 50 original check sites (26 smoke, 24
  ranker, 14 automation).
- 75% line coverage across `modules/` and `automations/` (1006 statements, 256
  missed), with `app.py` excluded and `ui_components.py` counted at 0%.
- `ruff` clean; CI green on Python 3.12 and 3.13; headless app boots HTTP 200.

### Illustrative (synthetic / demo)

All dollar, ROI, and hours figures in the app are illustrative, computed from
synthetic data. The ROI model is a conservative labor-savings estimate net of
build and maintenance cost, reporting payback and first-year ROI. During an
integrity pass, two earlier ROI headline metrics that were fabricated or
circular — one echoed a user slider back as a finding, one used invented
coefficients — were removed, and a test now asserts they stay gone. The 0–100
automation scores, ranked roadmap, and outbox follow-ups are likewise synthetic
demonstration outputs.

## Limitations

The numbers demonstrate the framework, not a real operation. Every ROI input —
loaded labor rates, manual minutes per request, monthly volume, coverage, build
and maintenance cost — comes from synthetic data or planning sliders;
`docs/calibration.md` lists the exact real-world fields and historical baselines
each would need before a figure could support a budget decision. Coverage
excludes the Streamlit UI layer, so the interactive pages are exercised by the
headless boot check rather than unit tests. The micro-automation writes to a
local outbox; it does not yet send anything.

## Next Build

Add real data connectors (Microsoft 365, service-desk/ITSM, shared inbox,
adoption and donation platforms) to replace the synthetic CSVs; add KPI alert
thresholds so aging, SLA breaches, and funding gaps trigger notifications
instead of waiting for someone to open the dashboard; and close the loop by
sending the follow-ups through an email or inbox integration, with encrypted
storage and access controls before any personal data is written to disk.
