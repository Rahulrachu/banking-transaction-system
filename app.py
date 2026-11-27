"""Banking Transaction & Financial Analysis System - Group 4 (Python Activity 3).

Apple-inspired premium dashboard (Streamlit). Covers: data structures,
NumPy/Pandas, regex, web scraping (with fallback), CSV/JSON/text/binary
storage + statements.
Extras: monthly money insights + savings goal projection; one-click
statement export.

Run:  streamlit run app.py
Design: Apple.com language - SF stack, huge tight headlines, generous
whitespace, two grays + one blue, pill actions, bento cards, restrained
fade-up reveals + hover lift. No emojis (no glyph tofu).
"""

from __future__ import annotations

import html
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

# ---------------- Apple design system ----------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{
  --ink:#1d1d1f; --gray:#86868b; --gray-2:#6e6e73; --bg:#f5f5f7;
  --card:#ffffff; --blue:#0071e3; --blue-2:#0066cc; --red:#d70015;
  --border:#e8e8ed; --radius:20px;
  --ease:cubic-bezier(0.22,1,0.36,1); --ease-btn:cubic-bezier(0.4,0,0.6,1);
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],.main,.block-container{
  background:var(--bg) !important; color:var(--ink) !important;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Inter","Helvetica Neue",Arial,sans-serif !important;
  -webkit-font-smoothing:antialiased;
}
.block-container{padding:0 2rem 4rem !important; max-width:1200px !important; margin:0 auto !important;}
h1,h2,h3,h4,p,span,div,label,button,input,select{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Inter","Helvetica Neue",Arial,sans-serif !important;}
.num,.kpi-num,td.num{font-variant-numeric:tabular-nums; font-feature-settings:"tnum" 1;}
header[data-testid="stHeader"],#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],.stDeployButton,div[data-testid="stStatusWidget"]{display:none !important;}
[data-testid="stSidebar"]{background:#ffffff !important; border-right:1px solid var(--border) !important;}
[data-testid="stSidebar"] .block-container{padding:2rem 1.5rem !important;}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span{color:var(--gray) !important;}
/* ---- hero (Apple product-hero) ---- */
.hero{text-align:center; padding:64px 16px 8px;}
.hero-eyebrow{font-size:13px; font-weight:600; letter-spacing:.02em; color:var(--blue);}
.hero h1{font-size:56px; font-weight:600; line-height:1.05; letter-spacing:-0.374px; color:var(--ink); margin:12px 0 12px;}
.hero-sub{font-size:21px; font-weight:400; line-height:1.38; letter-spacing:0.2px; color:var(--gray); max-width:720px; margin:0 auto;}
.hero-pills{display:flex; gap:8px; justify-content:center; flex-wrap:wrap; margin-top:22px;}
.pill{display:inline-flex; align-items:center; font-size:12px; font-weight:600; letter-spacing:.01em;
  padding:7px 14px; border-radius:980px; border:1px solid var(--border); background:#fff; color:var(--gray-2);}
.pill.blue{background:var(--blue); color:#fff; border-color:var(--blue);}
.pill.dark{background:var(--ink); color:#fff; border-color:var(--ink);}
/* ---- sections: one idea per scene ---- */
.sec{margin:64px 0 28px; text-align:left;}
.sec-eyebrow{font-size:13px; font-weight:600; color:var(--blue); letter-spacing:.02em;}
.sec h2{font-size:32px; font-weight:600; line-height:1.12; letter-spacing:-0.28px; margin:6px 0 0; color:var(--ink);}
.sec p{font-size:17px; font-weight:400; line-height:1.47; color:var(--gray); margin:8px 0 0; max-width:720px;}
/* ---- bento KPI tiles ---- */
.kpi-row{display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:8px 0 0;}
.kpi{background:var(--card); border:1px solid var(--border); border-radius:20px; padding:24px 22px;
  transition:transform .32s var(--ease), box-shadow .32s var(--ease);}
.kpi:hover{transform:translateY(-3px); box-shadow:0 16px 40px rgba(0,0,0,.08);}
.kpi.hero{background:var(--ink); color:#fff; border-color:var(--ink);}
.kpi-lbl{font-size:12px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--gray);}
.kpi.hero .kpi-lbl{color:#aeaeb2;}
.kpi-num{font-size:32px; font-weight:600; letter-spacing:-0.022em; margin:8px 0 4px; color:var(--ink);}
.kpi.hero .kpi-num{font-size:36px; color:#fff;}
.kpi-sub{font-size:13px; line-height:1.4; color:var(--gray);}
.kpi.hero .kpi-sub{color:#d2d2d7;}
.kpi-num.neg{color:var(--red);} .kpi-num.pos{color:#0071e3;}
/* ---- cards ---- */
.card{background:var(--card); border:1px solid var(--border); border-radius:20px; padding:26px;
  transition:transform .32s var(--ease), box-shadow .32s var(--ease);}
.card:hover{transform:translateY(-2px); box-shadow:0 16px 40px rgba(0,0,0,.07);}
.chart-title{font-size:17px; font-weight:600; letter-spacing:-0.01em; color:var(--ink); margin:0 0 2px;}
.chart-sub{font-size:13px; color:var(--gray); margin:0 0 12px;}
.callout{border-radius:16px; padding:16px 18px; font-size:14px; line-height:1.5; border:1px solid var(--border); background:#fff; color:var(--gray-2);}
.callout.good{background:#eef7ff; border-color:#d2e5ff; color:#003a72;}
.callout.warn{background:#fff4e6; border-color:#ffe1b8; color:#6b3b00;}
/* ---- buttons: Apple pills ---- */
.stButton>button,[data-testid="stDownloadButton"] button{
  border-radius:980px !important; border:1px solid var(--blue) !important; background:var(--blue) !important;
  color:#fff !important; font-weight:600 !important; font-size:15px !important; padding:.55rem 1.6rem !important;
  transition:transform .24s var(--ease-btn), background .24s var(--ease-btn) !important;}
.stButton>button:hover,[data-testid="stDownloadButton"] button:hover{background:var(--blue-2) !important; transform:scale(1.02);}
.stButton>button:active{transform:scale(0.96);}
[data-testid="stSidebar"] .stButton>button{width:100%;}
[data-testid="stWidgetLabel"] p{font-weight:600 !important; font-size:14px !important; color:var(--ink) !important;}
[data-testid="stWidgetLabel"] p::first-letter{color:var(--ink);}
/* inputs */
[data-testid="stTextInput"],[data-testid="stNumberInput"]{border-radius:980px !important;}
/* ---- custom Apple tables (no truncated edges) ---- */
.apple-table-wrap{background:#fff; border:1px solid var(--border); border-radius:16px; overflow:hidden; margin:8px 0 4px;}
table.apple-table{width:100%; border-collapse:collapse; font-size:14px; line-height:1.4;}
table.apple-table th{font-size:12px; font-weight:600; letter-spacing:.04em; text-transform:uppercase; color:var(--gray);
  text-align:left; padding:12px 16px; background:#fbfbfd; border-bottom:1px solid var(--border);}
table.apple-table td{padding:12px 16px; color:var(--ink); border-bottom:1px solid var(--border); vertical-align:top;}
table.apple-table tr:last-child td{border-bottom:none;}
table.apple-table tr{transition:background .24s var(--ease-btn);}
table.apple-table tbody tr:hover{background:#f5f5f7;}
table.apple-table td.num,table.apple-table th.num{text-align:right; font-variant-numeric:tabular-nums;}
.table-caption{font-size:13px; color:var(--gray); margin:0 0 8px;}
.table-title{font-size:17px; font-weight:600; color:var(--ink); margin:0 0 4px;}
/* ---- scrape status bento ---- */
.scrape-grid{display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:10px 0 4px;}
.scrape-tile{background:#fbfbfd; border:1px solid var(--border); border-radius:16px; padding:16px;}
.scrape-lbl{font-size:11px; font-weight:600; letter-spacing:.07em; text-transform:uppercase; color:var(--gray);}
.scrape-val{font-size:17px; font-weight:600; color:var(--ink); margin-top:4px; word-break:break-word;}
.scrape-val.small{font-size:13px; font-weight:500; color:var(--gray-2);}
/* ---- statement ---- */
.statement{background:#1d1d1f; color:#e8e8ed; border-radius:16px; padding:20px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:12.5px; line-height:1.6; white-space:pre-wrap; word-break:break-word; max-height:320px; overflow:auto;}
/* ---- reveal motion (Apple-restrained fade-up, pure CSS so it never hides content) ---- */
@keyframes fadeUp{from{opacity:0; transform:translateY(18px);} to{opacity:1; transform:none;}}
.reveal{animation:fadeUp .7s var(--ease) both;}
.reveal.d1{animation-delay:.08s;} .reveal.d2{animation-delay:.16s;} .reveal.d3{animation-delay:.24s;} .reveal.d4{animation-delay:.32s;}
@media (prefers-reduced-motion: reduce){.reveal{opacity:1; transform:none; animation:none;} *{transition:none !important; animation:none !important;}}
.footer{margin-top:72px; text-align:center; font-size:13px; line-height:1.5; color:var(--gray);}
.footer .rule{width:40px; height:1px; background:var(--border); margin:0 auto 16px;}
.caption{font-size:13px; color:var(--gray);}
@media (max-width: 900px){.kpi-row{grid-template-columns:repeat(2,1fr);} .scrape-grid{grid-template-columns:repeat(2,1fr);}
 .hero h1{font-size:40px;} .hero-sub{font-size:18px;}}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
# Count-up (Apple fade-up reveal is pure CSS animation above). Streamlit markdown keeps <script> in page.
# Numbers are rendered server-side; motion is pure CSS (Streamlit never runs markdown <script>).


# ---------------- plotly theme (Apple minimal) ----------------
FONT = "Inter"
INK = "#1d1d1f"
GRAY = "#86868b"
BLUE = "#0071e3"
GRID = "#e8e8ed"
RED = "#d70015"

def style_fig(fig, title: str = ""):
    fig.update_layout(
        font=dict(family=FONT, size=12, color=GRAY),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=8, r=12, t=20, b=48),
        legend=dict(font=dict(family=FONT, size=11), bgcolor="rgba(255,255,255,0)",
                    orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0),
        hoverlabel=dict(font_family=FONT),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(family=FONT, size=11))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(family=FONT, size=11))
    return fig

def chart_card(title: str, subtitle: str, fig, key: str):
    with st.container(border=True):
        st.markdown(
            f"<div class='reveal'><div class='chart-title'>{html.escape(title)}</div>"
            f"<div class='chart-sub'>{html.escape(subtitle)}</div></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, width="stretch", key=key)

def apple_table(df: pd.DataFrame, num_cols: list[str] | None = None) -> str:
    """Render a compact Apple-styled HTML table (no truncated edges)."""
    if df is None or len(df) == 0:
        return "<div class='callout'>No rows to show.</div>"
    num_cols = set(num_cols or [])
    cols = list(df.columns)
    head = "".join(
        f"<th class='{'num' if c in num_cols else ''}'>{html.escape(str(c))}</th>" for c in cols
    )
    rows = []
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if c in num_cols and isinstance(v, (int, float)):
                txt = f"{v:,.2f}" if isinstance(v, float) else f"{v:,}"
            else:
                txt = str(v)
            cells.append(f"<td class='{'num' if c in num_cols else ''}'>{html.escape(txt)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        "<div class='apple-table-wrap'><table class='apple-table'>"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )

def show_table(title: str, caption: str, df: pd.DataFrame, num_cols: list[str] | None = None):
    st.markdown(
        f"<div class='reveal'><div class='table-title'>{html.escape(title)}</div>"
        f"<div class='table-caption'>{html.escape(caption)}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(apple_table(df, num_cols), unsafe_allow_html=True)

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

# ---------------- hero (Apple product-hero) ----------------
st.markdown(
    '<div class="hero reveal">'
    '<div class="hero-eyebrow">Banking Transaction &amp; Financial Analysis</div>'
    '<h1>Your money,<br>in focus.</h1>'
    '<p class="hero-sub">A calm view of accounts, transfers and risk.<br>'
    'One question first &mdash; is today normal?</p>'
    '<div class="hero-pills">'
    '<span class="pill blue">Python Activity 3</span>'
    '<span class="pill dark">Group 4</span>'
    '<span class="pill">Streamlit + Pandas + Plotly</span>'
    '</div></div>',
    unsafe_allow_html=True,
)

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("Controls", unsafe_allow_html=True)
    st.caption("Filters apply to KPIs and charts below. Risk threshold is adjustable.")
    customers = ["All"] + sorted(df["customer"].unique().tolist())
    sel_cust = st.selectbox("Customer", customers)
    types = ["All"] + sorted(df["type"].unique().tolist())
    sel_type = st.selectbox("Transaction type", types)
    threshold = st.slider("Suspicious threshold (Rs)", 10000, 150000, 50000, 5000)

    st.divider()
    st.markdown("Web scraping", unsafe_allow_html=True)
    if st.button("Try live scrape (RBI / data.gov.in)"):
        st.session_state.scrape_info = scrape_live(timeout=6)
        st.toast("Scrape attempt finished")
    info = st.session_state.scrape_info
    if info.get("url"):
        st.caption(f"Source: {info['url']} · {info.get('raw_chars', 0)} chars · figures: {len(info.get('pcts', []))}")
    else:
        st.caption("Off by default. Seeded sample keeps the demo offline-safe. Parser extracts % / Rs figures with regex.")

    st.divider()
    st.markdown("Storage", unsafe_allow_html=True)
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

# ---------------- 01 verdict ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Overview</div><h2>Is today normal?</h2>'
    '<p>The verdict first. Detail follows, quietly.</p></div>',
    unsafe_allow_html=True,
)
net_cls = "neg" if net_total < 0 else "pos"
def rs(v):
    sign = "- " if v < 0 else ""
    return f"{sign}Rs {abs(int(round(v))):,}"
st.markdown(
    '<div class="kpi-row">'
    '<div class="kpi hero reveal d1"><div class="kpi-lbl">Net flow</div>'
    f"<div class='kpi-num num'>{rs(net_total)}</div>"
    '<div class="kpi-sub">Money in minus money out, in the filtered view.</div></div>'
    '<div class="kpi reveal d2"><div class="kpi-lbl">Transactions</div>'
    f"<div class='kpi-num num'>{len(view):,}</div>"
    f"<div class='kpi-sub'>{len(view)} shown of {len(df)} total.</div></div>"
    '<div class="kpi reveal d3"><div class="kpi-lbl">Total volume</div>'
    f"<div class='kpi-num num'>{rs(vol_total)}</div>"
    '<div class="kpi-sub">Gross amount moved.</div></div>'
    '<div class="kpi reveal d4"><div class="kpi-lbl">Flagged for review</div>'
    f"<div class='kpi-num num'>{flagged_count}</div>"
    f"<div class='kpi-sub'>{flagged_rate:.2f}% of {len(df)}. See Risk below.</div></div>"
    "</div>",
    unsafe_allow_html=True,
)
if len(view) == 0:
    st.markdown(
        '<div class="callout warn reveal">No transactions match the current filters. '
        "Clear the customer or type filter to see data.</div>",
        unsafe_allow_html=True,
    )

# ---------------- 02 cash flow ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Cash flow</div><h2>How money moved over time</h2>'
    "<p>One idea per screen. Weekly shape first, then the monthly split.</p></div>",
    unsafe_allow_html=True,
)

# FIX (v3): smooth the spiky daily line -> 7-day rolling mean, weekly ticks, no marker clutter.
if len(daily):
    daily_sorted = daily.sort_values("day").tail(60).copy()
    daily_sorted["smooth"] = daily_sorted["net"].rolling(window=7, center=True, min_periods=1).mean()
    fig_daily = go.Figure()
    fig_daily.add_trace(go.Scatter(
        x=daily_sorted["day"], y=daily_sorted["smooth"],
        mode="lines",
        line=dict(color=INK, width=2.5, shape="spline", smoothing=0.6),
        fill="tozeroy", fillcolor="rgba(0,113,227,0.08)",
        hovertemplate="%{x}<br>Net (7-day): Rs %{y:,.0f}<extra></extra>"))
    fig_daily.add_hline(y=0, line_color=GRID, line_width=1)
    style_fig(fig_daily)
    fig_daily.update_xaxes(tickmode="array", dtick="W-MON", tickformat="%b %d")
    fig_daily.update_yaxes(title="Net Rs")
else:
    fig_daily = None

if len(monthly):
    m = monthly.copy()
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(name="In", x=m["month"], y=m["total_in"], marker_color=BLUE,
                                   hovertemplate="%{x}<br>In: Rs %{y:,.0f}<extra></extra>"))
    fig_monthly.add_trace(go.Bar(name="Out", x=m["month"], y=m["total_out"], marker_color=INK,
                                   hovertemplate="%{x}<br>Out: Rs %{y:,.0f}<extra></extra>"))
    fig_monthly.update_layout(barmode="group", bargap=0.35)
    style_fig(fig_monthly)
    fig_monthly.update_yaxes(title="Rs")
else:
    fig_monthly = None

c1, c2 = st.columns([3, 2], gap="large")
if fig_daily is not None:
    with c1:
        chart_card("Money in, week by week", "7-day rolling net flow, last 60 days (Rs)", fig_daily, "daily_net_apple")
if fig_monthly is not None:
    with c2:
        chart_card("Monthly in vs out", "Income and spend per month (Rs)", fig_monthly, "monthly_io_apple")

# ---------------- 03 spending ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Spending</div><h2>Where money goes</h2>'
    "<p>Sorted bars. Largest spend on top.</p></div>",
    unsafe_allow_html=True,
)
spend_top = spend.head(7).copy() if len(spend) else spend
if len(spend_top):
    sp = spend_top.sort_values("spend")
    palette = [BLUE, INK, "#5aa9e6", "#86868b", "#aeaeb2", "#d2d2d7", "#e8e8ed"]
    fig_spend = px.bar(
        sp, x="spend", y="counterparty", orientation="h",
        color="counterparty", color_discrete_sequence=palette,
        template="simple_white",
    )
    fig_spend.update_layout(showlegend=False)
    style_fig(fig_spend)
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
        color="type", color_discrete_sequence=[INK, BLUE, GRAY, "#d2d2d7"],
        template="simple_white",
    )
    fig_mix.update_layout(showlegend=False)
    style_fig(fig_mix)
    fig_mix.update_xaxes(title="Count")
    fig_mix.update_yaxes(title="")
else:
    fig_mix = None

s1, s2 = st.columns([3, 2], gap="large")
if fig_spend is not None:
    with s1:
        chart_card("Spending by counterparty", "Outflows only, Rs", fig_spend, "spend_apple")
if fig_mix is not None:
    with s2:
        chart_card("Transaction mix", "Count by type, filtered view (sorted)", fig_mix, "mix_apple")

# ---------------- 04 detail tables ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Detail</div><h2>Working tables</h2>'
    "<p>Dense detail, kept quiet. Counts above every table.</p></div>",
    unsafe_allow_html=True,
)
t1, t2 = st.columns([3, 2], gap="large")
with t1:
    # FIX (v3): fewer columns so nothing truncates.
    acct_show = acct_summary.rename(columns={
        "customer": "Customer", "txn_count": "Txns", "net_flows": "Net (Rs)", "total_volume": "Volume (Rs)"
    })[["Customer", "Txns", "Net (Rs)", "Volume (Rs)"]]
    show_table("Account summary (Pandas)", f"{len(acct_summary)} accounts, by total volume.", acct_show, ["Txns", "Net (Rs)", "Volume (Rs)"])

    yearly_show = yearly.rename(columns={"year": "Year", "txn_count": "Txns", "net": "Net (Rs)"})
    show_table("Yearly summary", f"{len(yearly)} years.", yearly_show, ["Txns", "Net (Rs)"])

    st.markdown(
        "<div class='reveal'><div class='table-title'>Recent transactions</div>"
        f"<div class='table-caption'>Latest 15 of {len(view)} in filtered view.</div></div>",
        unsafe_allow_html=True,
    )
    recent = view.sort_values("date", ascending=False).head(15) if len(view) else view
    if len(recent):
        recent_show = pd.DataFrame({
            "Date": recent["date"].astype(str).str.slice(0, 10),
            "Customer": recent["customer"],
            "Type": recent["type"],
            "Amount (Rs)": recent["amount"],
        })
        st.markdown(apple_table(recent_show, ["Amount (Rs)"]), unsafe_allow_html=True)
    else:
        st.markdown(apple_table(pd.DataFrame()), unsafe_allow_html=True)

with t2:
    acct_df = pd.DataFrame(SAMPLE_CUSTOMERS)
    acct_show2 = pd.DataFrame({
        "Name": acct_df["name"],
        "Branch": acct_df["branch"],
        "Balance (Rs)": acct_df["balance"],
    })
    show_table("Accounts and branches", "Seeded customers. Balances update in the transfer demo.", acct_show2, ["Balance (Rs)"])
    st.markdown(
        '<div class="callout reveal">Blue is action. Ink is neutral. Red is risk. Nothing else is coloured.</div>',
        unsafe_allow_html=True,
    )

# ---------------- 05 risk ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Risk</div><h2>Suspicious transactions</h2>'
    "<p>Large amount at or above the threshold, bursts of 3+ per account per day, "
    "or night hours (00:00-04:00). Flagged rows need manual review, not auto-block.</p></div>",
    unsafe_allow_html=True,
)
with st.container(border=True):
    if flagged.empty:
        st.markdown(
            '<div class="callout good reveal">Nothing flagged at this threshold &mdash; good. '
            "Lower the threshold in Controls to see more.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='table-title reveal'>Flagged rows</div>"
            f"<div class='table-caption'>{len(flagged)} flagged of {len(df)} ({flagged_rate:.2f}%). Newest first.</div>",
            unsafe_allow_html=True,
        )
        flagged_show = pd.DataFrame({
            "Date": flagged["date"].astype(str).str.slice(0, 10),
            "Customer": flagged["customer"],
            "Type": flagged["type"],
            "Amount (Rs)": flagged["amount"],
        })
        st.markdown(apple_table(flagged_show, ["Amount (Rs)"]), unsafe_allow_html=True)
    st.caption("Rules live in `src/fraud.py` - transparent and auditable.")

# ---------------- 06 transfer demo ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Transfer demo</div><h2>Try a transfer</h2>'
    "<p>Balance and format checks, with clear rejections.</p></div>",
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
            st.success(f"Done. Ref {ref} · New balance Rs {src_acc['balance']:,.2f}")

st.caption(
    f"Structures active: dict accounts ({len(accounts)}) · list history ({history.total()} moves) · "
    f"queue ({len(queue.pending())} pending) · stack undo · defaultdict grouped ({len(grouped)} accounts)."
)

# ---------------- EXTRA 1 ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Extra 1 &middot; Insights</div><h2>Monthly insights and savings goal</h2>'
    "<p>Income, spend, net, savings rate, and a monthly-compounding goal projection.</p></div>",
    unsafe_allow_html=True,
)
with st.container(border=True):
    insights_show = insights.rename(columns={
        "month": "Month", "total_in": "In (Rs)", "total_out": "Out (Rs)",
        "net": "Net (Rs)", "savings_rate": "Savings %",
    })
    keep = [c for c in ["Month", "In (Rs)", "Out (Rs)", "Net (Rs)", "Savings %"] if c in insights_show.columns]
    show_table("Monthly insights", f"{len(insights)} months. Savings rate is net as % of income.", insights_show[keep], keep)
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
            line=dict(color=BLUE, width=3, shape="spline", smoothing=0.4),
            marker=dict(color=BLUE, size=5),
            fill="tozeroy", fillcolor="rgba(0,113,227,0.10)",
            hovertemplate="Month %{x}<br>Balance: Rs %{y:,.0f}<extra></extra>"))
        style_fig(fig_goal)
        fig_goal.update_yaxes(title="Balance Rs")
        st.plotly_chart(fig_goal, width="stretch", key="goal_apple")
        st.caption(f"Projected end balance: Rs {p_df['balance'].iloc[-1]:,.2f} in {int(n_months)} months (monthly compounding, demo only).")

# ---------------- EXTRA 2 ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Extra 2 &middot; Statement</div><h2>One-click account statement</h2>'
    "<p>Text statement with running balance. Download it directly from the dashboard.</p></div>",
    unsafe_allow_html=True,
)
with st.container(border=True):
    stmt_cust = st.selectbox("Statement for customer", sorted(df["customer"].unique().tolist()))
    stmt_txns = [t for t in txns if t["customer"] == stmt_cust] if txns else []
    acct_no = stmt_txns[0]["account_no"] if stmt_txns else "-"
    statement = storage.export_statement(acct_no, stmt_cust, stmt_txns)
    st.markdown(f"<div class='statement'>{html.escape(statement)}</div>", unsafe_allow_html=True)
    st.download_button("Download statement (.txt)", statement, file_name=f"statement_{stmt_cust.replace(' ', '_')}.txt", width="stretch")

# ---------------- checks ----------------
st.markdown(
    '<div class="sec reveal"><div class="sec-eyebrow">Checks &middot; Detail</div><h2>Regex checks and scraping detail</h2></div>',
    unsafe_allow_html=True,
)
checks = pd.DataFrame([
    {"Check": "Account no (10-16 digits)", "Result": "rev", "Pass": "Pass" if validate_account_no("2601299501") else "Fail"},
    {"Check": "PAN format", "Result": "BCCCC1234F", "Pass": "Pass" if validate_pan("BCCCC1234F") else "Fail"},
    {"Check": "TXN ref (TXN+8-14)", "Result": generate_txn_ref(), "Pass": "Pass" if validate_txn_ref(generate_txn_ref()) else "Fail"},
    {"Check": "Indian phone (6-9 start)", "Result": "9019709994", "Pass": "Pass" if validate_phone("9019709994") else "Fail"},
])
show_table("Validation results", "Regex checks from src/validation.py.", checks, [])

# FIX (v3): scrape detail as styled status cards, not a raw JSON block.
si = st.session_state.scrape_info
ok = bool(si.get("ok"))
url = si.get("url") or "Not run yet"
pcts = si.get("pcts", []) or []
chars = int(si.get("raw_chars", 0) or 0)
status_txt = "Figures found" if ok else ("Attempted, none found" if url != "Not run yet" else "Offline (seeded)")
st.markdown(
    "<div class='scrape-grid reveal'>"
    f"<div class='scrape-tile'><div class='scrape-lbl'>Status</div><div class='scrape-val'>{html.escape(status_txt)}</div></div>"
    f"<div class='scrape-tile'><div class='scrape-lbl'>Source</div><div class='scrape-val small'>{html.escape(str(url))}</div></div>"
    f"<div class='scrape-tile'><div class='scrape-lbl'>Figures found</div><div class='scrape-val'>{len(pcts)}</div></div>"
    f"<div class='scrape-tile'><div class='scrape-lbl'>Page chars</div><div class='scrape-val'>{chars:,}</div></div>"
    "</div>",
    unsafe_allow_html=True,
)
if pcts:
    st.caption("Sample figures parsed: " + ", ".join(f"{p}%" for p in pcts[:8]))
else:
    st.caption("Use Try live scrape in Controls. Seeded fallback keeps the demo working offline.")

st.markdown(
    '<div class="footer reveal"><div class="rule"></div>'
    "<span>Group 4 · Rahul S R, P Kavi Arasu, Prachodna B, Sarvesh MT · Python Activity 3</span><br>"
    "<span>Streamlit dashboard · Demo data is seeded</span></div>",
    unsafe_allow_html=True,
)
