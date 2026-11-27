# Banking Transaction & Financial Analysis System

**Python Activity 3 · Group 4** · Interactive Streamlit dashboard for accounts, transfers, fraud flags, daily/monthly/yearly analytics & statements.

## Team (4 members)
- Rahul S R — JCJ26012995
- P Kavi Arasu — JCJ26012989
- Prachodna B — JCJ26012990
- Sarvesh MT — JCJ26013012

Source: `1st_Sem_PYTHON Programming _list_MCA_A`, Sheet1.

## What it does
- Customer accounts, deposits, withdrawals, fund transfers & balance checks with insufficient-balance handling.
- Transaction history (dict / list / deque / queue / stack / defaultdict) — all used live in the dashboard.
- Suspicious-transaction detection (large ≥ threshold · burst 3+/day · night hours) — transparent, auditable.
- Daily / monthly / yearly statistics with Pandas + NumPy (groupby, percentiles, means).
- Regex validation of account numbers (10–16 digits), PAN, TXN refs, phone, email.
- Optional live scraping of permitted pages (RBI / data.gov.in) with regex %/₹ parsing; seeded fallback so the demo always runs offline.
- Save & export to **CSV, JSON, text and binary (pickle)** + downloadable account statements.
- **Extra 1:** Monthly money insights (income/spend/net, savings rate) + savings-goal projection.
- **Extra 2:** One-click text statement export per customer.

## Requirement mapping (Activity 3, Group 4)
| Requirement | Where |
|---|---|
| Data structures (dict, list, deque, queue, stack, defaultdict, set via counterparties) | `src/data_structures.py` — used live in `app.py` |
| NumPy + Pandas | `src/analysis.py` (groupby, rolling stats, quantiles) |
| Regex | `src/validation.py` (account/PAN/TXN/phone/email) + `src/scraper.py` (₹/% extraction) |
| Web scraping (permitted sites) | `src/scraper.py` → RBI / data.gov.in with fallback |
| CSV / JSON / text / binary storage | `src/storage.py` — `data/` files |
| Reporting | Statements (`export_statement`), fraud table, insights, in-app charts |
| Extra features | `src/insights.py` (monthly insights + goal) · statement export in `app.py` |

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
