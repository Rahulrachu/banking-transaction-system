# Banking Transaction & Financial Analysis System

**Python Activity 3 · Group 4** · A premium fintech dashboard for accounts, transfers, fraud flags, daily / monthly / yearly analytics & statements.

> Clean-light fintech design (Mercury-style calm), built with Streamlit + Plotly. Verdict row first, colour means state only, tabular numbers, no decorative gradients.

![Dashboard — overview](screenshots/banking_dashboard.png)

![Dashboard — spending and tables](screenshots/banking_dashboard_mid.png)

![Dashboard — statement and checks](screenshots/banking_dashboard_bottom.png)

## Team (4 members)

| Name | USN |
|---|---|
| Rahul S R | JCJ26012995 |
| P Kavi Arasu | JCJ26012989 |
| Prachodna B | JCJ26012990 |
| Sarvesh MT | JCJ26013012 |

Source: `1st_Sem_PYTHON Programming _list_MCA_A`, Sheet1.

## Features

- **Accounts & balances** — 6 seeded customers with opening balances, branches and PAN-format placeholders.
- **Transfers with error handling** — live transfer demo checks account format (regex), amount > 0 and sufficient balance. Insufficient funds are rejected with the exact available / requested amounts. Undo via stack.
- **Suspicious-transaction detection** — large at/above threshold · burst 3+ per account per day · night hours 00:00–04:00. Transparent, auditable rules; flagged rows need manual review, not auto-block.
- **Analytics** — daily net flow (60 days), monthly in vs out, yearly count/net, spending by counterparty, transaction mix — all with NumPy + Pandas (groupby, rolling stats, quantiles).
- **Regex validation** — account numbers (10–16 digits), PAN, TXN refs, Indian phone, email, amount. Plus a demo text-extractor.
- **Web scraping** — optional live scraping of permitted pages (RBI / data.gov.in) with regex %/Rs parsing. Seeded fallback so the demo always runs offline.
- **Multi-format storage** — CSV, JSON, text and binary (pickle) for transactions and accounts, plus downloadable account statements.
- **Extra 1 — Monthly insights & savings goal** — income / spend / net, savings rate, top spend per month, and a monthly-compounding goal projection chart.
- **Extra 2 — One-click statement export** — per-customer text statement with running balance, downloadable from the dashboard.

## Design choices (research-backed)

- **Layout:** verdict row → cash flow → spending → working tables → risk → actions. Three-tier hierarchy (summary, context, detail) with progressive disclosure — Stripe/Mercury pattern.
- **Typography:** Inter at 6 sizes, tabular figures for every number so columns scan vertically. Largest type carries the verdict (net flow).
- **Colour:** navy / emerald / slate only. Green = money in, red = risk, amber = review. No decorative gradients — colour means state.
- **Charts:** Plotly `simple_white` template with custom Inter theme, light grids, sentence titles with units, one chart = one message. Sorted horizontal bars instead of a pie (exact reading beats angle judgement).
- **Chrome:** Streamlit default header/footer/menu hidden via CSS; theming lives in `.streamlit/config.toml` + CSS variables. No emojis (avoid glyph tofu) — text pills carry status.

## Requirement mapping (Activity 3, Group 4)

| Requirement | Where |
|---|---|
| Data structures (dict, list, deque, queue, stack, defaultdict, set via counterparties) | `src/data_structures.py` — used live in `app.py` |
| NumPy + Pandas | `src/analysis.py` (groupby, rolling stats, quantiles) |
| Regex | `src/validation.py` (account/PAN/TXN/phone/email) + `src/scraper.py` (Rs/% extraction) |
| Web scraping (permitted sites) | `src/scraper.py` → RBI / data.gov.in with fallback |
| CSV / JSON / text / binary storage | `src/storage.py` — `data/` files |
| Reporting | Statements (`export_statement`), fraud table, insights, in-app charts |
| Extra features | `src/insights.py` (monthly insights + goal) · statement export in `app.py` |

## Project structure

```
.
|-- app.py                 # Streamlit dashboard (premium fintech UI)
|-- screenshot.py          # Playwright screenshot helper (waits for chart render)
|-- requirements.txt
|-- .streamlit/config.toml # Streamlit theme
|-- screenshots/           # Dashboard screenshots
|-- data/                  # Saved CSV / JSON / TXT / BIN exports
`-- src/
    |-- data_structures.py # dict / list / deque / queue / stack / defaultdict / set
    |-- analysis.py        # NumPy + Pandas analytics
    |-- validation.py      # Regex checks + TXN ref generator
    |-- fraud.py           # Suspicious-transaction rules
    |-- scraper.py         # Permitted-site scraping + seeded sample
    |-- storage.py         # CSV / JSON / TXT / BIN + statements
    `-- insights.py        # Extra: monthly insights + goal projection
```

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the printed local URL. No API keys needed.

## Data

`data/` holds saved exports (`transactions.*`, `accounts.*`). Demo customers & transactions are seeded, realistic values for the assignment demo — swap with real statements where needed.

## GitHub

This repo is the submission link for Python mam. Code + README are the deliverable; Classroom submission is done separately by the team.
