# Banking Transaction & Financial Analysis System

**Python Activity 3 · Group 4**

A Streamlit application for a bank: open accounts, deposit, withdraw, transfer, check balances, monitor
suspicious activity, analyse transactions, and produce statements and reports.

## Team

| Name | USN |
|---|---|
| Rahul S R | JCJ26012995 |
| P Kavi Arasu | JCJ26012989 |
| Prachodna B | JCJ26012990 |
| Sarvesh M T | JCJ26013012 |

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
python -m pytest -q        # unit tests
```

The app opens with six demo customers and 18 months of generated transactions, replayed through the
same bank engine the app uses, so every balance is consistent.

## Screens

| Tab | What it does |
|---|---|
| Overview | Total deposits, this month's money in and out, items needing review, cash-flow chart, spending by category, recent activity |
| Banking | Deposit, withdraw, transfer, balance enquiry, undo, transfer queue, open a new account |
| Analytics | Daily, monthly and yearly statistics, NumPy summary numbers, weekday-by-hour heatmap, channel mix, monthly insights per customer |
| Risk monitor | Flagged transactions with reasons and a 0-100 risk score |
| Loan advisor | EMI, eligibility and repayment schedule; savings-goal projection |
| Statements & data | Account statement for any date range, financial report, save to CSV / JSON / text / binary, regex validation lab |
| Market rates | RBI policy rates and reference exchange rates scraped from rbi.org.in |

## How each requirement is met

| Requirement | Where |
|---|---|
| Customer profiles, accounts, transaction records | `src/bank.py` (`Bank.open_account`, ledger entries with reference, timestamp, channel, balance after) |
| Deposits, withdrawals, transfers, balance enquiry | `src/bank.py` · Banking tab |
| Data structures | `src/data_structures.py`: dict (accounts), list (ledger), deque (recent window, transfer queue), stack (undo), defaultdict, set |
| Validation of accounts, customers, references | `src/validation.py`: account no, PAN, mobile, email, name, IFSC, TXN reference, plus extraction from free text |
| Suspicious transactions | `src/fraud.py`: large debit, 4+ debits in a day, 00:00-04:00 activity, one debit taking 70%+ of balance |
| Daily / monthly / yearly statistics (Pandas + NumPy) | `src/analysis.py` |
| Public financial information from a permitted site | `src/scraper.py`: requests + BeautifulSoup + regex on rbi.org.in, with a saved snapshot for offline use |
| Insufficient balance, invalid input, unexpected errors | Custom exceptions in `src/bank.py` (`InsufficientBalance`, `InvalidInput`, `AccountNotFound`, `LimitExceeded`), `StorageError`; minimum balance and daily debit limit enforced |
| Statements and financial reports | `src/storage.py`: statement with opening/closing balance (TXT and CSV), financial report, CSV / JSON / text / pickle storage |

## Extra features

1. **Smart risk score** (`src/risk.py`). Each amount is compared with the same customer's own history using a
   NumPy z-score, then combined with time of day and channel into a 0-100 score (Low / Medium / High).
   Rs 60,000 is normal for one customer and alarming for another; a fixed threshold cannot tell the difference.
2. **Loan advisor** (`src/loan.py`). Reads each customer's actual salary credits, applies the 50% FOIR rule
   banks use, and prices the loan off the live RBI repo rate. Shows EMI, maximum eligible loan, a year-by-year
   principal/interest chart, and a downloadable amortisation schedule.

Also included: monthly savings insights per customer, savings-goal projection, transfer queue, undo.

## Project structure

```
app.py                  Streamlit interface
src/
  bank.py               Bank engine and custom exceptions
  data_structures.py    AccountStore, TransactionHistory, TransferQueue, UndoStack
  validation.py         Regular expressions
  analysis.py           Pandas / NumPy statistics
  fraud.py              Rule-based suspicious-transaction checks
  risk.py               Extra 1: statistical risk score
  loan.py               Extra 2: EMI and eligibility
  insights.py           Monthly insights and savings goal
  scraper.py            RBI rates scraper
  storage.py            Files, statements, reports
  sample_data.py        Demo customers and transaction history
tests/test_bank.py      Unit tests
data/                   Saved files and RBI snapshot
```

Demo data is generated for teaching purposes; names other than the team are fictional.
