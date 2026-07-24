"""
Fictrade — Practice Stock Trading (real prices, fake money)
===========================================================
Clean light UI. Real prices via Yahoo Finance (yfinance). Everything saves in
the browser (localStorage) — no login. Educational simulator only: no real
brokerage, orders, or money.

Run locally:  streamlit run app.py
"""

from __future__ import annotations
import json
import time
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Fictrade", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    from streamlit_local_storage import LocalStorage
    _LS = LocalStorage()
    LS_OK = True
except Exception:
    _LS = None
    LS_OK = False

STORE_KEY = "fictrade_store_v3"

# =============================================================================
# THEME (light, Groww/Zerodha-style)
# =============================================================================
PRIMARY = "#4B6FFF"      # indigo accent
PRIMARY_D = "#3355E6"
GREEN = "#12B76A"
RED = "#F04438"
AMBER = "#F79009"
PAGE = "#F4F6FB"
CARD = "#FFFFFF"
BORDER = "#E7EAF1"
TEXT = "#111827"
MUTED = "#6B7280"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=TEXT, size=12),
    margin=dict(l=8, r=8, t=30, b=8),
    xaxis=dict(gridcolor="#EEF1F6", zerolinecolor="#EEF1F6"),
    yaxis=dict(gridcolor="#EEF1F6", zerolinecolor="#EEF1F6"),
)


def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    html, body, [class*="css"] {{ font-family:'Inter',-apple-system,sans-serif; }}
    .stApp {{ background:{PAGE}; color:{TEXT}; }}
    .block-container {{ padding-top:1.1rem; max-width:1200px; }}
    /* Hide Streamlit chrome */
    #MainMenu, footer {{display:none;}}
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton {{display:none !important;}}
    [data-testid="stHeader"] {{background:transparent; height:0;}}
    a[href*="github.com"] {{display:none !important;}}
    [class*="viewerBadge"], [class*="profileContainer"], [class*="profilePreview"] {{display:none !important;}}
    a[href*="streamlit.io"], a[href*="share.streamlit"] {{display:none !important;}}
    /* Sidebar (light) */
    section[data-testid="stSidebar"] {{ background:{CARD}; border-right:1px solid {BORDER}; }}
    section[data-testid="stSidebar"] * {{ color:{TEXT} !important; }}
    h1,h2,h3 {{ font-weight:800 !important; letter-spacing:-0.02em; color:{TEXT} !important; }}
    /* Metric cards */
    div[data-testid="stMetric"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px;
        padding:12px 16px 8px; box-shadow:0 1px 2px rgba(16,24,40,0.04); }}
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {{ color:#475467 !important; opacity:1 !important;
        font-weight:600; font-size:0.8rem !important; }}
    div[data-testid="stMetricValue"] {{ font-family:'JetBrains Mono',monospace; font-weight:700 !important;
        font-size:1.5rem !important; white-space:normal !important; overflow:visible !important;
        text-overflow:clip !important; line-height:1.15 !important; color:{TEXT} !important; }}
    div[data-testid="stMetricValue"] > div {{ white-space:normal !important; overflow:visible !important; text-overflow:clip !important; }}
    /* Buttons */
    .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {{
        background:{PRIMARY}; color:#fff !important; border:none; border-radius:10px; font-weight:700;
        padding:0.5rem 1.1rem; transition:background .12s, transform .12s; box-shadow:0 1px 2px rgba(75,111,255,0.25); }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{ background:{PRIMARY_D}; transform:translateY(-1px); }}
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"]>div {{
        background:{CARD} !important; border:1px solid {BORDER} !important; border-radius:10px !important; color:{TEXT} !important; }}
    div[data-baseweb="popover"] {{ background:{CARD} !important; }}
    /* Tabs */
    button[data-baseweb="tab"] {{ font-weight:600; color:{MUTED} !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color:{PRIMARY} !important; }}
    div[data-baseweb="tab-highlight"] {{ background-color:{PRIMARY} !important; }}
    /* Top nav as pill tabs */
    div[data-testid="stMain"] div[role="radiogroup"] {{ gap:8px; flex-wrap:wrap; margin-bottom:12px; }}
    div[data-testid="stMain"] div[role="radiogroup"] label {{
        background:{CARD}; border:1px solid {BORDER}; border-radius:999px; padding:7px 15px !important;
        margin:0 !important; cursor:pointer; box-shadow:0 1px 2px rgba(16,24,40,0.05); }}
    div[data-testid="stMain"] div[role="radiogroup"] label p,
    div[data-testid="stMain"] div[role="radiogroup"] label div {{ color:{TEXT} !important; font-weight:600 !important; font-size:0.9rem; }}
    /* hide the round radio marker */
    div[data-testid="stMain"] div[role="radiogroup"] label > div:first-child {{ display:none !important; }}
    div[data-testid="stMain"] div[role="radiogroup"] label:has(input:checked) {{ background:{PRIMARY} !important; border-color:{PRIMARY} !important; }}
    div[data-testid="stMain"] div[role="radiogroup"] label:has(input:checked) p,
    div[data-testid="stMain"] div[role="radiogroup"] label:has(input:checked) div {{ color:#fff !important; }}
    /* Cards & pills */
    .hero {{ padding:22px 26px; border-radius:18px; background:linear-gradient(120deg,#EEF2FF,#F7FAFF);
        border:1px solid {BORDER}; margin-bottom:18px; }}
    .hero h1 {{ margin:0 0 2px 0; font-size:1.7rem; }}
    .hero p {{ margin:0; color:{MUTED}; font-size:0.95rem; }}
    .card {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px;
        box-shadow:0 1px 2px rgba(16,24,40,0.04); margin-bottom:12px; }}
    .pill {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:0.74rem; font-weight:700; }}
    .pill-green {{ background:#E7F7EF; color:{GREEN}; }}
    .pill-red {{ background:#FEECEB; color:{RED}; }}
    .pill-amber {{ background:#FEF3E6; color:{AMBER}; }}
    .pill-blue {{ background:#EEF2FF; color:{PRIMARY}; }}
    .badge {{ display:inline-flex; align-items:center; gap:6px; background:#EEF2FF; border:1px solid #DCE3FF;
        color:{PRIMARY}; border-radius:999px; padding:5px 12px; font-size:0.8rem; font-weight:700; margin:3px 6px 3px 0; }}
    .mono {{ font-family:'JetBrains Mono',monospace; }}
    .tape {{ white-space:nowrap; overflow-x:auto; padding-bottom:6px; }}
    .tape-item {{ display:inline-block; background:{CARD}; border:1px solid {BORDER}; border-radius:12px;
        padding:9px 14px; margin-right:8px; box-shadow:0 1px 2px rgba(16,24,40,0.04); }}
    .muted {{ color:{MUTED}; }}
    hr {{ border-color:{BORDER} !important; }}
    a {{ color:{PRIMARY} !important; }}
    .xp-track {{ width:100%; height:8px; border-radius:999px; background:#EDEFF5; overflow:hidden; }}
    .xp-fill {{ height:100%; background:{PRIMARY}; }}
    </style>
    """, unsafe_allow_html=True)


def hero(title, subtitle="", icon="📈"):
    st.markdown(f'<div class="hero"><h1>{icon} {title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def pill(text, kind="blue"):
    return f'<span class="pill pill-{kind}">{text}</span>'


def change_pill(pct):
    if pct is None:
        return pill("N/A", "amber")
    return pill(f"{'▲' if pct>=0 else '▼'} {pct:+.2f}%", "green" if pct >= 0 else "red")


def badge(text, icon="🏅"):
    return f'<span class="badge">{icon} {text}</span>'


def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def xp_bar(pct):
    pct = max(0, min(100, pct))
    st.markdown(f'<div class="xp-track"><div class="xp-fill" style="width:{pct}%;"></div></div>', unsafe_allow_html=True)


def fmt_money(v, compact=False):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if compact:
        a = abs(v)
        if a >= 1e12:
            return f"₹{v/1e12:.2f} L Cr"
        if a >= 1e7:
            return f"₹{v/1e7:.2f} Cr"
        if a >= 1e5:
            return f"₹{v/1e5:.2f} L"
        if a >= 1e3:
            return f"₹{v/1e3:.1f}K"
    return f"₹{v:,.2f}"


# =============================================================================
# SECURITIES + SECTORS (for autocomplete + analytics)
# =============================================================================
SECURITIES = [
    ("Reliance Industries", "RELIANCE.NS", "Energy"), ("Tata Consultancy Services (TCS)", "TCS.NS", "IT"),
    ("Infosys", "INFY.NS", "IT"), ("HDFC Bank", "HDFCBANK.NS", "Financials"), ("ICICI Bank", "ICICIBANK.NS", "Financials"),
    ("State Bank of India (SBI)", "SBIN.NS", "Financials"), ("ITC", "ITC.NS", "FMCG"), ("Wipro", "WIPRO.NS", "IT"),
    ("Bajaj Finance", "BAJFINANCE.NS", "Financials"), ("Adani Enterprises", "ADANIENT.NS", "Diversified"),
    ("Tata Motors", "TATAMOTORS.NS", "Auto"), ("Hindustan Unilever (HUL)", "HINDUNILVR.NS", "FMCG"),
    ("Larsen & Toubro (L&T)", "LT.NS", "Infrastructure"), ("Axis Bank", "AXISBANK.NS", "Financials"),
    ("Kotak Mahindra Bank", "KOTAKBANK.NS", "Financials"), ("Bharti Airtel", "BHARTIARTL.NS", "Telecom"),
    ("Asian Paints", "ASIANPAINT.NS", "Consumer"), ("Maruti Suzuki", "MARUTI.NS", "Auto"),
    ("Sun Pharma", "SUNPHARMA.NS", "Pharma"), ("Titan Company", "TITAN.NS", "Consumer"),
    ("Nestle India", "NESTLEIND.NS", "FMCG"), ("HCL Technologies", "HCLTECH.NS", "IT"),
    ("Tata Steel", "TATASTEEL.NS", "Metals"), ("Power Grid", "POWERGRID.NS", "Energy"), ("NTPC", "NTPC.NS", "Energy"),
    ("ONGC", "ONGC.NS", "Energy"), ("Coal India", "COALINDIA.NS", "Energy"), ("JSW Steel", "JSWSTEEL.NS", "Metals"),
    ("Adani Ports", "ADANIPORTS.NS", "Infrastructure"), ("UltraTech Cement", "ULTRACEMCO.NS", "Infrastructure"),
    ("Bajaj Finserv", "BAJAJFINSV.NS", "Financials"), ("Tech Mahindra", "TECHM.NS", "IT"), ("Grasim", "GRASIM.NS", "Infrastructure"),
    ("Hindalco", "HINDALCO.NS", "Metals"), ("Dr Reddy's Labs", "DRREDDY.NS", "Pharma"), ("Cipla", "CIPLA.NS", "Pharma"),
    ("Divi's Laboratories", "DIVISLAB.NS", "Pharma"), ("Britannia", "BRITANNIA.NS", "FMCG"),
    ("Eicher Motors", "EICHERMOT.NS", "Auto"), ("Hero MotoCorp", "HEROMOTOCO.NS", "Auto"),
    ("Bajaj Auto", "BAJAJ-AUTO.NS", "Auto"), ("IndusInd Bank", "INDUSINDBK.NS", "Financials"),
    ("SBI Life Insurance", "SBILIFE.NS", "Financials"), ("HDFC Life Insurance", "HDFCLIFE.NS", "Financials"),
    ("Apollo Hospitals", "APOLLOHOSP.NS", "Pharma"), ("Tata Consumer Products", "TATACONSUM.NS", "FMCG"),
    ("Adani Green Energy", "ADANIGREEN.NS", "Energy"), ("Adani Power", "ADANIPOWER.NS", "Energy"),
    ("Avenue Supermarts (DMart)", "DMART.NS", "Consumer"), ("Pidilite Industries", "PIDILITIND.NS", "Consumer"),
    ("Paytm (One97)", "PAYTM.NS", "Financials"), ("Nykaa (FSN E-Commerce)", "NYKAA.NS", "Consumer"),
    ("IRCTC", "IRCTC.NS", "Consumer"), ("Vedanta", "VEDL.NS", "Metals"), ("Life Insurance Corp (LIC)", "LICI.NS", "Financials"),
    ("Bank of Baroda", "BANKBARODA.NS", "Financials"), ("Punjab National Bank (PNB)", "PNB.NS", "Financials"),
    ("GAIL India", "GAIL.NS", "Energy"), ("BPCL", "BPCL.NS", "Energy"), ("Indian Oil (IOC)", "IOC.NS", "Energy"),
    ("Tata Power", "TATAPOWER.NS", "Energy"), ("Ambuja Cements", "AMBUJACEM.NS", "Infrastructure"),
    ("Shree Cement", "SHREECEM.NS", "Infrastructure"), ("DLF", "DLF.NS", "Infrastructure"), ("Havells India", "HAVELLS.NS", "Consumer"),
    ("Dabur India", "DABUR.NS", "FMCG"), ("Godrej Consumer", "GODREJCP.NS", "FMCG"), ("Siemens India", "SIEMENS.NS", "Infrastructure"),
    ("Bosch", "BOSCHLTD.NS", "Auto"), ("Berger Paints", "BERGEPAINT.NS", "Consumer"), ("Marico", "MARICO.NS", "FMCG"),
    ("Colgate-Palmolive India", "COLPAL.NS", "FMCG"), ("InterGlobe Aviation (IndiGo)", "INDIGO.NS", "Consumer"),
    ("Bharat Electronics (BEL)", "BEL.NS", "Infrastructure"), ("Bharat Forge", "BHARATFORG.NS", "Auto"),
    ("Page Industries", "PAGEIND.NS", "Consumer"), ("SRF", "SRF.NS", "Infrastructure"), ("Trent", "TRENT.NS", "Consumer"),
    ("Tata Elxsi", "TATAELXSI.NS", "IT"), ("Mphasis", "MPHASIS.NS", "IT"), ("LTIMindtree", "LTIM.NS", "IT"),
    ("Persistent Systems", "PERSISTENT.NS", "IT"), ("Yes Bank", "YESBANK.NS", "Financials"),
    ("IDFC First Bank", "IDFCFIRSTB.NS", "Financials"), ("Federal Bank", "FEDERALBNK.NS", "Financials"),
    ("Zomato / Eternal", "ETERNAL.NS", "Consumer"),
    ("Apple", "AAPL", "Global"), ("Microsoft", "MSFT", "Global"), ("Alphabet (Google)", "GOOGL", "Global"),
    ("Amazon", "AMZN", "Global"), ("Nvidia", "NVDA", "Global"), ("Tesla", "TSLA", "Global"), ("Meta (Facebook)", "META", "Global"),
    ("Netflix", "NFLX", "Global"),
]
POPULAR_IN = [t for n, t, s in SECURITIES if t.endswith(".NS")][:20]
LABELS = [f"{n}  ·  {t}" for n, t, s in SECURITIES]
LABEL_TO_TICKER = {f"{n}  ·  {t}": t for n, t, s in SECURITIES}
TICKER_TO_NAME = {t: n for n, t, s in SECURITIES}
SECTOR_OF = {t: s for n, t, s in SECURITIES}
INDICES = [("Nifty 50", "^NSEI"), ("Sensex", "^BSESN"), ("Bank Nifty", "^NSEBANK")]
PERIOD_INTERVAL = {"1D": ("1d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "1d"),
                   "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "5Y": ("5y", "1wk"), "MAX": ("max", "1mo")}


def short_name(t):
    return TICKER_TO_NAME.get(t, t).split("(")[0].strip()


def security_picker(label, key, default_ticker=None):
    """Type-to-search company picker. index=None -> no need to erase anything."""
    idx = None
    if default_ticker and default_ticker in TICKER_TO_NAME:
        lbl = f"{TICKER_TO_NAME[default_ticker]}  ·  {default_ticker}"
        if lbl in LABELS:
            idx = LABELS.index(lbl)
    sel = st.selectbox(label, LABELS, index=idx, key=key,
                       placeholder="🔍 Type a company name — e.g. Tata, Reliance, Infosys")
    ticker = LABEL_TO_TICKER.get(sel) if sel else None
    with st.expander("Can't find it? Enter any ticker manually"):
        manual = st.text_input("Ticker (Indian stocks end in .NS, e.g. TATAMOTORS.NS)", key=key + "_manual").strip().upper()
        if manual:
            ticker = manual
    return ticker


# =============================================================================
# DATA
# =============================================================================
def _sg(d, *keys, default=None):
    for k in keys:
        v = d.get(k) if isinstance(d, dict) else None
        if v is not None:
            return v
    return default


@st.cache_data(ttl=90, show_spinner=False)
def get_history(ticker, period="6mo", interval="1d"):
    if yf is None:
        return pd.DataFrame()
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        dc = "Datetime" if "Datetime" in df.columns else "Date"
        return df.rename(columns={dc: "Date"})
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=45, show_spinner=False)
def get_quote(ticker):
    out = {"ticker": ticker, "ok": False, "name": TICKER_TO_NAME.get(ticker, ticker), "price": None,
           "prev_close": None, "change_pct": None, "day_high": None, "day_low": None, "market_cap": None,
           "year_high": None, "year_low": None, "volume": None}
    if yf is None:
        return out
    try:
        t = yf.Ticker(ticker)
        try:
            fi = dict(t.fast_info)
        except Exception:
            fi = {}
        price = _sg(fi, "lastPrice", "last_price")
        prev = _sg(fi, "previousClose", "previous_close")
        if price is None or prev is None:
            h = get_history(ticker, "5d", "1d")
            if not h.empty:
                if price is None:
                    price = float(h["Close"].iloc[-1])
                if prev is None and len(h) > 1:
                    prev = float(h["Close"].iloc[-2])
        if price is None:
            return out
        prev = prev or price
        out.update({"ok": True, "price": float(price), "prev_close": float(prev),
                    "change_pct": float((price - prev) / prev * 100) if prev else 0.0,
                    "day_high": _sg(fi, "dayHigh", "day_high"), "day_low": _sg(fi, "dayLow", "day_low"),
                    "market_cap": _sg(fi, "marketCap", "market_cap"), "volume": _sg(fi, "lastVolume", "last_volume"),
                    "year_high": _sg(fi, "yearHigh", "year_high"), "year_low": _sg(fi, "yearLow", "year_low")})
        try:
            info = t.get_info()
            out["name"] = TICKER_TO_NAME.get(ticker) or info.get("shortName") or info.get("longName") or ticker
            if out["market_cap"] is None:
                out["market_cap"] = info.get("marketCap")
        except Exception:
            pass
        return out
    except Exception:
        return out


@st.cache_data(ttl=45, show_spinner=False)
def get_quotes_batch(tickers):
    return {t: get_quote(t) for t in tickers}


@st.cache_data(ttl=300, show_spinner=False)
def get_news(ticker, limit=8):
    if yf is None:
        return []
    try:
        items = yf.Ticker(ticker).news or []
        out = []
        for it in items[:limit]:
            c = it.get("content", it)
            title = c.get("title") or it.get("title")
            prov = c.get("provider")
            pub = prov.get("displayName") if isinstance(prov, dict) else it.get("publisher")
            cu = c.get("canonicalUrl")
            link = cu.get("url") if isinstance(cu, dict) else it.get("link")
            if title:
                out.append({"title": title, "publisher": pub or "Unknown", "link": link or "#"})
        return out
    except Exception:
        return []


# =============================================================================
# INDICATORS
# =============================================================================
def sma(s, w):
    return s.rolling(window=w, min_periods=max(2, w // 3)).mean()


def ema(s, w):
    return s.ewm(span=w, adjust=False).mean()


def rsi(s, w=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(alpha=1 / w, min_periods=w).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1 / w, min_periods=w).mean()
    rs = g / l.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def macd(s, fast=12, slow=26, signal=9):
    ml = ema(s, fast) - ema(s, slow)
    return ml, ema(ml, signal), ml - ema(ml, signal)


def bollinger(s, w=20, n=2.0):
    m = sma(s, w)
    sd = s.rolling(window=w, min_periods=max(2, w // 3)).std()
    return m + n * sd, m, m - n * sd


def vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).cumsum() / df["Volume"].replace(0, np.nan).cumsum()


def build_price_chart(df, ticker, overlays, show_rsi, show_macd, show_vol, height=560):
    rows = 1 + int(show_rsi) + int(show_macd) + int(show_vol)
    heights = [0.58] + [0.42 / (rows - 1)] * (rows - 1) if rows > 1 else [1.0]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, row_heights=heights, vertical_spacing=0.04)
    fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                 name=ticker, increasing_line_color=GREEN, decreasing_line_color=RED,
                                 increasing_fillcolor=GREEN, decreasing_fillcolor=RED), row=1, col=1)
    if "SMA 20" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=sma(df["Close"], 20), name="SMA 20", line=dict(color=PRIMARY, width=1.4)), row=1, col=1)
    if "SMA 50" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=sma(df["Close"], 50), name="SMA 50", line=dict(color=AMBER, width=1.4)), row=1, col=1)
    if "EMA 20" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=ema(df["Close"], 20), name="EMA 20", line=dict(color="#9B51E0", width=1.3, dash="dot")), row=1, col=1)
    if "VWAP" in overlays and "Volume" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=vwap(df), name="VWAP", line=dict(color="#0BA5EC", width=1.3)), row=1, col=1)
    if "Bollinger Bands" in overlays:
        u, m, l = bollinger(df["Close"])
        fig.add_trace(go.Scatter(x=df["Date"], y=u, name="BB U", line=dict(color="rgba(75,111,255,0.4)", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=l, name="BB L", line=dict(color="rgba(75,111,255,0.4)", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(75,111,255,0.06)"), row=1, col=1)
    r = 2
    if show_vol and "Volume" in df.columns:
        vc = [GREEN if c >= o else RED for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Vol", marker_color=vc, opacity=0.5), row=r, col=1)
        fig.update_yaxes(title_text="Vol", row=r, col=1)
        r += 1
    if show_rsi:
        fig.add_trace(go.Scatter(x=df["Date"], y=rsi(df["Close"]), name="RSI", line=dict(color="#9B51E0", width=1.4)), row=r, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="rgba(240,68,56,0.5)", row=r, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="rgba(18,183,106,0.5)", row=r, col=1)
        fig.update_yaxes(range=[0, 100], title_text="RSI", row=r, col=1)
        r += 1
    if show_macd:
        ml, ms, mh = macd(df["Close"])
        fig.add_trace(go.Bar(x=df["Date"], y=mh, name="Hist", marker_color=[GREEN if v >= 0 else RED for v in mh.fillna(0)]), row=r, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=ml, name="MACD", line=dict(color=PRIMARY, width=1.2)), row=r, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=ms, name="Signal", line=dict(color=AMBER, width=1.2)), row=r, col=1)
        fig.update_yaxes(title_text="MACD", row=r, col=1)
    fig.update_layout(**PLOTLY_LAYOUT, height=height, xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h", y=1.03, bgcolor="rgba(0,0,0,0)"), dragmode="pan")
    return fig


# =============================================================================
# PORTFOLIO
# =============================================================================
BADGE_DEFS = [
    ("first_trade", "🎬", "First Trade", "Placed your first order."),
    ("five_holdings", "🧺", "Diversifier", "Held 5+ different stocks."),
    ("ten_trades", "🔟", "Getting Serious", "Placed 10 trades."),
    ("profit_10", "🌱", "In The Green", "Return crossed +10%."),
    ("profit_25", "🚀", "On A Roll", "Return crossed +25%."),
    ("first_loss_take", "🩹", "Cut The Loss", "Sold a losing position."),
    ("limit_order", "🎯", "Sniper", "Placed a limit order."),
    ("journaled", "📓", "Reflective", "Wrote a journal note."),
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def new_portfolio(name, starting_cash):
    return {"name": name, "currency": "INR", "starting_cash": float(starting_cash), "cash": float(starting_cash),
            "holdings": {}, "transactions": [], "net_worth_history": [{"ts": _now(), "value": float(starting_cash)}],
            "journal": [], "badges": [], "watchlist": [], "orders": [], "alerts": []}


class Portfolio:
    def __init__(self, d):
        d.setdefault("orders", [])
        d.setdefault("alerts", [])
        self.d = d

    cash = property(lambda self: self.d["cash"])
    holdings = property(lambda self: self.d["holdings"])
    transactions = property(lambda self: self.d["transactions"])
    starting_cash = property(lambda self: self.d["starting_cash"])
    orders = property(lambda self: self.d["orders"])
    alerts = property(lambda self: self.d["alerts"])

    def invested_cost(self):
        return sum(p["qty"] * p["avg_price"] for p in self.holdings.values())

    def holdings_value(self, prices):
        return sum(prices.get(t, p["avg_price"]) * p["qty"] for t, p in self.holdings.items())

    def total_value(self, prices):
        return self.cash + self.holdings_value(prices)

    def total_return_pct(self, prices):
        s = self.starting_cash
        return 0.0 if s <= 0 else (self.total_value(prices) - s) / s * 100

    def buy(self, ticker, qty, price, note=""):
        if qty <= 0 or not price or price <= 0:
            return False, "Invalid quantity or price."
        cost = qty * price
        if cost > self.cash + 1e-6:
            return False, "Not enough virtual cash."
        self.d["cash"] -= cost
        pos = self.holdings.get(ticker, {"qty": 0, "avg_price": 0.0})
        nq = pos["qty"] + qty
        self.holdings[ticker] = {"qty": nq, "avg_price": ((pos["qty"] * pos["avg_price"]) + cost) / nq}
        self._log(ticker, "BUY", qty, price, note)
        return True, f"Bought {qty} × {short_name(ticker)} @ ₹{price:,.2f}"

    def sell(self, ticker, qty, price, note=""):
        pos = self.holdings.get(ticker)
        if not pos or pos["qty"] < qty or qty <= 0 or not price or price <= 0:
            return False, "You don't hold enough shares."
        realized = (price - pos["avg_price"]) * qty
        self.d["cash"] += qty * price
        rem = pos["qty"] - qty
        if rem <= 0:
            del self.holdings[ticker]
        else:
            self.holdings[ticker] = {"qty": rem, "avg_price": pos["avg_price"]}
        self._log(ticker, "SELL", qty, price, note, realized)
        return True, f"Sold {qty} × {short_name(ticker)} @ ₹{price:,.2f} ({'+' if realized>=0 else ''}₹{realized:,.2f})"

    def _log(self, ticker, side, qty, price, note="", realized=None):
        self.transactions.append({"id": uuid.uuid4().hex[:10], "ts": _now(), "ticker": ticker, "side": side,
                                  "qty": qty, "price": price, "total": qty * price, "note": note, "realized_pl": realized})

    # ---- limit orders ----
    def add_order(self, ticker, side, qty, limit_price):
        self.orders.append({"id": uuid.uuid4().hex[:8], "ts": _now(), "ticker": ticker, "side": side,
                            "qty": int(qty), "limit": float(limit_price)})

    def cancel_order(self, oid):
        self.d["orders"] = [o for o in self.orders if o["id"] != oid]

    def check_orders(self, prices):
        """Fill pending limit orders when the market crosses the limit. Returns messages."""
        filled = []
        remaining = []
        for o in self.orders:
            px = prices.get(o["ticker"])
            if px is None:
                remaining.append(o)
                continue
            hit = (o["side"] == "BUY" and px <= o["limit"]) or (o["side"] == "SELL" and px >= o["limit"])
            if not hit:
                remaining.append(o)
                continue
            if o["side"] == "BUY":
                ok, msg = self.buy(o["ticker"], o["qty"], px, note="limit order")
            else:
                ok, msg = self.sell(o["ticker"], o["qty"], px, note="limit order")
            if ok:
                filled.append(f"🎯 Limit order filled — {msg}")
            else:
                remaining.append(o)  # couldn't fill (e.g. no cash) -> keep
        self.d["orders"] = remaining
        return filled

    # ---- alerts ----
    def add_alert(self, ticker, direction, price):
        self.alerts.append({"id": uuid.uuid4().hex[:8], "ticker": ticker, "dir": direction,
                            "price": float(price), "done": False})

    def remove_alert(self, aid):
        self.d["alerts"] = [a for a in self.alerts if a["id"] != aid]

    def check_alerts(self, prices):
        msgs = []
        for a in self.alerts:
            if a["done"]:
                continue
            px = prices.get(a["ticker"])
            if px is None:
                continue
            if (a["dir"] == "above" and px >= a["price"]) or (a["dir"] == "below" and px <= a["price"]):
                a["done"] = True
                msgs.append(f"🔔 {short_name(a['ticker'])} is now {a['dir']} ₹{a['price']:,.2f} (₹{px:,.2f})")
        return msgs

    # ---- misc ----
    def add_journal(self, ticker, text):
        self.d["journal"].append({"ts": _now(), "ticker": ticker, "text": text})

    def add_watch(self, t):
        if t not in self.d["watchlist"]:
            self.d["watchlist"].append(t)

    def remove_watch(self, t):
        if t in self.d["watchlist"]:
            self.d["watchlist"].remove(t)

    def snapshot(self, prices, force=False):
        v = self.total_value(prices)
        h = self.d["net_worth_history"]
        if force or not h or h[-1]["value"] != v:
            h.append({"ts": _now(), "value": v})
            self.d["net_worth_history"] = h[-500:]

    def xp(self):
        realized = sum(t.get("realized_pl") or 0 for t in self.transactions)
        return int(len(self.transactions) * 15 + max(0, realized) / 500 + len(self.d["badges"]) * 40)

    def level(self):
        return self.xp() // 250 + 1

    def level_progress_pct(self):
        return (self.xp() - (self.level() - 1) * 250) / 250 * 100

    def check_badges(self, prices):
        earned = set(self.d["badges"])
        new = []

        def aw(b):
            if b not in earned:
                earned.add(b)
                new.append(b)
        n = len(self.transactions)
        if n >= 1:
            aw("first_trade")
        if n >= 10:
            aw("ten_trades")
        if len(self.holdings) >= 5:
            aw("five_holdings")
        if any(t.get("side") == "SELL" and (t.get("realized_pl") or 0) < 0 for t in self.transactions):
            aw("first_loss_take")
        if self.d["journal"]:
            aw("journaled")
        if any(t.get("note") == "limit order" for t in self.transactions) or self.orders:
            aw("limit_order")
        r = self.total_return_pct(prices)
        if r >= 10:
            aw("profit_10")
        if r >= 25:
            aw("profit_25")
        self.d["badges"] = sorted(earned)
        return new

    def badge_details(self):
        e = set(self.d["badges"])
        return [{"id": b, "icon": i, "title": t, "desc": d, "earned": b in e} for b, i, t, d in BADGE_DEFS]

    def reset(self, starting_cash=None):
        self.d.update(new_portfolio(self.d["name"], starting_cash or self.starting_cash))


# =============================================================================
# STORAGE (browser localStorage, no login)
# =============================================================================
def default_store():
    return {"onboarded": False, "profiles": {}, "active_profile": None}


def load_store():
    if st.session_state.get("loaded"):
        return
    raw = None
    if LS_OK:
        try:
            raw = _LS.getItem(STORE_KEY)
        except Exception:
            raw = None
    if raw:
        try:
            st.session_state["store"] = json.loads(raw)
        except Exception:
            st.session_state["store"] = default_store()
        st.session_state["loaded"] = True
        return
    tries = st.session_state.get("load_tries", 0)
    if LS_OK and tries < 3:
        st.session_state["load_tries"] = tries + 1
        time.sleep(0.4)
        st.rerun()
    st.session_state.setdefault("store", default_store())
    st.session_state["loaded"] = True


def _js_write(blob):
    try:
        import streamlit.components.v1 as components
        components.html(f"<script>try{{window.parent.localStorage.setItem({json.dumps(STORE_KEY)}, {json.dumps(blob)});}}catch(e){{}}</script>", height=0, width=0)
    except Exception:
        pass


def save_store():
    if "store" not in st.session_state:
        return
    blob = json.dumps(st.session_state["store"])
    if LS_OK:
        st.session_state["ls_n"] = st.session_state.get("ls_n", 0) + 1
        try:
            _LS.setItem(STORE_KEY, blob, key=f"set_{st.session_state['ls_n']}")
        except Exception:
            pass
    _js_write(blob)


def store():
    return st.session_state["store"]


def active_portfolio():
    s = store()
    profs = s["profiles"]
    name = s.get("active_profile")
    if name not in profs:
        name = next(iter(profs))
        s["active_profile"] = name
    return Portfolio(profs[name])


def price_lookup_for(pm, extra=()):
    ts = tuple(set(list(pm.holdings.keys()) + [o["ticker"] for o in pm.orders] +
                   [a["ticker"] for a in pm.alerts if not a["done"]] + list(extra)))
    if not ts:
        return {}
    q = get_quotes_batch(ts)
    return {t: x["price"] for t, x in q.items() if x and x.get("ok") and x.get("price")}


def onboarding():
    inject_css()
    hero("Welcome to Fictrade", "Practice trading Indian & global stocks with real prices and fake money. "
         "Everything saves automatically in this browser — no login needed.", "📈")
    card_open()
    st.markdown("#### Set up your practice portfolio")
    with st.form("onb"):
        name = st.text_input("Portfolio name", value="My Portfolio")
        amount = st.number_input("How much virtual money do you want to start with? (₹)",
                                 min_value=1000.0, value=1000000.0, step=50000.0,
                                 help="Your total investable capital. Default ₹10,00,000 (10 lakh).")
        if st.form_submit_button("🚀 Start trading", use_container_width=True):
            nm = name.strip() or "My Portfolio"
            prof = new_portfolio(nm, amount)
            prof["watchlist"] = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
            store()["profiles"] = {nm: prof}
            store()["active_profile"] = nm
            store()["onboarded"] = True
            st.rerun()
    card_close()
    st.caption("⚠️ Simulated trading only — real market prices, but no real money, orders, or broker.")


# =============================================================================
# SIDEBAR (profile + net worth; navigation is at the top of the page)
# =============================================================================
def render_sidebar():
    st.sidebar.markdown("### 📈 Fictrade")
    st.sidebar.caption("Practice trading. Real prices. Zero real risk.")
    st.sidebar.markdown("---")
    s = store()
    names = list(s["profiles"].keys())
    active = s.get("active_profile")
    choice = st.sidebar.selectbox("Portfolio", names, index=names.index(active) if active in names else 0)
    if choice != active:
        s["active_profile"] = choice
        st.rerun()
    with st.sidebar.expander("➕ New portfolio"):
        with st.form("new_prof", clear_on_submit=True):
            nm = st.text_input("Name", placeholder="e.g. Aggressive Bets")
            amt = st.number_input("Starting money (₹)", min_value=1000.0, value=1000000.0, step=50000.0)
            if st.form_submit_button("Create") and nm.strip():
                if nm.strip() not in s["profiles"]:
                    s["profiles"][nm.strip()] = new_portfolio(nm.strip(), amt)
                    s["active_profile"] = nm.strip()
                    st.rerun()
    pm = active_portfolio()
    prices = price_lookup_for(pm)
    st.sidebar.markdown("---")
    st.sidebar.metric("Net worth", fmt_money(pm.total_value(prices), compact=True), f"{pm.total_return_pct(prices):+.2f}%")
    st.sidebar.progress(min(max(pm.level_progress_pct() / 100, 0.0), 1.0), text=f"Level {pm.level()} • {pm.xp()} XP")
    st.sidebar.caption("⚠️ Simulated — no real orders or money.")
    return pm, prices


# =============================================================================
# PAGES
# =============================================================================
def page_dashboard(pm, prices):
    hero(f"{pm.d['name']}", "Your practice portfolio at a glance. Prices are real (Yahoo Finance); trades are fictional.", "🏠")

    # Indices
    st.markdown("#### 📊 Markets today")
    iq = get_quotes_batch(tuple(t for _, t in INDICES))
    cols = st.columns(len(INDICES))
    for c, (nm, t) in zip(cols, INDICES):
        q = iq.get(t)
        if q and q.get("ok"):
            c.metric(nm, f"{q['price']:,.0f}", f"{q['change_pct']:+.2f}%")
        else:
            c.metric(nm, "—")

    # Money breakdown
    invested = pm.invested_cost()
    hv = pm.holdings_value(prices)
    day_pnl = 0.0
    for t, p in pm.holdings.items():
        q = get_quote(t)
        if q.get("ok") and q.get("prev_close"):
            day_pnl += p["qty"] * (q["price"] - q["prev_close"])
    st.markdown("#### 💰 Your money")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investable capital", fmt_money(pm.starting_cash, compact=True))
    c2.metric("Invested (at cost)", fmt_money(invested, compact=True))
    c3.metric("Holdings value", fmt_money(hv, compact=True), f"{((hv-invested)/invested*100) if invested else 0:+.2f}%")
    c4.metric("Cash left", fmt_money(pm.cash, compact=True))
    d1, d2, d3 = st.columns(3)
    d1.metric("Total net worth", fmt_money(pm.total_value(prices), compact=True), f"{pm.total_return_pct(prices):+.2f}% all-time")
    d2.metric("Today's P&L", fmt_money(day_pnl, compact=True))
    d3.metric("Capital deployed", f"{min((invested/pm.starting_cash*100) if pm.starting_cash else 0,100):.1f}%")

    left, right = st.columns([2, 1])
    with left:
        st.markdown("#### Net worth over time")
        h = pm.d["net_worth_history"]
        if len(h) >= 2:
            df = pd.DataFrame(h)
            df["ts"] = pd.to_datetime(df["ts"])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["ts"], y=df["value"], mode="lines", fill="tozeroy",
                                     line=dict(color=PRIMARY, width=2.5), fillcolor="rgba(75,111,255,0.08)"))
            fig.add_hline(y=pm.starting_cash, line_dash="dot", line_color="#C7CDDA")
            fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Make your first trade to start tracking your net-worth curve.")
    with right:
        st.markdown("#### 🏅 Level & badges")
        card_open()
        st.markdown(f"**Level {pm.level()}** — {pm.xp()} XP")
        xp_bar(pm.level_progress_pct())
        st.write("")
        earned = [b for b in pm.badge_details() if b["earned"]]
        if earned:
            st.markdown("".join(badge(b["title"], b["icon"]) for b in earned[-6:]), unsafe_allow_html=True)
        else:
            st.caption("Place your first trade to start earning badges.")
        card_close()

    # Movers
    st.markdown("#### 🔥 Top movers")
    mq = get_quotes_batch(tuple(POPULAR_IN))
    valid = [(t, q) for t, q in mq.items() if q and q.get("ok")]
    gainers = sorted(valid, key=lambda x: -x[1]["change_pct"])[:4]
    losers = sorted(valid, key=lambda x: x[1]["change_pct"])[:4]
    gc, lc = st.columns(2)
    with gc:
        st.markdown("**Gainers**")
        for t, q in gainers:
            a, b = st.columns([2, 1])
            a.markdown(f"{short_name(t)} <span class='muted mono' style='font-size:0.8rem'>{fmt_money(q['price'])}</span>", unsafe_allow_html=True)
            b.markdown(change_pill(q["change_pct"]), unsafe_allow_html=True)
    with lc:
        st.markdown("**Losers**")
        for t, q in losers:
            a, b = st.columns([2, 1])
            a.markdown(f"{short_name(t)} <span class='muted mono' style='font-size:0.8rem'>{fmt_money(q['price'])}</span>", unsafe_allow_html=True)
            b.markdown(change_pill(q["change_pct"]), unsafe_allow_html=True)


def _order_panels(pm, prices, ticker, qq):
    existing = pm.holdings.get(ticker)
    o1, o2 = st.columns(2)
    with o1:
        card_open()
        st.markdown("#### 🟢 Buy")
        otype = st.radio("Order type", ["Market", "Limit"], horizontal=True, key="buy_otype")
        with st.form("buy"):
            maxq = int(pm.cash // qq["price"]) if qq["price"] else 0
            qty = st.number_input("Quantity", min_value=1, value=min(10, max(1, maxq)) or 1, step=1)
            limit_price = None
            if otype == "Limit":
                limit_price = st.number_input("Buy when price ≤ (₹)", min_value=0.01, value=round(qq["price"] * 0.98, 2), step=0.5)
            st.caption(f"Est. cost: **{fmt_money(qty*(limit_price or qq['price']))}** · Cash: {fmt_money(pm.cash)} · Max: {maxq}")
            note = st.text_input("Note (optional)")
            if st.form_submit_button(f"Place {otype} Buy", use_container_width=True):
                if otype == "Limit":
                    pm.add_order(ticker, "BUY", qty, limit_price)
                    pm.check_badges(prices)
                    save_store()
                    st.success(f"Limit buy set: {qty} × {short_name(ticker)} when ≤ ₹{limit_price:,.2f}")
                    st.rerun()
                else:
                    ok, msg = pm.buy(ticker, int(qty), qq["price"], note)
                    if ok:
                        if note:
                            pm.add_journal(ticker, note)
                        pm.snapshot({**prices, ticker: qq["price"]}, force=True)
                        pm.check_badges({**prices, ticker: qq["price"]})
                        save_store()
                        st.success(msg + " — saved.")
                        st.rerun()
                    else:
                        st.error(msg)
        card_close()
    with o2:
        card_open()
        st.markdown("#### 🔴 Sell")
        if existing:
            st.caption(f"Holding **{existing['qty']}** @ avg {fmt_money(existing['avg_price'])}")
            st.markdown(change_pill((qq["price"] - existing["avg_price"]) / existing["avg_price"] * 100), unsafe_allow_html=True)
            sotype = st.radio("Order type", ["Market", "Limit"], horizontal=True, key="sell_otype")
            with st.form("sell"):
                qty = st.number_input("Quantity", min_value=1, max_value=int(existing["qty"]), value=int(existing["qty"]), step=1)
                slimit = None
                if sotype == "Limit":
                    slimit = st.number_input("Sell when price ≥ (₹)", min_value=0.01, value=round(qq["price"] * 1.02, 2), step=0.5)
                note = st.text_input("Note (optional)", key="sellnote")
                if st.form_submit_button(f"Place {sotype} Sell", use_container_width=True):
                    if sotype == "Limit":
                        pm.add_order(ticker, "SELL", qty, slimit)
                        save_store()
                        st.success(f"Limit sell set: {qty} × {short_name(ticker)} when ≥ ₹{slimit:,.2f}")
                        st.rerun()
                    else:
                        ok, msg = pm.sell(ticker, int(qty), qq["price"], note)
                        if ok:
                            if note:
                                pm.add_journal(ticker, note)
                            pm.snapshot({**prices, ticker: qq["price"]}, force=True)
                            pm.check_badges({**prices, ticker: qq["price"]})
                            save_store()
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.caption("You don't currently hold this stock.")
        card_close()


def page_trade(pm, prices):
    hero("Trade", "Search a company, view its candlestick chart & news, and place market or limit orders.", "💰")
    ticker = security_picker("Company / ticker", "trade_pick", st.session_state.get("trade_ticker"))
    if not ticker:
        st.info("Start typing a company name above — e.g. 'Tata', 'Reliance', 'Infosys'.")
        return
    st.session_state["trade_ticker"] = ticker
    with st.spinner(f"Fetching live data for {ticker}…"):
        qq = get_quote(ticker)
    if not qq.get("ok"):
        st.error(f"Couldn't fetch data for '{ticker}'. Indian stocks need a '.NS' suffix (e.g. TATAMOTORS.NS).")
        return

    a, b, c, d, e = st.columns([1.7, 1, 1, 1, 1])
    a.markdown(f"### {qq['name']}")
    a.markdown(f"`{ticker}` &nbsp; " + change_pill(qq["change_pct"]), unsafe_allow_html=True)
    b.metric("Price", fmt_money(qq["price"]))
    c.metric("Day High", fmt_money(qq.get("day_high")) if qq.get("day_high") else "—")
    d.metric("Day Low", fmt_money(qq.get("day_low")) if qq.get("day_low") else "—")
    e.metric("Mkt Cap", fmt_money(qq.get("market_cap"), compact=True) if qq.get("market_cap") else "—")

    # Candlestick chart on the Trade page
    cc1, cc2 = st.columns([1, 2])
    tf = cc1.select_slider("Timeframe", options=list(PERIOD_INTERVAL.keys()), value="6M", key="trade_tf")
    overlays = cc2.multiselect("Overlays", ["SMA 20", "SMA 50", "EMA 20", "VWAP", "Bollinger Bands"],
                               default=["SMA 20", "SMA 50"], key="trade_ov")
    period, interval = PERIOD_INTERVAL[tf]
    df = get_history(ticker, period, interval)
    if not df.empty:
        st.plotly_chart(build_price_chart(df, ticker, overlays, show_rsi=True, show_macd=False, show_vol=True, height=440),
                        use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})

    st.markdown("---")
    _order_panels(pm, prices, ticker, qq)

    # Watchlist + alert
    wc1, wc2 = st.columns([1, 2])
    inw = ticker in pm.d["watchlist"]
    if wc1.button("⭐ Remove from Watchlist" if inw else "☆ Add to Watchlist"):
        pm.remove_watch(ticker) if inw else pm.add_watch(ticker)
        save_store()
        st.rerun()
    with wc2.expander("🔔 Set a price alert"):
        with st.form("alertf"):
            adir = st.radio("Notify when price goes", ["above", "below"], horizontal=True)
            aprice = st.number_input("Target price (₹)", min_value=0.01, value=round(qq["price"], 2), step=0.5)
            if st.form_submit_button("Set alert"):
                pm.add_alert(ticker, adir, aprice)
                save_store()
                st.success(f"Alert set: {short_name(ticker)} {adir} ₹{aprice:,.2f}")

    # Per-stock news
    st.markdown("#### 📰 Latest news")
    news = get_news(ticker, 6)
    if not news:
        st.caption("No recent headlines found for this company.")
    else:
        for n in news:
            st.markdown(f"- **[{n['title']}]({n['link']})**  <span class='muted' style='font-size:0.8rem'>· {n['publisher']}</span>", unsafe_allow_html=True)


def page_portfolio(pm, prices):
    hero("Portfolio", "Holdings, analytics, pending orders, and full history.", "📊")
    invested = pm.invested_cost()
    hv = pm.holdings_value(prices)
    realized = sum(t.get("realized_pl") or 0 for t in pm.transactions)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net worth", fmt_money(pm.total_value(prices), compact=True), f"{pm.total_return_pct(prices):+.2f}%")
    c2.metric("Invested (cost)", fmt_money(invested, compact=True))
    c3.metric("Unrealized P&L", fmt_money(hv - invested, compact=True))
    c4.metric("Realized P&L", fmt_money(realized, compact=True))

    t1, t2, t3, t4, t5, t6 = st.tabs(["📦 Holdings", "📈 Analytics", "⏳ Orders", "🧾 History", "📓 Journal", "🏅 Badges"])
    with t1:
        if not pm.holdings:
            st.info("No open positions yet. Go to **Trade** to buy your first stock.")
        else:
            rows = []
            for t, p in pm.holdings.items():
                price = prices.get(t, p["avg_price"])
                rows.append({"Stock": short_name(t), "Ticker": t, "Qty": p["qty"], "Avg Cost": round(p["avg_price"], 2),
                             "Price": round(price, 2), "Value": round(price * p["qty"], 2),
                             "P&L": round((price - p["avg_price"]) * p["qty"], 2),
                             "P&L %": round((price - p["avg_price"]) / p["avg_price"] * 100 if p["avg_price"] else 0, 2)})
            st.dataframe(pd.DataFrame(rows).sort_values("Value", ascending=False), use_container_width=True, hide_index=True)
    with t2:
        if not pm.holdings:
            st.info("Buy some stocks to unlock analytics.")
        else:
            # Sector allocation
            sec = {}
            for t, p in pm.holdings.items():
                val = prices.get(t, p["avg_price"]) * p["qty"]
                sec[SECTOR_OF.get(t, "Other")] = sec.get(SECTOR_OF.get(t, "Other"), 0) + val
            ac1, ac2 = st.columns(2)
            with ac1:
                st.markdown("**Sector allocation**")
                fig = go.Figure(data=[go.Pie(labels=list(sec.keys()), values=list(sec.values()), hole=0.55,
                                             marker=dict(colors=["#4B6FFF", "#12B76A", "#F79009", "#9B51E0", "#0BA5EC", "#F04438", "#16B364", "#EE46BC", "#6172F3"]))])
                fig.update_layout(**PLOTLY_LAYOUT, height=300)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with ac2:
                st.markdown("**Highlights**")
                perf = []
                for t, p in pm.holdings.items():
                    price = prices.get(t, p["avg_price"])
                    plp = (price - p["avg_price"]) / p["avg_price"] * 100 if p["avg_price"] else 0
                    perf.append((t, plp))
                perf.sort(key=lambda x: -x[1])
                if perf:
                    st.markdown(f"🥇 Best: **{short_name(perf[0][0])}** {change_pill(perf[0][1])}", unsafe_allow_html=True)
                    st.markdown(f"🥉 Worst: **{short_name(perf[-1][0])}** {change_pill(perf[-1][1])}", unsafe_allow_html=True)
                tv = pm.total_value(prices)
                weights = [(prices.get(t, p["avg_price"]) * p["qty"]) / max(tv, 1) for t, p in pm.holdings.items()]
                hhi = sum(w * w for w in weights)
                div_score = max(0, min(100, round((1 - hhi) * 100)))
                st.markdown(f"🧺 Diversification score: **{div_score}/100** · {len(pm.holdings)} holdings · {len(sec)} sectors")
                if weights and max(weights) >= 0.5:
                    top = max(pm.holdings.items(), key=lambda kv: prices.get(kv[0], kv[1]['avg_price']) * kv[1]['qty'])
                    st.markdown(f"⚠️ {short_name(top[0])} is over half your portfolio — concentrated.")
    with t3:
        if not pm.orders and not pm.alerts:
            st.info("No pending limit orders or alerts. Set them on the **Trade** page.")
        if pm.orders:
            st.markdown("**Pending limit orders**")
            for o in pm.orders:
                cc = st.columns([3, 1])
                cc[0].markdown(f"{'🟢 Buy' if o['side']=='BUY' else '🔴 Sell'} **{o['qty']} × {short_name(o['ticker'])}** when price {'≤' if o['side']=='BUY' else '≥'} ₹{o['limit']:,.2f}")
                if cc[1].button("Cancel", key=f"co_{o['id']}"):
                    pm.cancel_order(o["id"])
                    save_store()
                    st.rerun()
        if pm.alerts:
            st.markdown("**Price alerts**")
            for a in pm.alerts:
                cc = st.columns([3, 1])
                status = "✅ triggered" if a["done"] else "⏳ waiting"
                cc[0].markdown(f"🔔 {short_name(a['ticker'])} {a['dir']} ₹{a['price']:,.2f} — {status}")
                if cc[1].button("Remove", key=f"ca_{a['id']}"):
                    pm.remove_alert(a["id"])
                    save_store()
                    st.rerun()
    with t4:
        if not pm.transactions:
            st.info("No trades yet.")
        else:
            df = pd.DataFrame(pm.transactions).sort_values("ts", ascending=False)
            df["ts"] = pd.to_datetime(df["ts"]).dt.strftime("%Y-%m-%d %H:%M")
            show = df[["ts", "ticker", "side", "qty", "price", "total", "realized_pl", "note"]].rename(
                columns={"ts": "Time", "ticker": "Ticker", "side": "Side", "qty": "Qty", "price": "Price",
                         "total": "Total", "realized_pl": "Realized P&L", "note": "Note"})
            st.dataframe(show, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Export CSV", show.to_csv(index=False).encode("utf-8"), "fictrade_transactions.csv", "text/csv")
    with t5:
        if not pm.d["journal"]:
            st.info("No journal entries yet. Add a note when you trade.")
        else:
            for j in reversed(pm.d["journal"][-30:]):
                card_open()
                st.markdown(f"**{short_name(j['ticker'])}** · <span class='muted mono' style='font-size:0.8rem'>{j['ts'][:16].replace('T',' ')}</span>", unsafe_allow_html=True)
                st.write(j["text"])
                card_close()
    with t6:
        cols = st.columns(4)
        for i, b in enumerate(pm.badge_details()):
            with cols[i % 4]:
                card_open()
                op = "1" if b["earned"] else "0.35"
                st.markdown(f"<div style='opacity:{op}'><div style='font-size:1.6rem'>{b['icon']}</div><b>{b['title']}</b><br><span class='muted' style='font-size:0.8rem'>{b['desc']}</span></div>", unsafe_allow_html=True)
                card_close()

    st.markdown("---")
    with st.expander("🗑️ Danger zone"):
        newcap = st.number_input("Reset with starting capital (₹)", min_value=1000.0, value=float(pm.starting_cash), step=50000.0)
        if st.button("Reset this portfolio"):
            pm.reset(newcap)
            save_store()
            st.success("Portfolio reset.")
            st.rerun()


def page_watchlist(pm, prices):
    hero("Watchlist", "Track companies and set price alerts.", "⭐")
    add = security_picker("Add a company", "watch_pick")
    if add and st.button("➕ Add to watchlist"):
        pm.add_watch(add)
        save_store()
        st.rerun()
    st.markdown("---")
    wl = pm.d["watchlist"]
    if not wl:
        st.info("Your watchlist is empty — add a company above.")
        return
    q = get_quotes_batch(tuple(wl))
    for t in wl:
        x = q.get(t)
        card_open()
        cols = st.columns([2, 1, 1, 1, 0.8])
        cols[0].markdown(f"**{short_name(t)}**  \n<span class='muted' style='font-size:0.8rem'>{t}</span>", unsafe_allow_html=True)
        if x and x.get("ok"):
            cols[1].markdown(f"<span class='mono'>{fmt_money(x['price'])}</span>", unsafe_allow_html=True)
            cols[2].markdown(change_pill(x["change_pct"]), unsafe_allow_html=True)
            cols[3].markdown(f"<span class='muted' style='font-size:0.78rem'>52W {fmt_money(x.get('year_high')) if x.get('year_high') else '—'} / {fmt_money(x.get('year_low')) if x.get('year_low') else '—'}</span>", unsafe_allow_html=True)
        else:
            cols[1].write("—")
            cols[2].write("No data")
        if cols[4].button("Remove", key=f"rm_{t}"):
            pm.remove_watch(t)
            save_store()
            st.rerun()
        card_close()


def page_charts(pm, prices):
    hero("Charts", "Full-screen candlestick analysis with indicators.", "📉")
    ticker = security_picker("Company / ticker", "chart_pick", st.session_state.get("chart_ticker", "RELIANCE.NS"))
    if not ticker:
        return
    st.session_state["chart_ticker"] = ticker
    c1, c2 = st.columns([1, 2])
    tf = c1.select_slider("Timeframe", options=list(PERIOD_INTERVAL.keys()), value="6M")
    overlays = c2.multiselect("Overlays", ["SMA 20", "SMA 50", "EMA 20", "VWAP", "Bollinger Bands"], default=["SMA 20", "SMA 50"])
    o1, o2, o3 = st.columns(3)
    show_rsi = o1.checkbox("RSI", value=True)
    show_macd = o2.checkbox("MACD", value=True)
    show_vol = o3.checkbox("Volume", value=True)
    period, interval = PERIOD_INTERVAL[tf]
    df = get_history(ticker, period, interval)
    qq = get_quote(ticker)
    if df.empty or "Close" not in df.columns:
        st.error(f"No chart data for '{ticker}'.")
        return
    if qq.get("ok"):
        h1, h2, h3 = st.columns([2, 1, 1])
        h1.markdown(f"### {qq['name']}  " + change_pill(qq["change_pct"]), unsafe_allow_html=True)
        h2.metric("Price", fmt_money(qq["price"]))
        try:
            h3.metric("RSI (14)", f"{float(rsi(df['Close']).iloc[-1]):.1f}")
        except Exception:
            h3.metric("RSI (14)", "—")
    st.plotly_chart(build_price_chart(df, ticker, overlays, show_rsi, show_macd, show_vol, height=620),
                    use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})


def page_learn(pm, prices):
    hero("Learn", "Every concept used in Fictrade, explained simply.", "🎓")
    topics = [
        ("💵 Market vs Limit order", "A market order buys/sells now at the current price. A limit order waits and only fills when the price reaches your target."),
        ("📊 Candlesticks", "Each candle shows the open, high, low and close for a period. Green = closed up, red = closed down."),
        ("📉 RSI", "A 0–100 momentum gauge. Above 70 = 'overbought', below 30 = 'oversold' — a clue, not a rule."),
        ("📈 Moving averages", "The average price over N days, smoothing noise so you can see the trend. EMA reacts faster than SMA."),
        ("🎯 MACD", "The gap between a fast and slow moving average — a momentum signal."),
        ("🎈 Bollinger Bands", "A band around a moving average; price near the top/bottom shows it's high/low vs recent swings."),
        ("💹 VWAP", "Volume-Weighted Average Price — the average price weighted by how much traded at each level. A common intraday benchmark."),
        ("🧺 Diversification", "Spreading money across sectors so one bad stock doesn't sink you. The diversification score rewards spreading out."),
        ("🔔 Alerts", "Get notified (when you next open the app) once a stock crosses a price you set."),
        ("📓 Why journal trades", "Writing down WHY you traded helps you learn from your own decisions over time."),
    ]
    for t, b in topics:
        with st.expander(t):
            st.write(b)
    st.info("🎮 Fictrade is a simulator. Prices are real; every trade is fictional play-money.")


def page_leaderboard(pm, prices):
    hero("Leaderboard", "Compare your portfolios, ranked by return.", "🏆")
    s = store()
    profs = s["profiles"]
    if len(profs) <= 1:
        st.info("Create more portfolios (sidebar) to compare strategies side by side.")
    all_t = set()
    for d in profs.values():
        all_t |= set(d["holdings"].keys())
    q = get_quotes_batch(tuple(all_t)) if all_t else {}
    rows = []
    for name, d in profs.items():
        m = Portfolio(d)
        lk = {t: x["price"] for t, x in q.items() if x and x.get("ok") and t in d["holdings"]}
        rows.append({"Portfolio": name, "Net Worth": round(m.total_value(lk), 2), "Return %": round(m.total_return_pct(lk), 2),
                     "Trades": len(m.transactions), "Level": m.level(), "Badges": len(d["badges"])})
    df = pd.DataFrame(rows).sort_values("Return %", ascending=False).reset_index(drop=True)
    medal = {0: "🥇", 1: "🥈", 2: "🥉"}
    df.insert(0, "Rank", [f"{medal.get(i,'')} #{i+1}" for i in range(len(df))])
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_settings(pm, prices):
    hero("Settings", "Manage portfolios and learn about this simulator.", "⚙️")
    st.markdown("### 💰 Change starting capital")
    card_open()
    st.write(f"Current portfolio **{pm.d['name']}** started with **{fmt_money(pm.starting_cash)}**.")
    newcap = st.number_input("New starting capital (₹) — resets this portfolio", min_value=1000.0, value=float(pm.starting_cash), step=50000.0)
    if st.button("Apply & reset portfolio"):
        pm.reset(newcap)
        save_store()
        st.success("Done.")
        st.rerun()
    card_close()
    st.markdown("### 👤 Your portfolios")
    card_open()
    s = store()
    for name in list(s["profiles"].keys()):
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"**{name}**")
        if c2.button("Switch", key=f"sw_{name}"):
            s["active_profile"] = name
            st.rerun()
        if c3.button("Delete", key=f"del_{name}"):
            if len(s["profiles"]) > 1:
                del s["profiles"][name]
                if s["active_profile"] == name:
                    s["active_profile"] = next(iter(s["profiles"]))
                save_store()
                st.rerun()
            else:
                st.error("Can't delete your only portfolio.")
    card_close()
    st.markdown("### ℹ️ About")
    card_open()
    st.markdown("- **Data:** real prices via Yahoo Finance (yfinance), typically delayed — not a live broker feed.\n"
                "- **Trading:** 100% fictional. No brokerage, no real orders, no real money.\n"
                "- **Saving:** everything is stored in **this browser** automatically — no login. Clearing browser data erases it.\n"
                "- **Limit orders & alerts** are checked whenever you open the app (there's no background server).\n"
                "- **Not investment advice.**")
    card_close()


# =============================================================================
# MAIN
# =============================================================================
def main():
    load_store()
    if not st.session_state.get("loaded"):
        return
    s = store()
    if not s.get("onboarded") or not s.get("profiles"):
        onboarding()
        save_store()
        return
    inject_css()
    pm, prices = render_sidebar()

    # Check pending limit orders + alerts on load
    notes = []
    if pm.orders or any(not a["done"] for a in pm.alerts):
        full = price_lookup_for(pm)
        notes += pm.check_orders(full)
        notes += pm.check_alerts(full)
        if notes:
            pm.snapshot(full, force=True)
            save_store()
            prices = price_lookup_for(pm)
    for m in notes:
        st.toast(m)
    if notes:
        st.success("  \n".join(notes))

    NAV = ["🏠 Dashboard", "💰 Trade", "📊 Portfolio", "⭐ Watchlist", "📉 Charts",
           "🎓 Learn", "🏆 Leaderboard", "⚙️ Settings"]
    page = st.radio("Navigate", NAV, horizontal=True, label_visibility="collapsed", key="nav")
    {
        "🏠 Dashboard": page_dashboard, "💰 Trade": page_trade, "📊 Portfolio": page_portfolio,
        "⭐ Watchlist": page_watchlist, "📉 Charts": page_charts, "🎓 Learn": page_learn,
        "🏆 Leaderboard": page_leaderboard, "⚙️ Settings": page_settings,
    }[page](pm, prices)
    save_store()


if __name__ == "__main__":
    main()
