"""Banking Transaction & Financial Analysis System - Group 4 (Python Activity 3).

Premium fintech dashboard (Streamlit). Covers: data structures, NumPy/Pandas,
regex, web scraping (with fallback), CSV/JSON/text/binary storage + statements.
Extras: monthly money insights + savings goal projection; one-click statement export.

Run:  streamlit run app.py
Design: clean-light fintech (Mercury-style calm), Inter, tabular numbers,
colour-means-state only, verdict row -> cash flow -> tables -> risk, progressive
disclosure. No emojis (Material text labels only) to avoid glyph boxes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src import analysis, storage
from src.data_structures import AccountStore, TransactionHistory, PendingQueue, UndoStack, group_by_account
from src.fraud import flag_suspicious, fraud_summary
from src.insights import monthly_insights, goal_projection
from src.scraper import SAMPLE_CUSTOMERS, generate_transactions, scrape_live
from src.validation import validate_account_no, validate_txn_ref, validate_pan, validate_phone, generate_txn_ref

st.set_page_config(
    page_title="Banking Transaction & Financial Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- design system (CSS variables + Clean-light fintech) ----------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --navy:#0B1F3A; --navy-2:#132F57; --emerald:#0E7C5B; --slate:#475569;
  --muted:#64748B; --border:#E3E7EE; --bg:#F6F7F9; --card:#FFFFFF;
  --red:#B42318; --red-bg:#FEF2F2; --amber:#B54708; --amber-bg:#FFFAEB;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],.main,.block-container,section[data-testid="stMain"]{
  background:var(--bg) !important; color:var(--navy) !important;
  font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif !important;
}
.block-container{padding:1.25rem 2rem 3rem !important; max-width:1440px !important;}
h1,h2,h3,h4,p,span,div,label,button,input,select{font-family:'Inter',sans-serif !important;}
.num{font-variant-numeric:tabular-nums; font-feature-settings:"tnum" 1;}
/* hide Streamlit chrome */
header[data-testid="stHeader"],#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],.stDeployButton,div[data-testid="stStatusWidget"]{display:none !important;}
[data-testid="stSidebar"]{background:#FFFFFF !important; border-right:1px solid var(--border) !important;}
[data-testid="stSidebar"] .block-container{padding:1.5rem 1.25rem !important;}
/* topbar */
.topbar{display:flex;align-items:center;gap:16px;background:var(--card);border:1px solid var(--border);
  border-radius:16px;padding:16px 20px;margin-bottom:18px;box-shadow:0 1px 3px rgba(11,31,58,.06);}
.logo-mark{width:44px;height:44px;border-radius:12px;background:var(--navy);color:#fff;
  display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;letter-spacing:.02em;flex:0 0 auto;}
.topbar h1{font-size:22px;font-weight:800;letter-spacing:-.02em;margin:0;line-height:1.15;color:var(--navy);}
.topbar p{margin:2px 0 0;color:var(--muted);font-size:13px;}
.badges{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:700;letter-spacing:.06em;
  text-transform:uppercase;padding:6px 10px;border-radius:999px;border:1px solid var(--border);background:#F8FAFC;color:var(--slate);}
.pill.live{color:var(--emerald);border-color:#A6D5C3;background:#ECFDF5;}
.pill.risk{color:var(--amber);border-color:#E8D9B5;background:var(--amber-bg);}
/* section headings */
.sec{margin:26px 0 12px;border-top:1px solid var(--border);padding-top:18px;}
.sec-eyebrow{font-size:11px;font-weight:800;letter-spacing:.1em;color:var(--emerald);text-transform:uppercase;}
.sec h2{font-size:20px;font-weight:800;letter-spacing:-.02em;margin:4px 0 0;color:var(--navy);}
.sec p{color:var(--muted);font-size:13px;margin:4px 0 0;}
/* KPI cards - verdict row */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 6px;}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px;
  box-shadow:0 1px 3px rgba(11,31,58,.05);}
.kpi.hero{border-color:var(--navy);background:var(--navy);color:#fff;}
.kpi-lbl{font-size:11px;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);}
.kpi.hero .kpi-lbl{color:#B9C6DD;}
.kpi-num{font-size:28px;font-weight:800;letter-spacing:-.03em;margin:6px 0 2px;color:var(--navy);
  font-variant-numeric:tabular-nums;}
.kpi.hero .kpi-num{font-size:34px;color:#fff;}
.kpi-sub{font-size:12.5px;color:var(--muted);}
.kpi.hero .kpi-sub{color:#D6DEEC;}
.kpi-num.neg{color:var(--red);}
.kpi-num.pos{color:var(--emerald);}
/* cards / containers */
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px;
  box-shadow:0 1px 3px rgba(11,31,58,.05);}
.chart-title{font-size:15px;font-weight:700;color:var(--navy);margin:0 0 2px;}
.chart-sub{font-size:12.5px;color:var(--muted);margin:0 0 10px;}
.callout{border-radius:12px;padding:12px 14px;font-size:13px;border:1px solid var(--border);background:#F8FAFC;color:var(--slate);}
.callout.warn{background:var(--amber-bg);border-color:#E8D9B5;color:#7A4A08;}
.callout.good{background:#ECFDF5;border-color:#A6D5C3;color:#0B5C43;}
.stButton>button{border-radius:10px;font-weight:700;transition:all .15s ease;}
[data-testid="stSidebar"] .stButton>button{width:100%;}
/* choice / inputs */
[data-testid="stWidgetLabel"] p{font-weight:600 !important;font-size:13px !important;}
/* dataframe */
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden;}
.caption{font-size:12.5px;color:var(--muted);}
.footer{margin-top:28px;border-top:1px solid var(--border);padding-top:14px;
  font-size:12px;color:var(--muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;}
@media (max-width: 900px){.kpi-row{grid-template-columns:repeat(2,1fr);} .topbar{flex-direction:column;align-items:flex-start;} .badges{margin-left:0;justify-content:flex-start;}}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ---------------- plotly theme helpers ----------------
FONT = "Inter"
NAVY = "#0B1F3A"
EMERALD = "#0E7C5B"
SLATE = "#64748B"
LIGHT_SLATE = "#94A3B8"
GRID = "#E8EDF3"
RED = "#B42318"
AMBER = "#B54708"

def style_fig(fig, title: str, subtitle: str = ""):
    # Card provides title (Streamlit HTML); Plotly title left empty to avoid duplication.
    fig.update_layout(
        font=dict(family=FONT, size=12, color=SLATE),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=8, r=12, t=16, b=48),
        legend=dict(font=dict(family=FONT, size=11), bgcolor="rgba(255,255,255,0)",
                    orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0),
        hoverlabel=dict(font_family=FONT),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(family=FONT, size=11))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(family=FONT, size=11))
    return fig

def chart_card(title: str, subtitle: str, fig, key: str):
    with st.container(border=True):
        st.markdown(f"<div class='chart-title'>{title}</div><div class='chart-sub'>{subtitle}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch", key=key)

# ---------------- session data ----------------
if "txns" not in st.session_state:
    st.session_state.txns = generate_transactions(seed=42, n=120)
    st.session_state.scrape_info = {"ok": False, "url": None, "pcts": [], "raw_chars": 0}

txns: list[dict] = st.session_state.txns

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

# ---------------- topbar ----------------
st.markdown(
    '<div class="topbar"><div class="logo-mark">BK</div><div>'
    '<h1>Banking Transaction &amp; Financial Analysis</h1>'
    '<p>Group 4 &middot; Python Activity 3 &middot; Accounts, transfers, fraud flags, daily / monthly / yearly analytics &amp; statements</p></div>'
    '<div class="badges"><span class="pill live">Live demo</span><span class="pill">Group 4</span>'
    '<span class="pill">Streamlit + Pandas + Plotly</span></div></div>',
    unsafe_allow_html=True,
)

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("### Controls", unsafe_allow_html=True)
    st.caption("Filters apply to KPIs and charts below. Risk threshold is adjustable.")
    customers = ["All"] + sorted(df["customer"].unique().tolist())
    sel_cust = st.selectbox("Customer", customers)
    types = ["All"] + sorted(df["type"].unique().tolist())
    sel_type = st.selectbox("Transaction type", types)
    threshold = st.slider("Suspicious threshold (Rs)", 10000, 150000, 50000, 5000)

    st.divider()
    st.markdown("#### Web scraping", unsafe_allow_html=True)
    if st.button("Try live scrape (RBI / data.gov.in)"):
        st.session_state.scrape_info = scrape_live(timeout=6)
        st.toast("Scrape attempt finished")
    info = st.session_state.scrape_info
    if info.get("url"):
        st.caption(f"Source: {info['url']} &middot; {info.get('raw_chars',0)} chars &middot; % found: {len(info.get('pcts',[]))}")
    else:
        st.caption("Live scrape is off by default. Seeded sample keeps the demo offline-safe. Parser extracts % / Rs figures with regex.")

    st.divider()
    st.markdown("#### Storage", unsafe_allow_html=True)
    if st.button("Save CSV / JSON / TXT / BIN"):
        paths = storage.save_all(df)
        storage.save_accounts(SAMPLE_CUSTOMERS)
        st.success("Saved to `data/`")
        for k, v in paths.items():
            st.caption(f"{k.upper()}: {v}")
    st.caption("Writes transactions.* and accounts.* to the data folder.")

# ---------------- filters ----------------
view = df.copy()
if sel_cust != "All":
    view = view[view["customer"] == sel_cust]
if sel_type != "All":
    view = view[view["type"] == sel_type]

flagged = flag_suspicious(df, large_threshold=float(threshold))
net_total = float(view["signed"].sum()) if len(view) else 0.0
vol_total = float(view["amount"].sum()) if len(view) else 0.0
flagged_count = len(flagged)
flagged_rate = (100 * flagged_count / len(df)) if len(df) else 0.0

# ---------------- 01 verdict row ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">01 &middot; Overview</div><h2>Is today normal?</h2>'
    '<p>Verdict row first. One glance answers the headline question; detail follows below.</p></div>',
    unsafe_allow_html=True,
)
net_cls = "neg" if net_total < 0 else "pos"
st.markdown(
    '<div class="kpi-row">'
    f'<div class="kpi hero"><div class="kpi-lbl">Net flow</div><div class="kpi-num num">Rs {net_total:,.0f}</div>'
    '<div class="kpi-sub">money in minus money out (filtered view)</div></div>'
    f'<div class="kpi"><div class="kpi-lbl">Transactions</div><div class="kpi-num num">{len(view)}</div>'
    f'<div class="kpi-sub">{len(view)} shown of {len(df)} total</div></div>'
    f'<div class="kpi"><div class="kpi-lbl">Total volume</div><div class="kpi-num num">Rs {vol_total:,.0f}</div>'
    '<div class="kpi-sub">gross amount moved</div></div>'
    f'<div class="kpi"><div class="kpi-lbl">Flagged for review</div><div class="kpi-num num">{flagged_count}</div>'
    f'<div class="kpi-sub">{flagged_rate:.2f}% of {len(df)} &middot; see Risk section</div></div>'
    '</div>',
    unsafe_allow_html=True,
)
if len(view) == 0:
    st.markdown('<div class="callout warn">No transactions match the current filters. Clear the customer / type filter to see data.</div>', unsafe_allow_html=True)

# ---------------- 02 cash flow ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">02 &middot; Cash flow</div><h2>How money moved over time</h2>'
    '<p>One question per chart. Line for flow over time, grouped bars for in vs out by month.</p></div>',
    unsafe_allow_html=True,
)

if len(daily):
    daily_sorted = daily.sort_values("day").tail(60)
    fig_daily = go.Figure()
    fig_daily.add_trace(go.Scatter(
        x=daily_sorted["day"], y=daily_sorted["net"], mode="lines+markers",
        line=dict(color=NAVY, width=2.2), marker=dict(color=NAVY, size=5),
        fill="tozeroy", fillcolor="rgba(11,31,58,0.08)", hovertemplate="%{x}<br>Net: Rs %{y:,.0f}<extra></extra>"))
    fig_daily.add_hline(y=0, line_color=GRID, line_width=1)
    style_fig(fig_daily, "Daily net flow", "Cash in vs out per day, last 60 days (Rs)")
    fig_daily.update_xaxes(title="", tickangle=0)
    fig_daily.update_yaxes(title="Net Rs")
else:
    fig_daily = None

if len(monthly):
    m = monthly.copy()
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(name="In", x=m["month"], y=m["total_in"], marker_color=EMERALD, hovertemplate="%{x}<br>In: Rs %{y:,.0f}<extra></extra>"))
    fig_monthly.add_trace(go.Bar(name="Out", x=m["month"], y=m["total_out"], marker_color=NAVY, hovertemplate="%{x}<br>Out: Rs %{y:,.0f}<extra></extra>"))
    fig_monthly.update_layout(barmode="group", bargap=0.3)
    style_fig(fig_monthly, "Monthly in vs out", "Income and spend per month (Rs)")
    fig_monthly.update_yaxes(title="Rs")
else:
    fig_monthly = None

c1, c2 = st.columns([3, 2], gap="large")
if fig_daily is not None:
    with c1:
        chart_card("Daily net flow", "Cash in vs out per day, last 60 days (Rs)", fig_daily, "daily_net")
if fig_monthly is not None:
    with c2:
        chart_card("Monthly in vs out", "Income and spend per month (Rs)", fig_monthly, "monthly_io")

# ---------------- 03 spending ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">03 &middot; Spending</div><h2>Where money goes</h2>'
    '<p>Sorted bars beat a pie for exact reading. Largest spend on top, values labeled with units.</p></div>',
    unsafe_allow_html=True,
)
spend_top = spend.head(7).copy() if len(spend) else spend
if len(spend_top):
    sp = spend_top.sort_values("spend")
    fig_spend = px.bar(
        sp, x="spend", y="counterparty", orientation="h",
        color="spend", color_continuous_scale=["#DCE6F2", NAVY],
        template="simple_white",
    )
    fig_spend.update_layout(showlegend=False, coloraxis_showscale=False)
    style_fig(fig_spend, "Spending by counterparty", "Outflows only, Rs")
    fig_spend.update_xaxes(title="Rs spend")
    fig_spend.update_yaxes(title="")
else:
    fig_spend = None

if len(view):
    mix = view["type"].value_counts().reset_index()
    mix.columns = ["type", "count"]
    mix = mix.sort_values("count")
    fig_mix = px.bar(
        mix, x="count", y="type", orientation="h",
        color="type",
        color_discrete_sequence=[NAVY, EMERALD, SLATE, LIGHT_SLATE],
        template="simple_white",
    )
    fig_mix.update_layout(showlegend=False)
    style_fig(fig_mix, "Transaction mix", "Count by type, filtered view (sorted)")
    fig_mix.update_xaxes(title="Count")
    fig_mix.update_yaxes(title="")
else:
    fig_mix = None

s1, s2 = st.columns([3, 2], gap="large")
if fig_spend is not None:
    with s1:
        chart_card("Spending by counterparty", "Outflows only, Rs", fig_spend, "spend")
if fig_mix is not None:
    with s2:
        chart_card("Transaction mix", "Count by type, filtered view (sorted)", fig_mix, "mix")

# ---------------- 04 tables ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">04 &middot; Detail</div><h2>Working tables</h2>'
    '<p>Dense, filterable detail. Record count above each table; numbers right-aligned where possible.</p></div>',
    unsafe_allow_html=True,
)
t1, t2 = st.columns([3, 2], gap="large")
with t1:
    st.markdown("#### Account summary (Pandas)", unsafe_allow_html=True)
    st.caption(f"{len(acct_summary)} accounts. Sorted by total volume.")
    st.dataframe(acct_summary, width="stretch", hide_index=True)
    st.markdown("#### Yearly summary", unsafe_allow_html=True)
    st.caption(f"{len(yearly)} years. Count and net flow.")
    st.dataframe(yearly, width="stretch", hide_index=True)
    st.markdown("#### Recent transactions (latest 15)", unsafe_allow_html=True)
    recent = view.sort_values("date", ascending=False).head(15) if len(view) else view
    st.caption(f"Showing {len(recent)} of {len(view)} in filtered view.")
    show_cols = [c for c in ["txn_ref", "customer", "type", "counterparty", "amount", "date", "channel"] if c in recent.columns]
    st.dataframe(recent[show_cols] if show_cols else recent, width="stretch", hide_index=True)
with t2:
    st.markdown("#### Accounts and branches", unsafe_allow_html=True)
    st.caption("Seeded customers. Balances update during the transfer demo below.")
    acct_df = pd.DataFrame(SAMPLE_CUSTOMERS)
    st.dataframe(acct_df, width="stretch", hide_index=True)
    st.markdown('<div class="callout">Colour means state only: green is money in, navy is neutral/out, red is risk. No decorative gradients.</div>', unsafe_allow_html=True)

# ---------------- 05 risk ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">05 &middot; Risk</div><h2>Suspicious transactions</h2>'
    '<p>Rules: large at or above threshold &middot; burst 3+ per account per day &middot; night hours (00:00-04:00). Flagged rows need manual review, not auto-block.</p></div>',
    unsafe_allow_html=True,
)
with st.container(border=True):
    if flagged.empty:
        st.markdown('<div class="callout good">Nothing flagged at this threshold &mdash; good. Lower the threshold in Controls to see more.</div>', unsafe_allow_html=True)
    else:
        st.caption(f"{len(flagged)} flagged of {len(df)} ({flagged_rate:.2f}%). Sorted newest first.")
        st.dataframe(flagged, width="stretch", hide_index=True)
    st.caption("Rules live in `src/fraud.py` - transparent and auditable.")

# ---------------- 06 transfer demo ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">06 &middot; Transfer demo</div><h2>Try a transfer</h2>'
    '<p>Live demo of balance checks and error handling. Invalid accounts and insufficient funds are rejected with clear messages.</p></div>',
    unsafe_allow_html=True,
)
with st.container(border=True):
    accounts = store.all_numbers()
    sim_cols = st.columns(4)
    with sim_cols[0]:
        from_no = st.selectbox("From account", accounts)
        amt = st.number_input("Amount (Rs)", min_value=1.0, value=2000.0, step=100.0)
    with sim_cols[1]:
        to_no = st.selectbox("To account", [a for a in accounts if a != from_no])
    with sim_cols[2]:
        st.caption("Action")
        do_transfer = st.button("Execute transfer", width="stretch")
    with sim_cols[3]:
        st.caption("Undo")
        if st.button("Undo last", width="stretch"):
            undone = stack.pop()
            if undone:
                st.info(f"Undid {undone['txn_ref']} (demo balance restore).")
            else:
                st.warning("Nothing to undo.")

    if do_transfer:
        src_acc = store.get(from_no)
        bal = float(src_acc["balance"]) if src_acc else 0.0
        if not validate_account_no(from_no) or not validate_account_no(to_no):
            st.error("Invalid account number - regex check failed (10-16 digits).")
        elif float(amt) <= 0:
            st.error("Amount must be positive.")
        elif bal < float(amt):
            st.error(f"Insufficient balance - available Rs {bal:,.2f}, requested Rs {float(amt):,.2f}. Transaction rejected.")
        else:
            src_acc["balance"] = round(bal - float(amt), 2)
            dst = store.get(to_no)
            if dst:
                dst["balance"] = round(float(dst["balance"]) + float(amt), 2)
            ref = generate_txn_ref(seed=f"{from_no}{to_no}{amt}{len(txns)}")
            new_txn = {
                "txn_ref": ref,
                "account_no": from_no,
                "customer": src_acc["name"],
                "type": "transfer_out",
                "counterparty": f"Transfer to {to_no[-4:]}",
                "amount": float(amt),
                "date": __import__("datetime").date.today().isoformat(),
                "channel": "NetBanking",
            }
            txns.append(new_txn)
            history.append(new_txn)
            stack.push(new_txn)
            queue.enqueue(new_txn)
            st.session_state.txns = txns
            st.success(f"Done. Ref {ref} &middot; New balance Rs {src_acc['balance']:,.2f}")

st.caption(f"Structures active: dict accounts ({len(accounts)}) &middot; list history ({history.total()} moves) &middot; queue ({len(queue.pending())} pending) &middot; stack undo &middot; defaultdict grouped ({len(grouped)} accounts).")

# ---------------- EXTRA 1 ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">Extra 1 &middot; Insights</div><h2>Monthly insights and savings goal</h2>'
    '<p>Income / spend / net, savings rate, and a monthly-compounding goal projection.</p></div>',
    unsafe_allow_html=True,
)
with st.container(border=True):
    st.markdown("#### Monthly insights", unsafe_allow_html=True)
    st.caption(f"{len(insights)} months. Savings rate is net as % of income.")
    st.dataframe(insights, width="stretch", hide_index=True)
    g1, g2, g3, g4 = st.columns([1, 1, 1, 2])
    with g1:
        cur_bal = st.number_input("Current balance Rs", min_value=0.0, value=31900.0, step=500.0)
    with g2:
        monthly_save = st.number_input("Save / month Rs", min_value=0.0, value=3000.0, step=500.0)
    with g3:
        n_months = st.number_input("Months", min_value=1, value=12, step=1)
    with g4:
        rate = st.number_input("Annual rate %", min_value=0.0, value=6.0, step=0.5)
    proj = goal_projection(float(cur_bal), float(monthly_save), int(n_months), float(rate))
    if proj:
        p_df = pd.DataFrame(proj)
        fig_goal = go.Figure()
        fig_goal.add_trace(go.Scatter(
            x=p_df["month"], y=p_df["balance"], mode="lines+markers",
            line=dict(color=EMERALD, width=2.4), marker=dict(color=EMERALD, size=5),
            fill="tozeroy", fillcolor="rgba(14,124,91,0.10)", hovertemplate="Month %{x}<br>Balance: Rs %{y:,.0f}<extra></extra>"))
        style_fig(fig_goal, "Goal projection", f"Rs {float(monthly_save):,.0f}/month at {float(rate)}% p.a.")
        fig_goal.update_yaxes(title="Balance Rs")
        st.plotly_chart(fig_goal, width="stretch", key="goal")
        st.caption(f"Projected end balance: Rs {p_df['balance'].iloc[-1]:,.2f} in {int(n_months)} months (monthly compounding, demo only).")

# ---------------- EXTRA 2 ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">Extra 2 &middot; Statement</div><h2>One-click account statement</h2>'
    '<p>Text statement with running balance. Download it directly from the dashboard.</p></div>',
    unsafe_allow_html=True,
)
with st.container(border=True):
    stmt_cust = st.selectbox("Statement for customer", sorted(df["customer"].unique().tolist()))
    stmt_txns = [t for t in txns if t["customer"] == stmt_cust] if txns else []
    acct_no = stmt_txns[0]["account_no"] if stmt_txns else "-"
    statement = storage.export_statement(acct_no, stmt_cust, stmt_txns)
    st.code(statement)
    st.download_button("Download statement (.txt)", statement, file_name=f"statement_{stmt_cust.replace(' ','_')}.txt", width="stretch")

# ---------------- validation ----------------
st.markdown(
    '<div class="sec"><div class="sec-eyebrow">Checks &middot; Detail</div><h2>Regex checks and scraping detail</h2></div>',
    unsafe_allow_html=True,
)
checks = [
    {"check": "Account no (10-16 digits)", "result": "rev", "pass": validate_account_no("2601299501")},
    {"check": "PAN format", "result": "BCCCC1234F", "pass": validate_pan("BCCCC1234F")},
    {"check": "TXN ref (TXN+8-14)", "result": generate_txn_ref(), "pass": validate_txn_ref(generate_txn_ref())},
    {"check": "Indian phone (6-9 start)", "result": "9019709994", "pass": validate_phone("9019709994")},
]
st.dataframe(pd.DataFrame(checks), width="stretch", hide_index=True)
st.json(st.session_state.scrape_info)

st.markdown(
    '<div class="footer"><span>Group 4 &middot; Rahul S R, P Kavi Arasu, Prachodna B, Sarvesh MT &middot; Python Activity 3</span>'
    '<span>Streamlit dashboard &middot; Demo data is seeded</span></div>',
    unsafe_allow_html=True,
)
