"""Banking Transaction & Financial Analysis System — Group 4 (Python Activity 3).

Super-UI Streamlit dashboard. Covers: data structures, NumPy/Pandas, regex,
web scraping (with fallback), CSV/JSON/text/binary storage + statements.
Extras: monthly money insights + savings goal projection; one-click statement export.

Run:  streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src import analysis, storage
from src.data_structures import AccountStore, TransactionHistory, PendingQueue, UndoStack, group_by_account
from src.fraud import flag_suspicious, fraud_summary
from src.insights import monthly_insights, goal_projection
from src.scraper import SAMPLE_CUSTOMERS, generate_transactions, scrape_live
from src.validation import validate_account_no, validate_txn_ref, validate_pan, validate_phone, generate_txn_ref

st.set_page_config(page_title="Banking Transaction & Financial Analysis", page_icon="🏦", layout="wide")

st.markdown(
    """
    <style>
    html,body,[data-testid="stAppViewContainer"]{font-family:'Inter',system-ui,sans-serif;}
    .kpi-card{background:#fff;border:1px solid #e8ecef;border-radius:14px;padding:16px 18px;
      box-shadow:0 4px 16px rgba(16,24,40,.06);}
    .kpi-num{font-size:26px;font-weight:800;color:#0b3d91;}
    .kpi-lbl{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#6b7280;}
    .hero{background:linear-gradient(135deg,#0b3d91,#2f6feb);color:#fff;border-radius:18px;padding:28px 30px;}
    .hero h1{font-size:30px;margin:0;}
    .hero p{opacity:.95;margin:6px 0 0;}
    [data-testid="stSidebar"]{background:#f3f6fb;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>🏦 Banking Transaction &amp; Financial Analysis</h1>'
    "<p>Group 4 · Python Activity 3 · Accounts, transfers, fraud flags, daily/monthly/yearly analytics &amp; statements — with regex validation, scraping, and multi-format storage.</p></div>",
    unsafe_allow_html=True,
)
st.write("")

# ---- session data ----
if "txns" not in st.session_state:
    st.session_state.txns = generate_transactions(seed=42, n=120)
    st.session_state.scrape_info = {"ok": False, "url": None, "pcts": [], "raw_chars": 0}

txns: list[dict] = st.session_state.txns

# data structures in real use
store = AccountStore()
for c in SAMPLE_CUSTOMERS:
    store.add({"account_no": c["account_no"], "name": c["name"], "balance": c["balance"], "pan": c["pan"], "branch": c["branch"]})
history = TransactionHistory()
for t in txns:
    history.append(t)
queue = PendingQueue()
stack = UndoStack()
grouped = group_by_account(txns)

df = analysis.to_dataframe(txns)
daily = analysis.daily_stats(df)
monthly = analysis.monthly_stats(df)
yearly = analysis.yearly_stats(df)
acct_summary = analysis.account_summary(df)
spend = analysis.spending_by_counterparty(df)
insights = monthly_insights(df)
fraud = fraud_summary(df)

# ---- sidebar ----
with st.sidebar:
    st.header("Controls")
    customers = ["All"] + sorted(df["customer"].unique().tolist())
    sel_cust = st.selectbox("Customer", customers)
    types = ["All"] + sorted(df["type"].unique().tolist())
    sel_type = st.selectbox("Transaction type", types)
    threshold = st.slider("Suspicious threshold (₹)", 10000, 150000, 50000, 5000)

    st.divider()
    st.subheader("Web scraping")
    if st.button("🔄 Try live scrape (RBI / data.gov.in)", use_container_width=True):
        st.session_state.scrape_info = scrape_live(timeout=6)
        st.toast("Scrape attempt finished")
    info = st.session_state.scrape_info
    if info.get("url"):
        st.caption(f"Source: {info['url']} · {info.get('raw_chars',0)} chars · % found: {len(info.get('pcts',[]))}")
    else:
        st.caption("Live scrape off by default; seeded sample keeps the demo offline-safe. Parser uses regex over % / ₹ figures.")

    st.divider()
    st.subheader("Storage")
    if st.button("💾 Save CSV / JSON / TXT / BIN", use_container_width=True):
        paths = storage.save_all(df)
        storage.save_accounts(SAMPLE_CUSTOMERS)
        st.success("Saved to `data/`")
        for k, v in paths.items():
            st.caption(f"{k.upper()}: {v}")

# ---- filters ----
view = df.copy()
if sel_cust != "All":
    view = view[view["customer"] == sel_cust]
if sel_type != "All":
    view = view[view["type"] == sel_type]

flagged = flag_suspicious(df, large_threshold=float(threshold))
net_total = float(view["signed"].sum()) if len(view) else 0.0
vol_total = float(view["amount"].sum()) if len(view) else 0.0

# ---- KPIs ----
kpi_cols = st.columns(4)
for col, (lbl, num, sub) in zip(
    kpi_cols,
    [
        ("Transactions", f"{len(view)}", f"{len(view)} shown"),
        ("Net flow", f"₹{net_total:,.0f}", "in − out"),
        ("Total volume", f"₹{vol_total:,.0f}", "gross moved"),
        ("Flagged (fraud rules)", f"{fraud['flagged']}", f"{fraud['rate_pct']}% of {fraud['total']}"),
    ],
):
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-lbl">{lbl}</div>'
        f'<div class="kpi-num">{num}</div><div style="color:#6b7280">{sub}</div></div>',
        unsafe_allow_html=True,
    )
st.write("")

# ---- charts ----
c1, c2 = st.columns([3, 2])
with c1:
    st.subheader("Daily net flow (last 60 days)")
    fig = px.line(daily, x="day", y="net", title="Cash in vs out per day (₹)", markers=True)
    fig.update_layout(xaxis_title="", yaxis_title="Net ₹")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly income vs spend")
    fig2 = px.bar(monthly, x="month", y=["total_in", "total_out"], barmode="group", title="Monthly in / out (₹)")
    fig2.update_layout(xaxis_title="", yaxis_title="₹")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Yearly — count & net")
    st.dataframe(yearly, use_container_width=True, hide_index=True)

with c2:
    st.subheader("Spending by counterparty (outflows)")
    fig3 = px.bar(spend.head(8), x="counterparty", y="spend", color="spend", color_continuous_scale="Blues", title="Where money goes")
    fig3.update_layout(showlegend=False, xaxis_title="", yaxis_title="₹ spend")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Transaction mix")
    mix = view["type"].value_counts().reset_index()
    mix.columns = ["type", "count"]
    fig4 = px.pie(mix, values="count", names="type", title="Deposits / withdrawals / transfers")
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Account summary (Pandas)")
    st.dataframe(acct_summary, use_container_width=True, hide_index=True)

# ---- fraud ----
st.divider()
st.header("🚩 Suspicious transactions (rules: large ≥ threshold · burst 3+/day · night hours)")
if flagged.empty:
    st.success("Nothing flagged at this threshold — good.")
else:
    st.dataframe(flagged, use_container_width=True, hide_index=True)
    st.caption("Rules are in `src/fraud.py` — transparent and auditable. Flagged rows need manual review, not auto-block.")

# ---- transaction simulator (balance / error handling) ----
st.divider()
st.header("💳 Try a transfer (live demo — balance & error handling)")
accounts = store.all_numbers()
sim_cols = st.columns(4)
with sim_cols[0]:
    from_no = st.selectbox("From account", accounts)
    amt = st.number_input("Amount (₹)", min_value=1.0, value=2000.0, step=100.0)
with sim_cols[1]:
    to_no = st.selectbox("To account", [a for a in accounts if a != from_no])
with sim_cols[2]:
    st.write("")
    st.write("")
    do_transfer = st.button("Execute transfer", use_container_width=True)
with sim_cols[3]:
    st.write("")
    st.write("")
    if st.button("Undo last", use_container_width=True):
        undone = stack.pop()
        if undone:
            st.info(f"Undid {undone['txn_ref']} (demo balance restore).")
        else:
            st.warning("Nothing to undo.")

if do_transfer:
    src_acc = store.get(from_no)
    bal = float(src_acc["balance"]) if src_acc else 0.0
    if not validate_account_no(from_no) or not validate_account_no(to_no):
        st.error("Invalid account number — regex check failed (10–16 digits).")
    elif amt <= 0:
        st.error("Amount must be positive.")
    elif bal < amt:
        st.error(f"Insufficient balance — available ₹{bal:,.2f}, requested ₹{amt:,.2f}. Transaction rejected.")
    else:
        src_acc["balance"] = round(bal - amt, 2)
        dst = store.get(to_no)
        if dst:
            dst["balance"] = round(float(dst["balance"]) + amt, 2)
        ref = generate_txn_ref(seed=f"{from_no}{to_no}{amt}{len(txns)}")
        new_txn = {
            "txn_ref": ref,
            "account_no": from_no,
            "customer": src_acc["name"],
            "type": "transfer_out",
            "counterparty": f"Transfer → {to_no[-4:]}",
            "amount": float(amt),
            "date": __import__("datetime").date.today().isoformat(),
            "channel": "NetBanking",
        }
        txns.append(new_txn)
        history.append(new_txn)
        stack.push(new_txn)
        queue.enqueue(new_txn)
        st.session_state.txns = txns
        st.success(f"Done ✓ Ref {ref} · New balance ₹{src_acc['balance']:,.2f}")

st.caption(f"Structures active: dict accounts ({len(accounts)}) · list history ({history.total()} moves) · queue ({len(queue.pending())} pending) · stack undo · defaultdict grouped ({len(grouped)} accounts).")

# ---- EXTRA 1: insights + goal ----
st.divider()
st.header("📊 Extra feature 1 — Monthly insights & savings goal")
st.dataframe(insights, use_container_width=True, hide_index=True)
goal_cols = st.columns([1, 1, 1, 2])
with goal_cols[0]:
    cur_bal = st.number_input("Current balance ₹", min_value=0.0, value=31900.0, step=500.0)
with goal_cols[1]:
    monthly_save = st.number_input("Save / month ₹", min_value=0.0, value=3000.0, step=500.0)
with goal_cols[2]:
    n_months = st.number_input("Months", min_value=1, value=12, step=1)
with goal_cols[3]:
    rate = st.number_input("Annual rate %", min_value=0.0, value=6.0, step=0.5)
proj = goal_projection(float(cur_bal), float(monthly_save), int(n_months), float(rate))
if proj:
    p_df = pd.DataFrame(proj)
    fig5 = px.line(p_df, x="month", y="balance", markers=True, title=f"Goal projection — ₹{float(monthly_save):,.0f}/mo at {float(rate)}% p.a.")
    st.plotly_chart(fig5, use_container_width=True)
    st.caption(f"Projected end balance: ₹{p_df['balance'].iloc[-1]:,.2f} in {int(n_months)} months (monthly compounding, demo only).")

# ---- EXTRA 2: statement export ----
st.divider()
st.header("🧾 Extra feature 2 — One-click account statement")
stmt_cust = st.selectbox("Statement for customer", sorted(df["customer"].unique().tolist()))
stmt_txns = txns and [t for t in txns if t["customer"] == stmt_cust]
acct_no = stmt_txns[0]["account_no"] if stmt_txns else "—"
statement = storage.export_statement(acct_no, stmt_cust, stmt_txns)
st.code(statement)
st.download_button("Download statement (.txt)", statement, file_name=f"statement_{stmt_cust.replace(' ','_')}.txt")

# ---- validation + scrape detail ----
st.divider()
st.subheader("Regex checks & scraping detail")
checks = [
    {"check": "Account no (10–16 digits)", "result": "rev", "pass": validate_account_no("2601299501")},
    {"check": "PAN format", "result": "BCCCC1234F", "pass": validate_pan("BCCCC1234F")},
    {"check": "TXN ref (TXN+8–14)", "result": generate_txn_ref(), "pass": validate_txn_ref(generate_txn_ref())},
    {"check": "Indian phone (6–9 start)", "result": "9019709994", "pass": validate_phone("9019709994")},
]
st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)
st.json(st.session_state.scrape_info)

st.caption("Group 4 · Rahul S R, P Kavi Arasu, Prachodna B, Sarvesh MT · Python Activity 3 · Streamlit dashboard")
