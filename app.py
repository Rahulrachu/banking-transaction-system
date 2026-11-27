"""Banking Transaction & Financial Analysis System
Python Activity 3 · Group 4

Run with:  streamlit run app.py
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import analysis, storage
from src.bank import MIN_BALANCE, BankError
from src.fraud import flag_suspicious, fraud_summary
from src.insights import goal_projection, monthly_insights
from src.loan import SPREADS, amortization, eligibility, emi, monthly_income
from src.risk import add_risk_scores, risk_distribution
from src.sample_data import build_demo_bank
from src.scraper import fetch_rbi_rates, load_snapshot
from src.validation import (
    extract_refs, validate_account_no, validate_email, validate_pan,
    validate_phone, validate_txn_ref,
)

st.set_page_config(page_title="Group 4 Bank · Transaction & Financial Analysis", page_icon="🏦",
                   layout="wide", initial_sidebar_state="collapsed")

# ----------------------------------------------------------------- design
INK, MUTED, LINE, BG = "#0F172A", "#64748B", "#E2E8F0", "#F8FAFC"
BRAND, GREEN, RED, AMBER = "#1E3A8A", "#047857", "#B91C1C", "#B45309"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', system-ui, sans-serif; }}
.stApp {{ background: {BG}; }}
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none; }}
.block-container {{ padding: 1.6rem 2.2rem 3rem; max-width: 1280px; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}

.topbar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom: .4rem; }}
.brand {{ display:flex; gap:.75rem; align-items:center; }}
.logo {{ width:40px; height:40px; border-radius:10px; background:{BRAND}; color:#fff; font-weight:700;
        display:flex; align-items:center; justify-content:center; font-size:15px; }}
.brand h1 {{ font-size:1.25rem; margin:0; font-weight:700; }}
.brand p {{ margin:0; color:{MUTED}; font-size:.85rem; }}
.chip {{ display:inline-block; padding:.25rem .65rem; border-radius:999px; font-size:.75rem; font-weight:600;
        background:#fff; border:1px solid {LINE}; color:{MUTED}; margin-left:.35rem; }}
.chip.live {{ color:{GREEN}; border-color:#A7F3D0; background:#ECFDF5; }}

.kpi {{ background:#fff; border:1px solid {LINE}; border-radius:14px; padding:1rem 1.1rem; height:100%; }}
.kpi .label {{ font-size:.78rem; color:{MUTED}; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }}
.kpi .value {{ font-size:1.55rem; font-weight:700; color:{INK}; margin:.25rem 0 .1rem;
              font-variant-numeric: tabular-nums; white-space:nowrap; }}
.kpi .sub {{ font-size:.8rem; color:{MUTED}; }}
.kpi .up {{ color:{GREEN}; font-weight:600; }} .kpi .down {{ color:{RED}; font-weight:600; }}

.section-title {{ font-size:1.05rem; font-weight:700; color:{INK}; margin:.2rem 0 .1rem; }}
.section-sub {{ font-size:.85rem; color:{MUTED}; margin-bottom:.6rem; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{ background:#fff; border-radius:14px; border-color:{LINE}; }}
.stTabs [data-baseweb="tab-list"] {{ gap:.25rem; border-bottom:1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ height:2.6rem; padding:0 1rem; font-weight:600; color:{MUTED}; }}
.stTabs [aria-selected="true"] {{ color:{BRAND} !important; }}
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
    border-radius:10px; font-weight:600; border:1px solid {BRAND}; background:{BRAND}; color:#fff; }}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{
    background:#1E40AF; border-color:#1E40AF; color:#fff; }}
.stButton > button p, .stDownloadButton > button p, .stFormSubmitButton > button p {{ color:#fff; }}
.receipt {{ background:#F1F5F9; border-radius:12px; padding:.9rem 1rem; font-size:.9rem; line-height:1.6; }}
.receipt b {{ color:{INK}; }}
.pill {{ padding:.15rem .55rem; border-radius:999px; font-size:.75rem; font-weight:600; }}
.pill.High {{ background:#FEE2E2; color:{RED}; }} .pill.Medium {{ background:#FEF3C7; color:{AMBER}; }}
.pill.Low {{ background:#DCFCE7; color:{GREEN}; }}
.foot {{ color:{MUTED}; font-size:.8rem; text-align:center; margin-top:2rem; }}
</style>
""", unsafe_allow_html=True)


def rs(x: float, decimals: int = 0) -> str:
    """Indian-style rupee formatting: 12,34,567."""
    neg = x < 0
    x = abs(round(float(x), decimals))
    whole, _, frac = f"{x:.{decimals}f}".partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = ",".join([head[max(i - 2, 0):i] for i in range(len(head), 0, -2)][::-1])
        whole = f"{head},{tail}"
    return f"{'-' if neg else ''}₹{whole}{'.' + frac if frac else ''}"


def kpi(col, label: str, value: str, sub: str = "") -> None:
    col.markdown(f"<div class='kpi'><div class='label'>{label}</div><div class='value'>{value}</div>"
                 f"<div class='sub'>{sub}</div></div>", unsafe_allow_html=True)


def section(title: str, sub: str = "") -> None:
    st.markdown(f"<div class='section-title'>{title}</div>"
                + (f"<div class='section-sub'>{sub}</div>" if sub else ""), unsafe_allow_html=True)


def style(fig, height: int = 320):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=8, r=8, t=10, b=8),
                      font=dict(family="Inter, sans-serif", color=MUTED, size=12),
                      legend=dict(orientation="h", y=1.08, x=0, title=None), hoverlabel=dict(font_family="Inter"))
    fig.update_xaxes(showgrid=False, title=None)
    fig.update_yaxes(gridcolor="#F1F5F9", title=None, zeroline=False)
    return fig


MONEY = st.column_config.NumberColumn(format="₹ %.2f")

# ----------------------------------------------------------------- state
if "bank" not in st.session_state:
    st.session_state.bank = build_demo_bank()
    st.session_state.rates = load_snapshot()
bank = st.session_state.bank
rates = st.session_state.rates

txns = bank.history.all()
df = analysis.to_dataframe(txns)
accounts = bank.accounts.all()
acct_label = {a["account_no"]: f"{a['name']} · {a['account_no']}" for a in accounts}
acct_numbers = list(acct_label)

# ----------------------------------------------------------------- header
live = "live" if rates.get("live") else ""
st.markdown(f"""
<div class='topbar'>
  <div class='brand'><div class='logo'>G4</div>
    <div><h1>Banking Transaction &amp; Financial Analysis</h1>
    <p>Python Activity 3 · Group 4 · {len(accounts)} accounts · {len(txns):,} transactions</p></div></div>
  <div><span class='chip {live}'>RBI repo {rates['rates'].get('Policy Repo Rate', 0):.2f}%</span>
       <span class='chip'>{date.today():%d %b %Y}</span></div>
</div>""", unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Banking", "Analytics", "Risk monitor", "Loan advisor", "Statements & data", "Market rates"])

# ================================================================= OVERVIEW
with tabs[0]:
    month_now = pd.Timestamp.today().to_period("M").strftime("%Y-%m")
    month_prev = (pd.Timestamp.today().to_period("M") - 1).strftime("%Y-%m")
    monthly = analysis.monthly_stats(df)
    cur = monthly[monthly["month"] == month_now]
    prev = monthly[monthly["month"] == month_prev]
    flagged = flag_suspicious(df)
    fs = fraud_summary(flagged, len(df))

    spend_now = float(cur["money_out"].sum())
    spend_prev = float(prev["money_out"].sum()) or 1
    change = 100 * (spend_now - spend_prev) / spend_prev
    c = st.columns(4)
    kpi(c[0], "Total deposits", rs(bank.accounts.total_balance()), f"across {len(accounts)} accounts")
    kpi(c[1], "Money in this month", rs(cur["money_in"].sum()), f"{int(cur['transactions'].sum())} transactions")
    kpi(c[2], "Money out this month", rs(spend_now),
        f"<span class='{'down' if change > 0 else 'up'}'>{change:+.0f}%</span> vs last month")
    kpi(c[3], "Needs review", f"{fs['flagged']}", f"{fs['high']} high risk · {fs['rate_pct']}% of all")

    st.write("")
    left, right = st.columns([1.7, 1])
    with left, st.container(border=True):
        section("Cash flow", "Monthly money in and out, all accounts")
        m = monthly.tail(12)
        fig = go.Figure()
        fig.add_bar(x=m["month"], y=m["money_in"], name="Money in", marker_color=BRAND)
        fig.add_bar(x=m["month"], y=m["money_out"], name="Money out", marker_color="#93C5FD")
        fig.add_scatter(x=m["month"], y=m["net"], name="Net", mode="lines+markers", line=dict(color=INK, width=2))
        fig.update_layout(barmode="group", bargap=0.3)
        st.plotly_chart(style(fig, 330), width="stretch")
    with right, st.container(border=True):
        section("Where money goes", "Spending by category, last 90 days")
        recent = df[df["timestamp"] >= pd.Timestamp.today() - pd.Timedelta(days=90)]
        cat = analysis.spending_by_category(recent).head(7)
        fig = px.bar(cat.sort_values("amount"), x="amount", y="category", orientation="h",
                     color_discrete_sequence=[BRAND], text=cat.sort_values("amount")["share_pct"].map(lambda v: f"{v}%"))
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(style(fig, 330), width="stretch")

    left, right = st.columns([1.7, 1])
    with left, st.container(border=True):
        section("Recent activity")
        rec = pd.DataFrame(bank.history.recent(8))
        if len(rec):
            rec["when"] = pd.to_datetime(rec["timestamp"]).dt.strftime("%d %b, %H:%M")
            rec["signed"] = rec.apply(lambda r: r["amount"] if r["type"] in ("deposit", "transfer_in") else -r["amount"], axis=1)
            st.dataframe(rec[["when", "customer", "counterparty", "channel", "signed"]], hide_index=True,
                         width="stretch",
                         column_config={"when": "Time", "customer": "Customer", "counterparty": "Description",
                                        "channel": "Channel", "signed": st.column_config.NumberColumn("Amount", format="₹ %.2f")})
    with right, st.container(border=True):
        section("Accounts")
        acc_df = pd.DataFrame(accounts)[["name", "branch", "balance"]].sort_values("balance", ascending=False)
        st.dataframe(acc_df, hide_index=True, width="stretch",
                     column_config={"name": "Customer", "branch": "Branch", "balance": st.column_config.NumberColumn("Balance", format="₹ %.2f")})

# ================================================================= BANKING
with tabs[1]:
    section("Banking desk", "Deposits, withdrawals, transfers and balance enquiry. Every action is validated and can be undone.")
    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))
    left, right = st.columns([1.35, 1])
    with left, st.container(border=True):
        op = st.segmented_control("Action", ["Deposit", "Withdraw", "Transfer", "Balance enquiry"],
                                  default="Deposit", label_visibility="collapsed")
        if op == "Balance enquiry":
            acc_no = st.selectbox("Account", acct_numbers, format_func=acct_label.get)
            a = bank.accounts.get(acc_no)
            last = bank.history.for_account(acc_no)[-1:] or [None]
            st.markdown(
                f"<div class='receipt'>Available balance<br><span style='font-size:1.8rem;font-weight:700;color:{INK}'>"
                f"{rs(a['balance'], 2)}</span><br>Withdrawable now: <b>{rs(max(a['balance'] - MIN_BALANCE, 0), 2)}</b> "
                f"(minimum balance {rs(MIN_BALANCE)})<br>Last activity: <b>{last[0]['timestamp'].replace('T', ' ')[:16] if last[0] else '-'}</b>"
                f"</div>", unsafe_allow_html=True)
        else:
            with st.form("txn", clear_on_submit=False, border=False):
                if op == "Transfer":
                    c1, c2 = st.columns(2)
                    src_no = c1.selectbox("From", acct_numbers, format_func=acct_label.get)
                    dst_no = c2.selectbox("To", acct_numbers, index=1, format_func=acct_label.get)
                else:
                    src_no = st.selectbox("Account", acct_numbers, format_func=acct_label.get)
                c1, c2 = st.columns(2)
                amount = c1.number_input("Amount (₹)", min_value=0.0, value=5000.0, step=500.0, format="%.2f")
                note = c2.text_input("Note (optional)", placeholder="e.g. Rent December")
                later = op == "Transfer" and st.checkbox("Add to transfer queue instead of sending now")
                go_btn = st.form_submit_button(f"Confirm {op.lower()}", width="stretch", type="primary")
            if go_btn:
                try:
                    if op == "Deposit":
                        t = bank.deposit(src_no, amount, note or "Cash deposit")
                    elif op == "Withdraw":
                        t = bank.withdraw(src_no, amount, note or "Cash withdrawal")
                    elif later:
                        bank.schedule_transfer(src_no, dst_no, amount, note)
                        t = None
                        st.session_state.flash = f"Queued. {len(bank.queue)} transfer(s) waiting in the queue."
                        st.rerun()
                    else:
                        t, _ = bank.transfer(src_no, dst_no, amount, note)
                    if t:
                        st.session_state.flash = (f"{op} successful · Ref {t['txn_ref']} · "
                                                  f"New balance {rs(t['balance_after'], 2)}")
                        st.rerun()
                except BankError as exc:
                    st.error(str(exc))
                except Exception as exc:  # anything unexpected is reported, never crashes the app
                    st.error(f"Unexpected error: {exc}")

    with right:
        with st.container(border=True):
            section("Undo", "Stack (last in, first out)")
            top = bank.undo_stack.peek()
            st.caption(f"{len(bank.undo_stack)} action(s) can be undone." if top else "Nothing to undo yet.")
            if st.button("Undo last action", width="stretch", disabled=top is None):
                try:
                    st.session_state.flash = bank.undo_last()
                    st.rerun()
                except BankError as exc:
                    st.warning(str(exc))
        with st.container(border=True):
            section("Transfer queue", "Queue (first in, first out)")
            q = bank.queue.items()
            if q:
                st.dataframe(pd.DataFrame(q), hide_index=True, width="stretch",
                             column_config={"amount": MONEY})
                if st.button("Process queue", width="stretch"):
                    lines = [f"{rs(i['amount'], 2)} {i['from'][-4:]} → {i['to'][-4:]}: {o}" for i, o in bank.process_queue()]
                    st.session_state.flash = "Queue processed. " + " | ".join(lines)
                    st.rerun()
            else:
                st.caption("No transfers waiting.")

    with st.container(border=True):
        section("Open a new account", "Name, phone, email and PAN are validated with regular expressions.")
        with st.form("open", clear_on_submit=True, border=False):
            c = st.columns(3)
            name = c[0].text_input("Full name", placeholder="Ananya Sharma")
            phone = c[1].text_input("Mobile", placeholder="9876543210")
            email = c[2].text_input("Email", placeholder="ananya@example.com")
            c = st.columns(3)
            pan = c[0].text_input("PAN", placeholder="ABCDE1234F")
            branch = c[1].selectbox("Branch", ["Jayanagar", "Koramangala", "Malleshwaram", "HSR Layout", "Whitefield"])
            opening = c[2].number_input("Opening deposit (₹)", min_value=0.0, value=5000.0, step=500.0)
            if st.form_submit_button("Open account", width="stretch"):
                try:
                    acc = bank.open_account(name, phone, email, pan, branch, opening)
                    st.session_state.flash = f"Account {acc['account_no']} opened for {acc['name']} with {rs(opening, 2)}."
                    st.rerun()
                except BankError as exc:
                    st.error(str(exc))

# ================================================================= ANALYTICS
with tabs[2]:
    period = st.segmented_control("Period", ["Daily", "Monthly", "Yearly"], default="Monthly", label_visibility="collapsed")
    c1, c2 = st.columns([1, 3])
    who = c1.selectbox("Customer", ["All customers"] + [a["name"] for a in accounts])
    view = df if who == "All customers" else df[df["customer"] == who]
    nums = analysis.summary_numbers(view)
    c = st.columns(4)
    kpi(c[0], "Transactions", f"{nums['count']:,}")
    kpi(c[1], "Average amount", rs(nums["mean"]), f"median {rs(nums['median'])}")
    kpi(c[2], "Std deviation", rs(nums["std"]), "spread of amounts (NumPy)")
    kpi(c[3], "95th percentile", rs(nums["p95"]), "95% of transactions are below this")
    st.write("")

    if period == "Daily":
        stats = analysis.daily_stats(view[view["timestamp"] >= pd.Timestamp.today() - pd.Timedelta(days=60)])
        key = "date"
    elif period == "Yearly":
        stats, key = analysis.yearly_stats(view), "year"
        stats["year"] = stats["year"].astype(str)
    else:
        stats, key = analysis.monthly_stats(view), "month"

    with st.container(border=True):
        section(f"{period} money in and out", "Last 60 days" if period == "Daily" else "")
        if period == "Daily":
            stats["net_7d"] = stats["net"].rolling(7, min_periods=1).mean()
            fig = go.Figure()
            fig.add_bar(x=stats[key], y=stats["net"], name="Net per day",
                        marker_color=[GREEN if v >= 0 else RED for v in stats["net"]], opacity=.55)
            fig.add_scatter(x=stats[key], y=stats["net_7d"], name="7-day average", line=dict(color=INK, width=2))
        else:
            fig = go.Figure()
            fig.add_bar(x=stats[key], y=stats["money_in"], name="Money in", marker_color=BRAND)
            fig.add_bar(x=stats[key], y=stats["money_out"], name="Money out", marker_color="#93C5FD")
            fig.update_layout(barmode="group", bargap=.3)
        st.plotly_chart(style(fig, 340), width="stretch")
        show = stats.drop(columns=[c for c in ["net_7d"] if c in stats]).copy()
        if key == "date":
            show["date"] = show["date"].dt.strftime("%d %b %Y")
        st.dataframe(show.sort_values(key, ascending=False), hide_index=True, width="stretch", height=260,
                     column_config={k: MONEY for k in ["money_in", "money_out", "net", "average", "largest"]}
                     | {"spend_change_pct": st.column_config.NumberColumn("Spend change", format="%.1f%%")})

    left, right = st.columns(2)
    with left, st.container(border=True):
        section("When people bank", "Transactions by weekday and hour")
        heat = analysis.hourly_heat(view)
        fig = px.imshow(heat, color_continuous_scale=["#F8FAFC", "#BFDBFE", BRAND], aspect="auto")
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(style(fig, 280), width="stretch")
    with right, st.container(border=True):
        section("Channels", "How transactions are made")
        ch = analysis.channel_mix(view)
        fig = px.bar(ch, x="channel", y="transactions", color_discrete_sequence=[BRAND])
        st.plotly_chart(style(fig, 280), width="stretch")

    if who != "All customers":
        with st.container(border=True):
            section(f"Monthly insights · {who}", "Savings rate = what was left from income that month")
            ins = monthly_insights(view)
            st.dataframe(ins.sort_values("month", ascending=False), hide_index=True, width="stretch",
                         column_config={"income": MONEY, "spend": MONEY, "net": MONEY,
                                        "savings_rate_pct": st.column_config.ProgressColumn("Savings rate", min_value=-100, max_value=100, format="%.0f%%"),
                                        "top_spend": "Biggest spend"})

# ================================================================= RISK
with tabs[3]:
    c1, c2 = st.columns([1, 2])
    threshold = c1.number_input("Large debit threshold (₹)", min_value=10_000, max_value=500_000, value=50_000, step=5_000)
    flagged = flag_suspicious(df, threshold)
    fs = fraud_summary(flagged, len(df))
    dist = risk_distribution(add_risk_scores(df))
    c = st.columns(4)
    kpi(c[0], "Flagged", f"{fs['flagged']}", f"{fs['rate_pct']}% of {len(df):,} transactions")
    kpi(c[1], "High risk", f"{fs['high']}", "score 70 or above")
    kpi(c[2], "Amount under review", rs(fs["total_amount"]))
    kpi(c[3], "Most flagged", max(fs["by_customer"], key=fs["by_customer"].get) if fs["by_customer"] else "-")
    st.write("")

    left, right = st.columns([2, 1])
    with left, st.container(border=True):
        section("Transactions to review", "Sorted by risk score. Rules explain why each one was flagged.")
        level = st.segmented_control("Show", ["All", "High", "Medium", "Low"], default="All", label_visibility="collapsed")
        show = flagged if level == "All" else flagged[flagged["risk_level"] == level]
        show = show.assign(when=show["timestamp"].dt.strftime("%d %b %Y, %H:%M"))
        st.dataframe(show[["when", "customer", "type", "amount", "risk_score", "risk_level", "reasons"]],
                     hide_index=True, width="stretch", height=420,
                     column_config={"when": "Time", "customer": "Customer", "type": "Type", "amount": MONEY,
                                    "risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%d"),
                                    "risk_level": "Level", "reasons": st.column_config.TextColumn("Why", width="large")})
    with right:
        with st.container(border=True):
            section("Risk mix", "All transactions")
            fig = px.pie(names=list(dist), values=list(dist.values()), hole=.62,
                         color=list(dist), color_discrete_map={"Low": "#86EFAC", "Medium": "#FCD34D", "High": "#F87171"})
            fig.update_traces(textinfo="label+percent", textposition="outside")
            fig.update_layout(showlegend=False)
            st.plotly_chart(style(fig, 260), width="stretch")
        with st.container(border=True):
            section("How it works")
            st.markdown(
                "- **Rules:** large debit, 4+ debits in a day, 00:00–04:00 activity, one debit taking 70%+ of balance\n"
                "- **Risk score:** NumPy z-score of each amount against that customer's own history, plus time and channel\n"
                "- Flagged items are for **manual review**, not automatic blocking")

# ================================================================= LOAN ADVISOR
with tabs[4]:
    section("Loan advisor", "Eligibility from the customer's real salary credits. Rate = live RBI repo rate + bank spread.")
    repo = rates["rates"].get("Policy Repo Rate", 5.5)
    left, right = st.columns([1, 1.5])
    with left, st.container(border=True):
        acc_no = st.selectbox("Customer", acct_numbers, format_func=acct_label.get, key="loan_acc")
        kind = st.selectbox("Loan type", list(SPREADS))
        rate = st.slider("Interest rate (% a year)", 4.0, 20.0, round(repo + SPREADS[kind], 2), 0.05,
                         help=f"Default = RBI repo {repo:.2f}% + {SPREADS[kind]:.2f}% spread")
        years = st.slider("Tenure (years)", 1, 30, 20 if kind == "Home loan" else 5)
        existing = st.number_input("Existing EMIs per month (₹)", min_value=0.0, value=0.0, step=1000.0)
        income = monthly_income(df, acc_no)
        elig = eligibility(income, existing, rate, years * 12)
        amount = st.number_input("Loan amount (₹)", min_value=10_000.0, step=50_000.0,
                                 value=float(min(max(elig["max_loan"], 100_000), 5_000_000)))
    with right:
        pay = emi(amount, rate, years * 12)
        ok = pay <= elig["emi_capacity"]
        c = st.columns(3)
        kpi(c[0], "Monthly EMI", rs(pay), f"for {years * 12} months")
        kpi(c[1], "You can borrow up to", rs(elig["max_loan"]), f"income {rs(income)}/month")
        kpi(c[2], "Verdict", "Eligible" if ok else "Too high",
            f"<span class='{'up' if ok else 'down'}'>EMI {'within' if ok else 'above'} 50% of income</span>")
        st.write("")
        with st.container(border=True):
            sched = amortization(amount, rate, years * 12)
            total_interest = sched["interest"].sum()
            section("Repayment", f"Total interest {rs(total_interest)} · total paid {rs(amount + total_interest)}")
            yearly = sched.assign(year=(sched["month"] - 1) // 12 + 1).groupby("year")[["interest", "principal"]].sum().reset_index()
            fig = go.Figure()
            fig.add_bar(x=yearly["year"], y=yearly["principal"], name="Principal", marker_color=BRAND)
            fig.add_bar(x=yearly["year"], y=yearly["interest"], name="Interest", marker_color="#93C5FD")
            fig.update_layout(barmode="stack", xaxis_title="Year")
            st.plotly_chart(style(fig, 300), width="stretch")
            st.download_button("Download repayment schedule (CSV)", sched.to_csv(index=False),
                               file_name=f"emi_schedule_{acc_no}.csv", width="stretch")

    with st.container(border=True):
        section("Savings goal", "How a monthly saving grows with interest")
        c = st.columns(4)
        start = c[0].number_input("Starting amount (₹)", min_value=0.0, value=float(bank.balance(acc_no)), step=1000.0)
        monthly_save = c[1].number_input("Save every month (₹)", min_value=0.0, value=5000.0, step=500.0)
        months = c[2].number_input("Months", min_value=1, max_value=360, value=24)
        fd_rate = c[3].number_input("Interest (% a year)", min_value=0.0, max_value=15.0, value=6.5, step=0.25)
        proj = goal_projection(start, monthly_save, int(months), fd_rate)
        fig = px.area(proj, x="month", y="balance", color_discrete_sequence=[BRAND])
        st.plotly_chart(style(fig, 240), width="stretch")
        st.caption(f"After {int(months)} months: **{rs(proj['balance'].iloc[-1])}**")

# ================================================================= STATEMENTS & DATA
with tabs[5]:
    left, right = st.columns([1.4, 1])
    with left, st.container(border=True):
        section("Account statement", "Opening balance, every transaction with running balance, closing balance")
        c = st.columns([2, 1, 1])
        acc_no = c[0].selectbox("Account", acct_numbers, format_func=acct_label.get, key="stmt_acc")
        start = c[1].date_input("From", date.today().replace(day=1))
        end = c[2].date_input("To", date.today())
        if start > end:
            st.error("'From' date must be before 'To' date.")
        else:
            acc = bank.accounts.get(acc_no)
            text = storage.statement_text(acc, bank.history.for_account(acc_no), start.isoformat(), end.isoformat())
            st.code(text, language=None)
            d1, d2 = st.columns(2)
            d1.download_button("Download statement (.txt)", text, file_name=f"statement_{acc_no}_{start}_{end}.txt",
                               width="stretch")
            d2.download_button("Download statement (.csv)",
                               storage.statement_csv(bank.history.for_account(acc_no), start.isoformat(), end.isoformat()),
                               file_name=f"statement_{acc_no}_{start}_{end}.csv", width="stretch")

    with right:
        with st.container(border=True):
            section("Financial report", "Yearly and monthly summary for management")
            report = storage.financial_report(analysis.monthly_stats(df), analysis.yearly_stats(df),
                                              analysis.summary_numbers(df), len(flag_suspicious(df)),
                                              bank.accounts.total_balance())
            st.download_button("Download financial report", report, file_name="financial_report.txt",
                               width="stretch")
        with st.container(border=True):
            section("Save data", "CSV, JSON, text and binary (pickle) files in the data folder")
            if st.button("Save all files", width="stretch"):
                try:
                    for fmt, path in storage.save_all(txns, accounts).items():
                        st.write(f"✓ {fmt} → `{path}`")
                except storage.StorageError as exc:
                    st.error(str(exc))
        with st.container(border=True):
            section("Validation lab", "Test the regular expressions")
            kind = st.selectbox("Check", ["Account number", "PAN", "Mobile", "Email", "Transaction ref", "Find refs in text"])
            value = st.text_input("Value", placeholder="Type here", key="val_in")
            if value:
                if kind == "Find refs in text":
                    st.json(extract_refs(value))
                else:
                    fn = {"Account number": validate_account_no, "PAN": validate_pan, "Mobile": validate_phone,
                          "Email": validate_email, "Transaction ref": validate_txn_ref}[kind]
                    (st.success if fn(value) else st.error)("Valid" if fn(value) else "Not valid")

# ================================================================= MARKET RATES
with tabs[6]:
    c1, c2 = st.columns([3, 1])
    with c1:
        section("RBI policy rates", f"Scraped from {rates['source']} · {'live' if rates.get('live') else 'saved snapshot'} · "
                                    f"{rates.get('fetched_at', '')}")
    if c2.button("Refresh from RBI", width="stretch"):
        with st.spinner("Fetching rbi.org.in ..."):
            st.session_state.rates = rates = fetch_rbi_rates()
        if rates.get("live"):
            st.success("Updated with live figures.")
        else:
            st.warning(f"Could not reach RBI, showing saved snapshot. ({rates.get('error', '')})")
    r = rates["rates"]
    cols = st.columns(4)
    for i, (k, v) in enumerate(r.items()):
        kpi(cols[i % 4], k, f"{v:.2f}%")
        if i % 4 == 3:
            cols = st.columns(4)
    st.write("")
    with st.container(border=True):
        section("Reference exchange rates", "Rupees per unit of foreign currency")
        fx = pd.DataFrame([{"Currency": k, "INR": v} for k, v in rates["fx"].items()])
        st.dataframe(fx, hide_index=True, width="stretch",
                     column_config={"INR": st.column_config.NumberColumn(format="₹ %.4f")})
        st.caption("Figures are extracted with regular expressions from the page text. Used by the Loan advisor.")

st.markdown("<div class='foot'>Group 4 · Rahul S R · P Kavi Arasu · Prachodna B · Sarvesh M T &nbsp;|&nbsp; "
            "Demo data is generated for teaching purposes</div>", unsafe_allow_html=True)
