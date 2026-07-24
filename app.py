"""
Fictrade — Fictional Trading Simulator with Real Market Data (INR edition)
==========================================================================
Practice trading with real prices (Yahoo Finance via yfinance) and fake money.
Everything saves in the browser (localStorage) — no login, no password.

NO real brokerage, NO real orders, NO real money — ever. Educational only.
Run locally:  streamlit run app.py
"""

from __future__ import annotations
import json
import time
import uuid
import hashlib
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Fictrade", page_icon="📈", layout="wide")

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

STORE_KEY = "fictrade_store_v2"

# =============================================================================
# THEME
# =============================================================================
PRIMARY = "#7C5CFF"
PRIMARY_2 = "#3EC6FF"
GREEN = "#00E39A"
RED = "#FF5C7A"
AMBER = "#FFC65C"
TEXT_MUTED = "#9AA3B8"
CARD = "rgba(255,255,255,0.045)"
CARD_BORDER = "rgba(255,255,255,0.09)"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#EAEBF3"),
    legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=10, r=10, t=40, b=10),
)


def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
    html, body, [class*="css"] {{ font-family:'Inter',-apple-system,sans-serif; }}
    .stApp {{
        background: radial-gradient(circle at 15% 0%, rgba(124,92,255,0.16), transparent 40%),
          radial-gradient(circle at 85% 15%, rgba(62,198,255,0.12), transparent 45%),
          linear-gradient(180deg,#06070D 0%,#0C0F1D 100%);
        color:#EAEBF3;
    }}
    /* Hide Streamlit chrome: menu, footer branding, toolbar, GitHub link, owner avatar/manage badge */
    #MainMenu {{display:none;}}
    footer {{display:none;}}
    [data-testid="stToolbar"] {{display:none !important;}}
    [data-testid="stDecoration"] {{display:none !important;}}
    [data-testid="stStatusWidget"] {{display:none !important;}}
    .stDeployButton {{display:none !important;}}
    [data-testid="stHeader"] {{background:transparent;}}
    a[href*="github.com"] {{display:none !important;}}
    section[data-testid="stSidebar"] {{ background:linear-gradient(180deg,#0A0C18,#090A14); border-right:1px solid {CARD_BORDER}; }}
    section[data-testid="stSidebar"] * {{ color:#D6D9E8 !important; }}
    h1,h2,h3 {{ font-weight:800 !important; letter-spacing:-0.02em; }}
    h1 {{ color:#fff !important; }}
    div[data-testid="stMetric"] {{ background:{CARD}; border:1px solid {CARD_BORDER}; border-radius:16px; padding:14px 18px 10px; backdrop-filter:blur(6px); }}
    div[data-testid="stMetricLabel"] {{ color:{TEXT_MUTED} !important; font-weight:600; text-transform:uppercase; font-size:0.72rem !important; letter-spacing:0.06em; }}
    div[data-testid="stMetricValue"] {{ font-family:'JetBrains Mono',monospace; font-weight:700 !important; }}
    .stButton>button, .stFormSubmitButton>button {{
        background:linear-gradient(135deg,{PRIMARY},{PRIMARY_2}); color:#fff !important; border:none;
        border-radius:12px; font-weight:700; padding:0.55rem 1.2rem; transition:transform .12s,box-shadow .12s;
        box-shadow:0 4px 18px rgba(124,92,255,0.28); }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{ transform:translateY(-1px); box-shadow:0 8px 24px rgba(124,92,255,0.4); }}
    button[data-baseweb="tab"] {{ font-weight:600; color:{TEXT_MUTED} !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color:#fff !important; }}
    div[data-baseweb="tab-highlight"] {{ background-color:{PRIMARY} !important; }}
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"]>div {{
        background:{CARD} !important; border:1px solid {CARD_BORDER} !important; border-radius:10px !important; color:#EAEBF3 !important; }}
    .hero {{ padding:28px 30px; border-radius:22px; background:linear-gradient(120deg,rgba(124,92,255,0.22),rgba(62,198,255,0.10)); border:1px solid {CARD_BORDER}; margin-bottom:22px; }}
    .hero h1 {{ margin:0 0 4px 0; font-size:2rem; }}
    .hero p {{ margin:0; color:{TEXT_MUTED}; font-size:0.98rem; }}
    .glass-card {{ background:{CARD}; border:1px solid {CARD_BORDER}; border-radius:18px; padding:18px 20px; backdrop-filter:blur(6px); margin-bottom:14px; }}
    .pill {{ display:inline-block; padding:3px 12px; border-radius:999px; font-size:0.74rem; font-weight:700; }}
    .pill-green {{ background:rgba(0,227,154,0.15); color:{GREEN}; border:1px solid rgba(0,227,154,0.35); }}
    .pill-red {{ background:rgba(255,92,122,0.15); color:{RED}; border:1px solid rgba(255,92,122,0.35); }}
    .pill-amber {{ background:rgba(255,198,92,0.15); color:{AMBER}; border:1px solid rgba(255,198,92,0.35); }}
    .pill-violet {{ background:rgba(124,92,255,0.18); color:#C9BBFF; border:1px solid rgba(124,92,255,0.4); }}
    .badge {{ display:inline-flex; align-items:center; gap:6px; background:linear-gradient(135deg,rgba(124,92,255,0.25),rgba(62,198,255,0.18)); border:1px solid rgba(124,92,255,0.4); border-radius:999px; padding:6px 14px; font-size:0.8rem; font-weight:700; margin:3px 6px 3px 0; }}
    .mono {{ font-family:'JetBrains Mono',monospace; }}
    .ticker-tape {{ white-space:nowrap; overflow-x:auto; padding-bottom:6px; }}
    .ticker-item {{ display:inline-block; background:{CARD}; border:1px solid {CARD_BORDER}; border-radius:12px; padding:10px 16px; margin-right:10px; }}
    .xp-track {{ width:100%; height:10px; border-radius:999px; background:rgba(255,255,255,0.08); overflow:hidden; border:1px solid {CARD_BORDER}; }}
    .xp-fill {{ height:100%; background:linear-gradient(90deg,{PRIMARY},{PRIMARY_2}); }}
    hr {{ border-color:{CARD_BORDER} !important; }}
    a {{ color:{PRIMARY_2} !important; }}
    </style>
    """, unsafe_allow_html=True)


def hero(title, subtitle="", icon="📈"):
    st.markdown(f'<div class="hero"><h1>{icon} {title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def pill(text, kind="violet"):
    return f'<span class="pill pill-{kind}">{text}</span>'


def change_pill(pct):
    if pct is None:
        return pill("N/A", "amber")
    kind = "green" if pct >= 0 else "red"
    return pill(f"{'▲' if pct>=0 else '▼'} {pct:+.2f}%", kind)


def badge(text, icon="🏅"):
    return f'<span class="badge">{icon} {text}</span>'


def card_open():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def xp_bar(pct):
    pct = max(0, min(100, pct))
    st.markdown(f'<div class="xp-track"><div class="xp-fill" style="width:{pct}%;"></div></div>', unsafe_allow_html=True)


def fmt_money(v, compact=False):
    """Everything is shown in Indian Rupees."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if compact:
        a = abs(v)
        if a >= 1e7:
            return f"₹{v/1e7:.2f} Cr"
        if a >= 1e5:
            return f"₹{v/1e5:.2f} L"
        if a >= 1e3:
            return f"₹{v/1e3:.1f}K"
    return f"₹{v:,.2f}"


# =============================================================================
# SECURITIES (for company-name autocomplete). name -> yfinance ticker.
# =============================================================================
SECURITIES = [
    # ---- Indian (NSE) ----
    ("Reliance Industries", "RELIANCE.NS"), ("Tata Consultancy Services (TCS)", "TCS.NS"),
    ("Infosys", "INFY.NS"), ("HDFC Bank", "HDFCBANK.NS"), ("ICICI Bank", "ICICIBANK.NS"),
    ("State Bank of India (SBI)", "SBIN.NS"), ("ITC", "ITC.NS"), ("Wipro", "WIPRO.NS"),
    ("Bajaj Finance", "BAJFINANCE.NS"), ("Adani Enterprises", "ADANIENT.NS"),
    ("Tata Motors", "TATAMOTORS.NS"), ("Hindustan Unilever (HUL)", "HINDUNILVR.NS"),
    ("Larsen & Toubro (L&T)", "LT.NS"), ("Axis Bank", "AXISBANK.NS"),
    ("Kotak Mahindra Bank", "KOTAKBANK.NS"), ("Bharti Airtel", "BHARTIARTL.NS"),
    ("Asian Paints", "ASIANPAINT.NS"), ("Maruti Suzuki", "MARUTI.NS"),
    ("Sun Pharma", "SUNPHARMA.NS"), ("Titan Company", "TITAN.NS"),
    ("Nestle India", "NESTLEIND.NS"), ("HCL Technologies", "HCLTECH.NS"),
    ("Tata Steel", "TATASTEEL.NS"), ("Power Grid", "POWERGRID.NS"), ("NTPC", "NTPC.NS"),
    ("ONGC", "ONGC.NS"), ("Coal India", "COALINDIA.NS"), ("JSW Steel", "JSWSTEEL.NS"),
    ("Adani Ports", "ADANIPORTS.NS"), ("UltraTech Cement", "ULTRACEMCO.NS"),
    ("Bajaj Finserv", "BAJAJFINSV.NS"), ("Tech Mahindra", "TECHM.NS"), ("Grasim", "GRASIM.NS"),
    ("Hindalco", "HINDALCO.NS"), ("Dr Reddy's Labs", "DRREDDY.NS"), ("Cipla", "CIPLA.NS"),
    ("Divi's Laboratories", "DIVISLAB.NS"), ("Britannia", "BRITANNIA.NS"),
    ("Eicher Motors", "EICHERMOT.NS"), ("Hero MotoCorp", "HEROMOTOCO.NS"),
    ("Bajaj Auto", "BAJAJ-AUTO.NS"), ("IndusInd Bank", "INDUSINDBK.NS"),
    ("SBI Life Insurance", "SBILIFE.NS"), ("HDFC Life Insurance", "HDFCLIFE.NS"),
    ("Apollo Hospitals", "APOLLOHOSP.NS"), ("Tata Consumer Products", "TATACONSUM.NS"),
    ("Adani Green Energy", "ADANIGREEN.NS"), ("Adani Power", "ADANIPOWER.NS"),
    ("Avenue Supermarts (DMart)", "DMART.NS"), ("Pidilite Industries", "PIDILITIND.NS"),
    ("Paytm (One97)", "PAYTM.NS"), ("Nykaa (FSN E-Commerce)", "NYKAA.NS"),
    ("IRCTC", "IRCTC.NS"), ("Vedanta", "VEDL.NS"), ("Life Insurance Corp (LIC)", "LICI.NS"),
    ("Bank of Baroda", "BANKBARODA.NS"), ("Punjab National Bank (PNB)", "PNB.NS"),
    ("GAIL India", "GAIL.NS"), ("BPCL", "BPCL.NS"), ("Indian Oil (IOC)", "IOC.NS"),
    ("Tata Power", "TATAPOWER.NS"), ("Ambuja Cements", "AMBUJACEM.NS"),
    ("Shree Cement", "SHREECEM.NS"), ("DLF", "DLF.NS"), ("Havells India", "HAVELLS.NS"),
    ("Dabur India", "DABUR.NS"), ("Godrej Consumer", "GODREJCP.NS"), ("Siemens India", "SIEMENS.NS"),
    ("Bosch", "BOSCHLTD.NS"), ("Berger Paints", "BERGEPAINT.NS"), ("Marico", "MARICO.NS"),
    ("Colgate-Palmolive India", "COLPAL.NS"), ("InterGlobe Aviation (IndiGo)", "INDIGO.NS"),
    ("Bharat Electronics (BEL)", "BEL.NS"), ("Bharat Forge", "BHARATFORG.NS"),
    ("Page Industries", "PAGEIND.NS"), ("SRF", "SRF.NS"), ("Trent", "TRENT.NS"),
    ("Tata Elxsi", "TATAELXSI.NS"), ("Mphasis", "MPHASIS.NS"), ("LTIMindtree", "LTIM.NS"),
    ("Persistent Systems", "PERSISTENT.NS"), ("Yes Bank", "YESBANK.NS"),
    ("IDFC First Bank", "IDFCFIRSTB.NS"), ("Federal Bank", "FEDERALBNK.NS"),
    ("Zomato / Eternal", "ETERNAL.NS"),
    # ---- US ----
    ("Apple", "AAPL"), ("Microsoft", "MSFT"), ("Alphabet (Google)", "GOOGL"),
    ("Amazon", "AMZN"), ("Nvidia", "NVDA"), ("Tesla", "TSLA"), ("Meta (Facebook)", "META"),
    ("Netflix", "NFLX"), ("JPMorgan Chase", "JPM"), ("Visa", "V"), ("Walt Disney", "DIS"),
    ("AMD", "AMD"), ("Intel", "INTC"), ("Coca-Cola", "KO"), ("McDonald's", "MCD"),
    ("Nike", "NKE"), ("Walmart", "WMT"), ("Adobe", "ADBE"), ("Salesforce", "CRM"),
    ("Oracle", "ORCL"), ("IBM", "IBM"), ("Uber", "UBER"), ("Starbucks", "SBUX"),
    ("Pfizer", "PFE"), ("Boeing", "BA"),
]
POPULAR_IN = [t for n, t in SECURITIES if t.endswith(".NS")][:12]
LABELS = [f"{n}  ·  {t}" for n, t in SECURITIES]
LABEL_TO_TICKER = {f"{n}  ·  {t}": t for n, t in SECURITIES}
TICKER_TO_NAME = {t: n for n, t in SECURITIES}
PERIOD_INTERVAL = {"1D": ("1d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "1d"),
                   "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "5Y": ("5y", "1wk"), "MAX": ("max", "1mo")}


def security_picker(label, key, default_ticker=None):
    """A type-to-search company picker + manual ticker fallback. Returns ticker or None."""
    placeholder = "🔍 Type a company name, e.g. Tata, Reliance, Infosys…"
    opts = [placeholder] + LABELS
    idx = 0
    if default_ticker and default_ticker in TICKER_TO_NAME:
        lbl = f"{TICKER_TO_NAME[default_ticker]}  ·  {default_ticker}"
        if lbl in opts:
            idx = opts.index(lbl)
    sel = st.selectbox(label, opts, index=idx, key=key)
    ticker = LABEL_TO_TICKER.get(sel)
    with st.expander("Can't find it? Enter any ticker manually"):
        manual = st.text_input("Ticker (Indian stocks end in .NS, e.g. TATAMOTORS.NS)",
                               key=key + "_manual").strip().upper()
        if manual:
            ticker = manual
    return ticker


# =============================================================================
# DATA (yfinance, defensive)
# =============================================================================
def _safe_get(d, *keys, default=None):
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
        date_col = "Datetime" if "Datetime" in df.columns else "Date"
        return df.rename(columns={date_col: "Date"})
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=45, show_spinner=False)
def get_quote(ticker):
    out = {"ticker": ticker, "ok": False, "name": TICKER_TO_NAME.get(ticker, ticker), "price": None,
           "change_pct": None, "day_high": None, "day_low": None, "market_cap": None,
           "currency": "INR", "year_high": None, "year_low": None}
    if yf is None:
        return out
    try:
        t = yf.Ticker(ticker)
        try:
            fi = dict(t.fast_info)
        except Exception:
            fi = {}
        price = _safe_get(fi, "lastPrice", "last_price")
        prev = _safe_get(fi, "previousClose", "previous_close")
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
        out.update({"ok": True, "price": float(price), "change_pct": float((price - prev) / prev * 100) if prev else 0.0,
                    "day_high": _safe_get(fi, "dayHigh", "day_high"), "day_low": _safe_get(fi, "dayLow", "day_low"),
                    "market_cap": _safe_get(fi, "marketCap", "market_cap"),
                    "year_high": _safe_get(fi, "yearHigh", "year_high"), "year_low": _safe_get(fi, "yearLow", "year_low"),
                    "currency": _safe_get(fi, "currency", default="INR")})
        try:
            info = t.get_info()
            out["name"] = TICKER_TO_NAME.get(ticker) or info.get("shortName") or info.get("longName") or ticker
            if out["market_cap"] is None:
                out["market_cap"] = info.get("marketCap")
        except Exception:
            pass
        return out
    except Exception as e:
        out["error"] = str(e)
        return out


@st.cache_data(ttl=45, show_spinner=False)
def get_quotes_batch(tickers):
    return {t: get_quote(t) for t in tickers}


@st.cache_data(ttl=300, show_spinner=False)
def get_news(ticker, limit=10):
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
    sl = ema(ml, signal)
    return ml, sl, ml - sl


def bollinger(s, w=20, n=2.0):
    m = sma(s, w)
    sd = s.rolling(window=w, min_periods=max(2, w // 3)).std()
    return m + n * sd, m, m - n * sd


# =============================================================================
# NOTES (rule-based, no AI)
# =============================================================================
def risk_notes(weights):
    notes = []
    if not weights:
        return ["Your portfolio is currently all cash — no market exposure yet."]
    weights = sorted(weights, key=lambda x: -x[1])
    top_t, top_w = weights[0]
    if top_w >= 50:
        notes.append(f"{top_t} is {top_w:.0f}% of your invested money — a single bad day there will dominate your results.")
    elif top_w >= 30:
        notes.append(f"{top_t} is your biggest position at {top_w:.0f}% of holdings.")
    if len(weights) == 1:
        notes.append("You hold only one stock. Spreading across a few reduces single-stock risk.")
    if not notes:
        notes.append("Your positions look reasonably balanced.")
    return notes


POS_WORDS = {"beat", "beats", "surge", "surges", "soar", "rally", "record", "growth", "upgrade",
             "profit", "gain", "gains", "strong", "bullish", "approval", "buyback", "dividend",
             "jump", "jumps", "boom", "wins", "exceeds"}
NEG_WORDS = {"miss", "misses", "plunge", "slump", "fall", "falls", "downgrade", "loss", "losses",
             "weak", "bearish", "layoff", "lawsuit", "probe", "recall", "cut", "cuts", "warning",
             "warns", "decline", "drop", "drops", "fraud", "concern", "risk"}


def headline_tag(title):
    w = {x.strip(".,!?:;()'\"").lower() for x in title.split()}
    p, n = len(w & POS_WORDS), len(w & NEG_WORDS)
    return 1 if p > n else (-1 if n > p else 0)


# =============================================================================
# PORTFOLIO
# =============================================================================
BADGE_DEFS = [
    ("first_trade", "🎬", "First Trade", "Placed your first order."),
    ("five_holdings", "🧺", "Diversifier", "Held 5+ different stocks at once."),
    ("ten_trades", "🔟", "Getting Serious", "Placed 10 trades."),
    ("profit_10", "🌱", "In The Green", "Portfolio return crossed +10%."),
    ("profit_25", "🚀", "On A Roll", "Portfolio return crossed +25%."),
    ("first_loss_take", "🩹", "Cut The Loss", "Sold a losing position."),
    ("journaled", "📓", "Reflective Trader", "Wrote a trade journal note."),
    ("concentrated", "⚠️", "High Roller", "Put 50%+ into one stock."),
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def new_portfolio(name, starting_cash):
    return {"name": name, "currency": "INR", "starting_cash": float(starting_cash), "cash": float(starting_cash),
            "holdings": {}, "transactions": [], "net_worth_history": [{"ts": _now(), "value": float(starting_cash)}],
            "journal": [], "badges": [], "watchlist": []}


class Portfolio:
    def __init__(self, d):
        self.d = d

    @property
    def cash(self):
        return self.d["cash"]

    @property
    def holdings(self):
        return self.d["holdings"]

    @property
    def transactions(self):
        return self.d["transactions"]

    @property
    def starting_cash(self):
        return self.d["starting_cash"]

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
            return False, "Not enough virtual cash for this order."
        self.d["cash"] -= cost
        pos = self.holdings.get(ticker, {"qty": 0, "avg_price": 0.0})
        nq = pos["qty"] + qty
        self.holdings[ticker] = {"qty": nq, "avg_price": ((pos["qty"] * pos["avg_price"]) + cost) / nq}
        self._log(ticker, "BUY", qty, price, note)
        return True, f"Bought {qty} × {ticker} @ ₹{price:,.2f}"

    def sell(self, ticker, qty, price, note=""):
        pos = self.holdings.get(ticker)
        if not pos or pos["qty"] < qty or qty <= 0 or not price or price <= 0:
            return False, "You don't hold enough shares to sell that."
        realized = (price - pos["avg_price"]) * qty
        self.d["cash"] += qty * price
        rem = pos["qty"] - qty
        if rem <= 0:
            del self.holdings[ticker]
        else:
            self.holdings[ticker] = {"qty": rem, "avg_price": pos["avg_price"]}
        self._log(ticker, "SELL", qty, price, note, realized)
        return True, f"Sold {qty} × {ticker} @ ₹{price:,.2f} ({'+' if realized>=0 else ''}₹{realized:,.2f} P&L)"

    def _log(self, ticker, side, qty, price, note="", realized=None):
        self.transactions.append({"id": uuid.uuid4().hex[:10], "ts": _now(), "ticker": ticker, "side": side,
                                  "qty": qty, "price": price, "total": qty * price, "note": note, "realized_pl": realized})

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
        newly = []

        def award(b):
            if b not in earned:
                earned.add(b)
                newly.append(b)
        n = len(self.transactions)
        if n >= 1:
            award("first_trade")
        if n >= 10:
            award("ten_trades")
        if len(self.holdings) >= 5:
            award("five_holdings")
        if any(t.get("side") == "SELL" and (t.get("realized_pl") or 0) < 0 for t in self.transactions):
            award("first_loss_take")
        if self.d["journal"]:
            award("journaled")
        r = self.total_return_pct(prices)
        if r >= 10:
            award("profit_10")
        if r >= 25:
            award("profit_25")
        tv = self.total_value(prices)
        for t, p in self.holdings.items():
            if (prices.get(t, p["avg_price"]) * p["qty"]) / max(tv, 1) >= 0.5:
                award("concentrated")
                break
        self.d["badges"] = sorted(earned)
        return newly

    def badge_details(self):
        e = set(self.d["badges"])
        return [{"id": b, "icon": i, "title": t, "desc": d, "earned": b in e} for b, i, t, d in BADGE_DEFS]

    def reset(self, starting_cash=None):
        sc = starting_cash if starting_cash else self.starting_cash
        self.d.update(new_portfolio(self.d["name"], sc))


# =============================================================================
# STORAGE (browser localStorage, NO login/password)
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
        st.session_state["saved_hash"] = _store_hash()
        return
    # No value yet: give localStorage a few reruns to respond before assuming empty.
    tries = st.session_state.get("load_tries", 0)
    if LS_OK and tries < 3:
        st.session_state["load_tries"] = tries + 1
        time.sleep(0.4)
        st.rerun()
    st.session_state.setdefault("store", default_store())
    st.session_state["loaded"] = True
    st.session_state["saved_hash"] = _store_hash()


def _store_hash():
    return hashlib.md5(json.dumps(st.session_state.get("store", {}), sort_keys=True).encode()).hexdigest()


def save_store():
    if not LS_OK:
        return
    h = _store_hash()
    if st.session_state.get("saved_hash") != h:
        st.session_state["ls_n"] = st.session_state.get("ls_n", 0) + 1
        try:
            _LS.setItem(STORE_KEY, json.dumps(st.session_state["store"]), key=f"set_{st.session_state['ls_n']}")
        except Exception:
            pass
        st.session_state["saved_hash"] = h


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


def price_lookup_for(pm):
    ts = tuple(pm.holdings.keys())
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
                                 help="This is your total investable capital. Default is ₹10,00,000 (10 lakh).")
        st.caption("You can reset or change this anytime from Settings.")
        if st.form_submit_button("🚀 Start trading", use_container_width=True):
            nm = name.strip() or "My Portfolio"
            prof = new_portfolio(nm, amount)
            prof["watchlist"] = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
            store()["profiles"] = {nm: prof}
            store()["active_profile"] = nm
            store()["onboarded"] = True
            save_store()
            st.rerun()
    card_close()
    st.caption("⚠️ Simulated trading only — real market prices, but no real money, orders, or broker.")


# =============================================================================
# SIDEBAR
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
    st.sidebar.markdown("---")

    page = st.sidebar.radio("Go to", ["🏠 Dashboard", "💰 Trade", "📊 Portfolio", "⭐ Watchlist",
                                      "📉 Charts", "📰 News", "🎓 Learn", "🏆 Leaderboard", "⚙️ Settings"],
                            label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Simulated — no real orders or money.")
    return pm, prices, page


# =============================================================================
# PAGES
# =============================================================================
def page_dashboard(pm, prices):
    hero(f"{pm.d['name']}", "Your practice portfolio at a glance. Prices are real (Yahoo Finance); trades are fictional.", "🏠")

    invested = pm.invested_cost()
    holdings_val = pm.holdings_value(prices)
    total = pm.total_value(prices)
    ret = pm.total_return_pct(prices)

    st.markdown("#### 💰 Your money")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investable capital", fmt_money(pm.starting_cash, compact=True), help="What you started with.")
    c2.metric("Invested (at cost)", fmt_money(invested, compact=True), help="What you paid for the stocks you hold.")
    c3.metric("Current holdings value", fmt_money(holdings_val, compact=True),
              f"{((holdings_val-invested)/invested*100) if invested else 0:+.2f}%", help="What those stocks are worth now.")
    c4.metric("Cash left to invest", fmt_money(pm.cash, compact=True), help="Uninvested virtual cash.")

    st.write("")
    d1, d2 = st.columns([1, 1])
    d1.metric("Total net worth", fmt_money(total, compact=True), f"{ret:+.2f}% all-time")
    used_pct = (invested / pm.starting_cash * 100) if pm.starting_cash else 0
    d2.metric("Capital deployed", f"{min(used_pct,100):.1f}%", help="Share of your investable capital currently in the market.")

    st.write("")
    left, right = st.columns([2, 1])
    with left:
        st.markdown("#### Net worth over time")
        h = pm.d["net_worth_history"]
        if len(h) >= 2:
            df = pd.DataFrame(h)
            df["ts"] = pd.to_datetime(df["ts"])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["ts"], y=df["value"], mode="lines", fill="tozeroy",
                                     line=dict(color=PRIMARY_2, width=3), fillcolor="rgba(62,198,255,0.12)"))
            fig.add_hline(y=pm.starting_cash, line_dash="dot", line_color="rgba(255,255,255,0.3)")
            fig.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
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

    st.markdown("#### 🌍 Market pulse")
    q = get_quotes_batch(tuple(POPULAR_IN))
    tape = '<div class="ticker-tape">'
    for t in POPULAR_IN:
        x = q.get(t)
        if x and x.get("ok"):
            tape += f'<div class="ticker-item"><b>{TICKER_TO_NAME.get(t,t).split("(")[0].strip()}</b><br><span class="mono">{fmt_money(x["price"])}</span> {change_pill(x["change_pct"])}</div>'
    tape += "</div>"
    st.markdown(tape, unsafe_allow_html=True)


def page_trade(pm, prices):
    hero("Trade", "Search a company by name, see its live price, and place a fictional order.", "💰")
    ticker = security_picker("Company / ticker", "trade_pick", st.session_state.get("trade_ticker"))
    if not ticker:
        st.info("Start typing a company name above — e.g. 'Tata', 'Reliance', 'Infosys'.")
        return
    st.session_state["trade_ticker"] = ticker
    with st.spinner(f"Fetching live data for {ticker}…"):
        qq = get_quote(ticker)
    if not qq.get("ok"):
        st.error(f"Couldn't fetch data for '{ticker}'. If you typed it manually, Indian stocks need a '.NS' suffix "
                 f"(e.g. TATAMOTORS.NS).")
        return

    a, b, c, d, e = st.columns([1.7, 1, 1, 1, 1])
    a.markdown(f"### {qq['name']}")
    a.markdown(f"`{ticker}` &nbsp; " + change_pill(qq["change_pct"]), unsafe_allow_html=True)
    b.metric("Price", fmt_money(qq["price"]))
    c.metric("Day High", fmt_money(qq.get("day_high")) if qq.get("day_high") else "—")
    d.metric("Day Low", fmt_money(qq.get("day_low")) if qq.get("day_low") else "—")
    e.metric("Mkt Cap", fmt_money(qq.get("market_cap"), compact=True) if qq.get("market_cap") else "—")

    h = get_history(ticker, "3mo", "1d")
    if not h.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=h["Date"], y=h["Close"], mode="lines", line=dict(color=PRIMARY, width=2.5),
                                 fill="tozeroy", fillcolor="rgba(124,92,255,0.10)"))
        fig.update_layout(**PLOTLY_LAYOUT, height=220)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")
    existing = pm.holdings.get(ticker)
    o1, o2 = st.columns(2)
    with o1:
        card_open()
        st.markdown("#### 🟢 Buy")
        maxq = int(pm.cash // qq["price"]) if qq["price"] else 0
        with st.form("buy"):
            qty = st.number_input("Quantity", min_value=1, value=min(10, max(1, maxq)) or 1, step=1)
            st.caption(f"Cost: **{fmt_money(qty*qq['price'])}** · Cash available: {fmt_money(pm.cash)} · Max you can afford: {maxq}")
            note = st.text_input("Why this trade? (optional note)")
            if st.form_submit_button("Place Buy Order", use_container_width=True):
                ok, msg = pm.buy(ticker, int(qty), qq["price"], note)
                if ok:
                    if note:
                        pm.add_journal(ticker, note)
                    pm.snapshot({**prices, ticker: qq["price"]}, force=True)
                    for bid in pm.check_badges({**prices, ticker: qq["price"]}):
                        st.toast(f"🏅 Badge unlocked: {dict((x['id'],x) for x in pm.badge_details())[bid]['title']}", icon="🏅")
                    save_store()
                    st.success(msg + " — saved to your portfolio.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)
        card_close()
    with o2:
        card_open()
        st.markdown("#### 🔴 Sell")
        if existing:
            st.caption(f"You hold **{existing['qty']}** @ avg {fmt_money(existing['avg_price'])}")
            st.markdown(change_pill((qq["price"] - existing["avg_price"]) / existing["avg_price"] * 100), unsafe_allow_html=True)
            with st.form("sell"):
                qty = st.number_input("Quantity", min_value=1, max_value=int(existing["qty"]), value=int(existing["qty"]), step=1)
                st.caption(f"Proceeds: **{fmt_money(qty*qq['price'])}**")
                note = st.text_input("Reason for selling (optional)")
                if st.form_submit_button("Place Sell Order", use_container_width=True):
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
    inw = ticker in pm.d["watchlist"]
    if st.button("⭐ Remove from Watchlist" if inw else "☆ Add to Watchlist"):
        pm.remove_watch(ticker) if inw else pm.add_watch(ticker)
        save_store()
        st.rerun()


def page_portfolio(pm, prices):
    hero("Portfolio", "Your holdings, performance, and full trade history.", "📊")
    invested = pm.invested_cost()
    holdings_val = pm.holdings_value(prices)
    realized = sum(t.get("realized_pl") or 0 for t in pm.transactions)
    unreal = holdings_val - invested
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net worth", fmt_money(pm.total_value(prices), compact=True), f"{pm.total_return_pct(prices):+.2f}%")
    c2.metric("Invested (cost)", fmt_money(invested, compact=True))
    c3.metric("Unrealized P&L", fmt_money(unreal, compact=True))
    c4.metric("Realized P&L", fmt_money(realized, compact=True))

    t1, t2, t3, t4, t5 = st.tabs(["📦 Holdings", "🥧 Allocation", "🧾 Transactions", "📓 Journal", "🏅 Badges"])
    with t1:
        if not pm.holdings:
            st.info("No open positions yet. Go to **Trade** to buy your first stock.")
        else:
            rows = []
            for t, p in pm.holdings.items():
                price = prices.get(t, p["avg_price"])
                rows.append({"Stock": TICKER_TO_NAME.get(t, t), "Ticker": t, "Qty": p["qty"],
                             "Avg Cost": round(p["avg_price"], 2), "Price": round(price, 2),
                             "Value": round(price * p["qty"], 2), "P&L": round((price - p["avg_price"]) * p["qty"], 2),
                             "P&L %": round((price - p["avg_price"]) / p["avg_price"] * 100 if p["avg_price"] else 0, 2)})
            df = pd.DataFrame(rows).sort_values("Value", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown("##### 📋 Notes")
            tv = pm.total_value(prices)
            w = [(TICKER_TO_NAME.get(t, t), (prices.get(t, p["avg_price"]) * p["qty"]) / max(tv, 1) * 100) for t, p in pm.holdings.items()]
            for n in risk_notes(w):
                st.markdown(f"- {n}")
    with t2:
        if not pm.holdings:
            st.info("Nothing to allocate yet.")
        else:
            labels, values = [], []
            for t, p in pm.holdings.items():
                labels.append(TICKER_TO_NAME.get(t, t).split("(")[0].strip())
                values.append(prices.get(t, p["avg_price"]) * p["qty"])
            if pm.cash > 0:
                labels.append("Cash")
                values.append(pm.cash)
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.55,
                                         marker=dict(colors=["#7C5CFF", "#3EC6FF", "#00E39A", "#FFC65C", "#FF5C7A", "#C084FC", "#38BDF8", "#4ADE80"]))])
            fig.update_layout(**PLOTLY_LAYOUT, height=380)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with t3:
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
    with t4:
        if not pm.d["journal"]:
            st.info("No journal entries yet. Add a note when you trade.")
        else:
            for j in reversed(pm.d["journal"][-30:]):
                card_open()
                st.markdown(f"**{TICKER_TO_NAME.get(j['ticker'], j['ticker'])}** · <span class='mono' style='color:#9AA3B8'>{j['ts'][:16].replace('T',' ')}</span>", unsafe_allow_html=True)
                st.write(j["text"])
                card_close()
    with t5:
        cols = st.columns(3)
        for i, b in enumerate(pm.badge_details()):
            with cols[i % 3]:
                card_open()
                op = "1" if b["earned"] else "0.35"
                st.markdown(f"<div style='opacity:{op}'><div style='font-size:2rem'>{b['icon']}</div><b>{b['title']}</b><br><span style='color:#9AA3B8;font-size:0.85rem'>{b['desc']}</span></div>", unsafe_allow_html=True)
                card_close()

    st.markdown("---")
    with st.expander("🗑️ Danger zone"):
        st.warning("Resets this portfolio (cash, holdings, trades, journal, badges).")
        newcap = st.number_input("Reset with starting capital (₹)", min_value=1000.0, value=float(pm.starting_cash), step=50000.0)
        if st.button("Reset this portfolio"):
            pm.reset(newcap)
            save_store()
            st.success("Portfolio reset.")
            st.rerun()


def page_watchlist(pm, prices):
    hero("Watchlist", "Track companies you're interested in without buying them.", "⭐")
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
        cols[0].markdown(f"**{TICKER_TO_NAME.get(t,t)}**  \n<span style='color:#9AA3B8;font-size:0.8rem'>{t}</span>", unsafe_allow_html=True)
        if x and x.get("ok"):
            cols[1].markdown(f"<span class='mono'>{fmt_money(x['price'])}</span>", unsafe_allow_html=True)
            cols[2].markdown(change_pill(x["change_pct"]), unsafe_allow_html=True)
            cols[3].markdown(f"52W H/L<br><span class='mono' style='font-size:0.8rem'>{fmt_money(x.get('year_high')) if x.get('year_high') else '—'} / {fmt_money(x.get('year_low')) if x.get('year_low') else '—'}</span>", unsafe_allow_html=True)
        else:
            cols[1].write("—")
            cols[2].write("No data")
        if cols[4].button("Remove", key=f"rm_{t}"):
            pm.remove_watch(t)
            save_store()
            st.rerun()
        card_close()


def page_charts(pm, prices):
    hero("Charts", "Real price history with candlesticks, moving averages, Bollinger Bands, RSI & MACD.", "📉")
    ticker = security_picker("Company / ticker", "chart_pick", st.session_state.get("chart_ticker", "RELIANCE.NS"))
    if not ticker:
        st.info("Pick a company above to chart it.")
        return
    st.session_state["chart_ticker"] = ticker
    c1, c2 = st.columns([1, 2])
    tf = c1.select_slider("Timeframe", options=list(PERIOD_INTERVAL.keys()), value="6M")
    overlays = c2.multiselect("Overlays", ["SMA 20", "SMA 50", "Bollinger Bands"], default=["SMA 20", "SMA 50"])
    show_rsi = st.checkbox("RSI panel", value=True)
    show_macd = st.checkbox("MACD panel", value=True)

    period, interval = PERIOD_INTERVAL[tf]
    with st.spinner("Loading price history…"):
        df = get_history(ticker, period, interval)
        qq = get_quote(ticker)
    if df.empty or "Close" not in df.columns:
        st.error(f"No chart data for '{ticker}'. Check the ticker (Indian stocks need '.NS').")
        return

    if qq.get("ok"):
        h1, h2, h3 = st.columns([2, 1, 1])
        h1.markdown(f"### {qq['name']}  " + change_pill(qq["change_pct"]), unsafe_allow_html=True)
        h2.metric("Price", fmt_money(qq["price"]))
        try:
            rv = float(rsi(df["Close"]).iloc[-1])
        except Exception:
            rv = None
        h3.metric("RSI (14)", f"{rv:.1f}" if rv is not None else "—")

    rows = 1 + int(show_rsi) + int(show_macd)
    heights = [0.6] + [0.2] * (rows - 1) if rows > 1 else [1.0]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, row_heights=heights, vertical_spacing=0.04)
    fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                                 name=ticker, increasing_line_color=GREEN, decreasing_line_color=RED), row=1, col=1)
    if "SMA 20" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=sma(df["Close"], 20), name="SMA 20", line=dict(color=PRIMARY_2, width=1.5)), row=1, col=1)
    if "SMA 50" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=sma(df["Close"], 50), name="SMA 50", line=dict(color=AMBER, width=1.5)), row=1, col=1)
    if "Bollinger Bands" in overlays:
        u, m, l = bollinger(df["Close"])
        fig.add_trace(go.Scatter(x=df["Date"], y=u, name="BB U", line=dict(color="rgba(124,92,255,0.5)", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=l, name="BB L", line=dict(color="rgba(124,92,255,0.5)", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(124,92,255,0.06)"), row=1, col=1)
    nr = 2
    if show_rsi:
        fig.add_trace(go.Scatter(x=df["Date"], y=rsi(df["Close"]), name="RSI", line=dict(color="#C084FC", width=1.5)), row=nr, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="rgba(255,92,122,0.5)", row=nr, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="rgba(0,227,154,0.5)", row=nr, col=1)
        fig.update_yaxes(range=[0, 100], row=nr, col=1)
        nr += 1
    if show_macd:
        ml, ms, mh = macd(df["Close"])
        colors = [GREEN if v >= 0 else RED for v in mh.fillna(0)]
        fig.add_trace(go.Bar(x=df["Date"], y=mh, name="Hist", marker_color=colors), row=nr, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=ml, name="MACD", line=dict(color=PRIMARY_2, width=1.3)), row=nr, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=ms, name="Signal", line=dict(color=AMBER, width=1.3)), row=nr, col=1)
    fig.update_layout(**PLOTLY_LAYOUT, height=640, xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h", y=1.02, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})


def page_news(pm, prices):
    hero("News", "Recent headlines for a company, with a simple positive/negative tag.", "📰")
    pool = list(dict.fromkeys(list(pm.holdings.keys()) + pm.d["watchlist"])) or ["RELIANCE.NS"]
    labels = [f"{TICKER_TO_NAME.get(t,t)} · {t}" for t in pool]
    pick = st.selectbox("Company", labels)
    ticker = pool[labels.index(pick)]
    with st.spinner("Fetching headlines…"):
        news = get_news(ticker, 12)
    if not news:
        st.info("No recent headlines found for this company from the data source.")
        return
    for n in news:
        tg = headline_tag(n["title"])
        tag = pill("Positive", "green") if tg > 0 else (pill("Negative", "red") if tg < 0 else pill("Neutral", "amber"))
        card_open()
        st.markdown(f"{tag} &nbsp; **[{n['title']}]({n['link']})**", unsafe_allow_html=True)
        st.caption(n.get("publisher", ""))
        card_close()


def page_learn(pm, prices):
    hero("Learn", "Every concept used in Fictrade, explained simply.", "🎓")
    topics = [
        ("💵 Market order", "Buys or sells immediately at the current price. Fictrade simulates market orders."),
        ("📉 RSI", "A 0–100 momentum gauge. Above 70 = 'overbought', below 30 = 'oversold' — a clue, not a rule."),
        ("📈 Moving averages", "The average price over N days, smoothing noise so you can see the trend."),
        ("🎯 MACD", "The gap between a fast and slow moving average — a momentum signal."),
        ("🎈 Bollinger Bands", "A band around a moving average; price near the top/bottom shows it's high/low vs recent swings."),
        ("🧺 Diversification", "Spreading money across several stocks so one bad one doesn't sink you."),
        ("💼 Invested vs cash", "'Invested' is money currently in stocks; 'cash left' is what's still available to deploy."),
        ("🩹 Realized vs unrealized P&L", "Unrealized = paper gain/loss on what you still hold. Realized = locked in once you sell."),
        ("📓 Why journal trades", "Writing down WHY you traded helps you learn from your own decisions over time."),
    ]
    for t, b in topics:
        with st.expander(t):
            st.write(b)
    st.markdown("---")
    st.info("🎮 Fictrade is a simulator. Prices are real; every trade is fictional play-money.")


def page_leaderboard(pm, prices):
    hero("Leaderboard", "Compare your portfolios, ranked by return.", "🏆")
    s = store()
    profs = s["profiles"]
    if len(profs) <= 1:
        st.info("Create more portfolios (from the sidebar) to compare strategies side by side.")
    all_t = set()
    for d in profs.values():
        all_t |= set(d["holdings"].keys())
    q = get_quotes_batch(tuple(all_t)) if all_t else {}
    rows = []
    for name, d in profs.items():
        m = Portfolio(d)
        lk = {t: x["price"] for t, x in q.items() if x and x.get("ok") and t in d["holdings"]}
        rows.append({"Portfolio": name, "Net Worth": round(m.total_value(lk), 2),
                     "Return %": round(m.total_return_pct(lk), 2), "Trades": len(m.transactions),
                     "Level": m.level(), "Badges": len(d["badges"])})
    df = pd.DataFrame(rows).sort_values("Return %", ascending=False).reset_index(drop=True)
    medal = {0: "🥇", 1: "🥈", 2: "🥉"}
    df.insert(0, "Rank", [f"{medal.get(i,'')} #{i+1}" for i in range(len(df))])
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_settings(pm, prices):
    hero("Settings", "Manage portfolios and learn about this simulator.", "⚙️")
    st.markdown("### 💰 Change starting capital")
    card_open()
    st.write(f"Current portfolio **{pm.d['name']}** started with **{fmt_money(pm.starting_cash)}**.")
    st.caption("Changing this resets the current portfolio to a clean slate with the new amount.")
    newcap = st.number_input("New starting capital (₹)", min_value=1000.0, value=float(pm.starting_cash), step=50000.0)
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
                "- **Saving:** everything is stored in **this browser** automatically — no login, no password. "
                "Clearing your browser data will erase it, and it won't follow you to another device/browser.\n"
                "- **Not investment advice.**")
    card_close()


# =============================================================================
# MAIN
# =============================================================================
def main():
    load_store()
    if not st.session_state.get("loaded"):
        return  # still waiting for localStorage; a rerun is queued
    s = store()
    if not s.get("onboarded") or not s.get("profiles"):
        onboarding()
        save_store()
        return
    inject_css()
    pm, prices, page = render_sidebar()
    {
        "🏠 Dashboard": page_dashboard, "💰 Trade": page_trade, "📊 Portfolio": page_portfolio,
        "⭐ Watchlist": page_watchlist, "📉 Charts": page_charts, "📰 News": page_news,
        "🎓 Learn": page_learn, "🏆 Leaderboard": page_leaderboard, "⚙️ Settings": page_settings,
    }[page](pm, prices)
    save_store()


if __name__ == "__main__":
    main()
