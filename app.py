"""
Fictrade — Fictional Trading Simulator with Real Market Data (single-file build)
================================================================================
A paper-trading web app: real prices & news from Yahoo Finance (via yfinance),
100% fictional money, an AI Coach layer, gamification, and a dark fintech UI.

NO real brokerage, NO real orders, NO real money — ever. Educational only.

This is a single-file build designed for one-click hosting on Streamlit
Community Cloud. Just this file + requirements.txt in a GitHub repo is enough.

Run locally:   streamlit run app.py
"""

from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

# =============================================================================
# CONFIG & THEME
# =============================================================================
st.set_page_config(page_title="Fictrade — Fictional Trading", page_icon="📈", layout="wide")

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

POPULAR_US = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX", "JPM", "V", "DIS", "AMD"]
POPULAR_IN = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS",
              "ITC.NS", "WIPRO.NS", "BAJFINANCE.NS", "ADANIENT.NS", "TATAMOTORS.NS", "HINDUNILVR.NS"]
PERIOD_INTERVAL = {"1D": ("1d", "5m"), "5D": ("5d", "15m"), "1M": ("1mo", "1d"),
                   "6M": ("6mo", "1d"), "1Y": ("1y", "1d"), "5Y": ("5y", "1wk"), "MAX": ("max", "1mo")}
DEFAULT_STARTING_CASH = {"USD": 100000.0, "INR": 10000000.0}


def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; }}
    .stApp {{
        background: radial-gradient(circle at 15% 0%, rgba(124,92,255,0.16), transparent 40%),
          radial-gradient(circle at 85% 15%, rgba(62,198,255,0.12), transparent 45%),
          linear-gradient(180deg, #06070D 0%, #0C0F1D 100%);
        color: #EAEBF3;
    }}
    #MainMenu, footer {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    section[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #0A0C18, #090A14); border-right: 1px solid {CARD_BORDER}; }}
    section[data-testid="stSidebar"] * {{ color: #D6D9E8 !important; }}
    h1,h2,h3 {{ font-weight: 800 !important; letter-spacing: -0.02em; }}
    h1 {{ color: #fff !important; }}
    div[data-testid="stMetric"] {{ background:{CARD}; border:1px solid {CARD_BORDER}; border-radius:16px; padding:14px 18px 10px; backdrop-filter: blur(6px); }}
    div[data-testid="stMetricLabel"] {{ color:{TEXT_MUTED} !important; font-weight:600; text-transform:uppercase; font-size:0.72rem !important; letter-spacing:0.06em; }}
    div[data-testid="stMetricValue"] {{ font-family:'JetBrains Mono', monospace; font-weight:700 !important; }}
    .stButton > button, .stFormSubmitButton > button {{
        background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_2}); color:#fff !important; border:none;
        border-radius:12px; font-weight:700; padding:0.55rem 1.2rem; transition:transform .12s, box-shadow .12s;
        box-shadow:0 4px 18px rgba(124,92,255,0.28); }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{ transform:translateY(-1px); box-shadow:0 8px 24px rgba(124,92,255,0.4); }}
    button[data-baseweb="tab"] {{ font-weight:600; color:{TEXT_MUTED} !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color:#fff !important; }}
    div[data-baseweb="tab-highlight"] {{ background-color:{PRIMARY} !important; }}
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {{
        background:{CARD} !important; border:1px solid {CARD_BORDER} !important; border-radius:10px !important; color:#EAEBF3 !important; }}
    div[data-testid="stDataFrame"] {{ border:1px solid {CARD_BORDER}; border-radius:14px; overflow:hidden; }}
    .hero {{ padding:28px 30px; border-radius:22px; background:linear-gradient(120deg, rgba(124,92,255,0.22), rgba(62,198,255,0.10)); border:1px solid {CARD_BORDER}; margin-bottom:22px; }}
    .hero h1 {{ margin:0 0 4px 0; font-size:2rem; }}
    .hero p {{ margin:0; color:{TEXT_MUTED}; font-size:0.98rem; }}
    .glass-card {{ background:{CARD}; border:1px solid {CARD_BORDER}; border-radius:18px; padding:18px 20px; backdrop-filter:blur(6px); margin-bottom:14px; }}
    .pill {{ display:inline-block; padding:3px 12px; border-radius:999px; font-size:0.74rem; font-weight:700; }}
    .pill-green {{ background:rgba(0,227,154,0.15); color:{GREEN}; border:1px solid rgba(0,227,154,0.35); }}
    .pill-red {{ background:rgba(255,92,122,0.15); color:{RED}; border:1px solid rgba(255,92,122,0.35); }}
    .pill-amber {{ background:rgba(255,198,92,0.15); color:{AMBER}; border:1px solid rgba(255,198,92,0.35); }}
    .pill-violet {{ background:rgba(124,92,255,0.18); color:#C9BBFF; border:1px solid rgba(124,92,255,0.4); }}
    .badge {{ display:inline-flex; align-items:center; gap:6px; background:linear-gradient(135deg, rgba(124,92,255,0.25), rgba(62,198,255,0.18));
        border:1px solid rgba(124,92,255,0.4); border-radius:999px; padding:6px 14px; font-size:0.8rem; font-weight:700; margin:3px 6px 3px 0; }}
    .mono {{ font-family:'JetBrains Mono', monospace; }}
    .ticker-tape {{ white-space:nowrap; overflow-x:auto; padding-bottom:6px; }}
    .ticker-item {{ display:inline-block; background:{CARD}; border:1px solid {CARD_BORDER}; border-radius:12px; padding:10px 16px; margin-right:10px; }}
    .xp-track {{ width:100%; height:10px; border-radius:999px; background:rgba(255,255,255,0.08); overflow:hidden; border:1px solid {CARD_BORDER}; }}
    .xp-fill {{ height:100%; background:linear-gradient(90deg, {PRIMARY}, {PRIMARY_2}); }}
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
    arrow = "▲" if pct >= 0 else "▼"
    return pill(f"{arrow} {pct:+.2f}%", kind)


def badge(text, icon="🏅"):
    return f'<span class="badge">{icon} {text}</span>'


def card_open():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def xp_bar(pct):
    pct = max(0, min(100, pct))
    st.markdown(f'<div class="xp-track"><div class="xp-fill" style="width:{pct}%;"></div></div>', unsafe_allow_html=True)


def currency_symbol(code):
    return {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥"}.get(code, code + " ")


def fmt_money(value, currency="USD", compact=False):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    sym = currency_symbol(currency)
    if compact:
        a = abs(value)
        if a >= 1e12:
            return f"{sym}{value/1e12:.2f}T"
        if a >= 1e9:
            return f"{sym}{value/1e9:.2f}B"
        if a >= 1e7 and currency == "INR":
            return f"{sym}{value/1e7:.2f}Cr"
        if a >= 1e5 and currency == "INR":
            return f"{sym}{value/1e5:.2f}L"
        if a >= 1e6:
            return f"{sym}{value/1e6:.2f}M"
    return f"{sym}{value:,.2f}"


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
    out = {"ticker": ticker, "ok": False, "name": ticker, "price": None, "prev_close": None,
           "change": None, "change_pct": None, "day_high": None, "day_low": None, "volume": None,
           "market_cap": None, "pe": None, "sector": None, "currency": "USD", "year_high": None, "year_low": None}
    if yf is None:
        out["error"] = "yfinance not installed"
        return out
    try:
        t = yf.Ticker(ticker)
        try:
            fi = dict(t.fast_info)
        except Exception:
            fi = {}
        price = _safe_get(fi, "lastPrice", "last_price")
        prev_close = _safe_get(fi, "previousClose", "previous_close")
        if price is None or prev_close is None:
            hist = get_history(ticker, "5d", "1d")
            if not hist.empty:
                if price is None:
                    price = float(hist["Close"].iloc[-1])
                if prev_close is None and len(hist) > 1:
                    prev_close = float(hist["Close"].iloc[-2])
        if price is None:
            return out
        prev_close = prev_close if prev_close else price
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        out.update({"ok": True, "price": float(price), "prev_close": float(prev_close),
                    "change": float(change), "change_pct": float(change_pct),
                    "day_high": _safe_get(fi, "dayHigh", "day_high"), "day_low": _safe_get(fi, "dayLow", "day_low"),
                    "volume": _safe_get(fi, "lastVolume", "last_volume"), "market_cap": _safe_get(fi, "marketCap", "market_cap"),
                    "year_high": _safe_get(fi, "yearHigh", "year_high"), "year_low": _safe_get(fi, "yearLow", "year_low"),
                    "currency": _safe_get(fi, "currency", default="USD")})
        try:
            info = t.get_info()
            out["name"] = info.get("shortName") or info.get("longName") or ticker
            out["sector"] = info.get("sector")
            out["pe"] = info.get("trailingPE")
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
def get_news(ticker, limit=8):
    if yf is None:
        return []
    try:
        items = yf.Ticker(ticker).news or []
        cleaned = []
        for it in items[:limit]:
            content = it.get("content", it)
            title = content.get("title") or it.get("title")
            prov = content.get("provider")
            publisher = prov.get("displayName") if isinstance(prov, dict) else it.get("publisher")
            cu = content.get("canonicalUrl")
            link = cu.get("url") if isinstance(cu, dict) else it.get("link")
            if not title:
                continue
            cleaned.append({"title": title, "publisher": publisher or "Unknown", "link": link or "#"})
        return cleaned
    except Exception:
        return []


# =============================================================================
# INDICATORS
# =============================================================================
def sma(series, window):
    return series.rolling(window=window, min_periods=max(2, window // 3)).mean()


def ema(series, window):
    return series.ewm(span=window, adjust=False).mean()


def rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    ag = gain.ewm(alpha=1 / window, min_periods=window).mean()
    al = loss.ewm(alpha=1 / window, min_periods=window).mean()
    rs = ag / al.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


def macd(series, fast=12, slow=26, signal=9):
    ml = ema(series, fast) - ema(series, slow)
    sl = ema(ml, signal)
    return ml, sl, ml - sl


def bollinger(series, window=20, num_std=2.0):
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=max(2, window // 3)).std()
    return mid + num_std * std, mid, mid - num_std * std


def max_drawdown_pct(series):
    if series.empty:
        return 0.0
    cummax = series.cummax()
    return float(((series - cummax) / cummax).min() * 100)


def volatility_pct(series):
    rets = series.pct_change().dropna()
    return 0.0 if rets.empty else float(rets.std() * np.sqrt(252) * 100)


def signal_snapshot(df):
    if df is None or df.empty or len(df) < 5:
        return {}
    c = df["Close"]
    r = rsi(c)
    ml, ms, mh = macd(c)
    u, m, l = bollinger(c)
    s20, s50 = sma(c, min(20, len(c))), sma(c, min(50, len(c)))

    def last(x):
        return float(x.iloc[-1]) if not pd.isna(x.iloc[-1]) else None
    return {"rsi": last(r), "macd": last(ml), "macd_signal": last(ms), "macd_hist": last(mh),
            "sma20": last(s20), "sma50": last(s50), "bb_upper": last(u), "bb_lower": last(l),
            "last_close": float(c.iloc[-1]), "volatility": volatility_pct(c), "max_drawdown": max_drawdown_pct(c)}


# =============================================================================
# AI COACH (rule-based)
# =============================================================================
POSITIVE_WORDS = {"beat", "beats", "surge", "surges", "soar", "soars", "rally", "record", "growth",
                  "upgrade", "upgraded", "profit", "profits", "gain", "gains", "strong", "outperform",
                  "bullish", "partnership", "approval", "approved", "buyback", "dividend", "raise",
                  "raised", "jump", "jumps", "boom", "breakthrough", "positive", "win", "wins", "exceeds", "upbeat"}
NEGATIVE_WORDS = {"miss", "misses", "plunge", "plunges", "slump", "fall", "falls", "downgrade", "downgraded",
                  "loss", "losses", "weak", "underperform", "bearish", "layoff", "layoffs", "lawsuit", "probe",
                  "investigation", "recall", "cut", "cuts", "warning", "warns", "decline", "declines", "sinks",
                  "drop", "drops", "negative", "concern", "concerns", "risk", "risks", "delay", "delayed", "fraud"}


def headline_sentiment(title):
    words = {w.strip(".,!?:;()'\"").lower() for w in title.split()}
    pos, neg = len(words & POSITIVE_WORDS), len(words & NEGATIVE_WORDS)
    return 1 if pos > neg else (-1 if neg > pos else 0)


def news_sentiment_summary(news):
    if not news:
        return {"label": "No data", "score": 0, "pos": 0, "neg": 0, "neu": 0}
    scores = [headline_sentiment(n["title"]) for n in news]
    pos, neg, neu = scores.count(1), scores.count(-1), scores.count(0)
    net = pos - neg
    label = "Leaning Bullish 🟢" if net >= 2 else ("Leaning Bearish 🔴" if net <= -2 else "Mixed / Neutral 🟡")
    return {"label": label, "score": net, "pos": pos, "neg": neg, "neu": neu}


def technical_narrative(ticker, snap):
    if not snap:
        return f"Not enough price history for {ticker} yet to generate a technical read."
    lines = []
    r = snap.get("rsi")
    if r is not None:
        if r >= 70:
            lines.append(f"RSI is {r:.0f}, in overbought territory (≥70) — the stock has moved up quickly and short-term pullbacks are more common from here.")
        elif r <= 30:
            lines.append(f"RSI is {r:.0f}, in oversold territory (≤30) — selling pressure looks stretched, which historically precedes bounces (but not always).")
        else:
            lines.append(f"RSI is {r:.0f} — neither overbought nor oversold, a fairly neutral momentum reading.")
    s20, s50, price = snap.get("sma20"), snap.get("sma50"), snap.get("last_close")
    if s20 and s50 and price:
        if price > s20 > s50:
            lines.append("Price is above both its 20-day and 50-day averages, and the shorter average is above the longer one — a classic short-term uptrend structure.")
        elif price < s20 < s50:
            lines.append("Price is below both its 20-day and 50-day averages, with the shorter also below the longer — a short-term downtrend structure.")
        else:
            lines.append("Price is chopping around its moving averages without a clean trend in either direction right now.")
    mh = snap.get("macd_hist")
    if mh is not None:
        lines.append("MACD histogram is positive — momentum has been tilting upward recently." if mh > 0
                     else "MACD histogram is negative — momentum has been tilting downward recently.")
    bu, bl = snap.get("bb_upper"), snap.get("bb_lower")
    if bu and bl and price:
        if price >= bu:
            lines.append("Price is testing the upper Bollinger Band — trading near the top of its recent volatility range.")
        elif price <= bl:
            lines.append("Price is testing the lower Bollinger Band — trading near the bottom of its recent volatility range.")
    v = snap.get("volatility")
    if v is not None:
        lines.append(f"Annualized volatility over this window is roughly {v:.1f}%.")
    lines.append("This is a descriptive read of the math, not a prediction or investment advice.")
    return " ".join(lines)


def risk_check(weights):
    notes = []
    if not weights:
        return ["Your portfolio is currently all cash — no concentration risk, but also no market exposure."]
    weights = sorted(weights, key=lambda x: -x[1])
    top_t, top_w = weights[0]
    if top_w >= 50:
        notes.append(f"{top_t} makes up {top_w:.0f}% of your invested portfolio — a single bad day there will dominate results. Consider whether that concentration is intentional.")
    elif top_w >= 30:
        notes.append(f"{top_t} is your largest position at {top_w:.0f}% of holdings — worth keeping an eye on.")
    if len(weights) == 1:
        notes.append("You currently hold only one stock. Diversifying across a few uncorrelated names is a common way to reduce single-stock risk.")
    elif len(weights) >= 8:
        notes.append(f"You're spread across {len(weights)} positions — good diversification, though very small positions add tracking overhead for limited benefit.")
    if not notes:
        notes.append("Position sizing looks reasonably balanced across your holdings.")
    return notes


def daily_briefing(quotes):
    q = [x for x in quotes if x and x.get("ok")]
    if not q:
        return "Add a few stocks to your watchlist or portfolio to get a daily briefing here."
    seen = {x["ticker"]: x for x in q}
    q = list(seen.values())
    gainers = sorted([x for x in q if x["change_pct"] >= 0], key=lambda x: -x["change_pct"])
    losers = sorted([x for x in q if x["change_pct"] < 0], key=lambda x: x["change_pct"])
    parts = []
    if gainers:
        parts.append(f"{gainers[0]['ticker']} is today's top mover on your radar, up {gainers[0]['change_pct']:+.2f}%.")
    if losers:
        parts.append(f"{losers[0]['ticker']} is lagging, down {losers[0]['change_pct']:+.2f}%.")
    avg = sum(x["change_pct"] for x in q) / len(q)
    tone = "a broadly positive" if avg > 0.3 else ("a broadly negative" if avg < -0.3 else "a fairly flat")
    parts.append(f"Across the {len(q)} names you're tracking, it's been {tone} session on average ({avg:+.2f}%).")
    return " ".join(parts)


def ask_ai_coach(api_key, model, context, question):
    try:
        import anthropic
    except ImportError:
        return "The `anthropic` package isn't installed."
    if not api_key:
        return "Add your Anthropic API key in Settings to unlock live AI Q&A."
    system = ("You are the AI Coach inside Fictrade, a FICTIONAL paper-trading simulator for education. "
              "No real money or brokerage is involved. Explain concepts and the given data clearly, ground "
              "answers in the numbers provided, encourage good habits (journaling, diversification, risk "
              "thinking). Do NOT give personalized real-money investment advice or claim certainty about "
              "future prices. Keep answers concise, warm, and educational.")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        ctx = "\n".join(f"- {k}: {v}" for k, v in context.items())
        resp = client.messages.create(model=model or "claude-sonnet-5", max_tokens=700, system=system,
                                       messages=[{"role": "user", "content": f"CONTEXT (fictional simulator):\n{ctx}\n\nQUESTION: {question}"}])
        return "\n".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip() or "(no response)"
    except Exception as e:
        return f"Couldn't reach the AI Coach right now ({e}). The rule-based insights still work without an API key."


# =============================================================================
# PORTFOLIO (session-state backed; persists for the session)
# =============================================================================
BADGE_DEFS = [
    ("first_trade", "🎬", "First Trade", "Placed your first order."),
    ("five_holdings", "🧺", "Diversifier", "Held 5+ different stocks at once."),
    ("ten_trades", "🔟", "Getting Serious", "Placed 10 trades."),
    ("fifty_trades", "💼", "Desk Veteran", "Placed 50 trades."),
    ("profit_10", "🌱", "In The Green", "Portfolio return crossed +10%."),
    ("profit_50", "🚀", "Rocket Ride", "Portfolio return crossed +50%."),
    ("doubled", "💎", "Doubled Up", "Doubled your starting capital."),
    ("first_loss_take", "🩹", "Cut The Loss", "Sold a losing position."),
    ("journaled", "📓", "Reflective Trader", "Wrote a trade journal note."),
    ("concentrated", "⚠️", "High Roller", "Put 50%+ into one stock."),
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def new_portfolio(name, currency):
    cash = DEFAULT_STARTING_CASH.get(currency, 100000.0)
    return {"name": name, "currency": currency, "starting_cash": cash, "cash": cash,
            "holdings": {}, "transactions": [], "net_worth_history": [{"ts": _now(), "value": cash}],
            "journal": [], "badges": [], "watchlist": []}


class Portfolio:
    """Thin wrapper over a plain dict kept in st.session_state."""

    def __init__(self, d):
        self.d = d

    @property
    def currency(self):
        return self.d["currency"]

    @property
    def cash(self):
        return self.d["cash"]

    @property
    def holdings(self):
        return self.d["holdings"]

    @property
    def transactions(self):
        return self.d["transactions"]

    def holdings_value(self, prices):
        return sum(prices.get(t, p["avg_price"]) * p["qty"] for t, p in self.holdings.items())

    def total_value(self, prices):
        return self.cash + self.holdings_value(prices)

    def total_return_pct(self, prices):
        s = self.d["starting_cash"]
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
        return True, f"Bought {qty} x {ticker} @ {price:.2f}"

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
        return True, f"Sold {qty} x {ticker} @ {price:.2f} ({'+' if realized >= 0 else ''}{realized:.2f} P&L)"

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
        return int(len(self.transactions) * 15 + max(0, realized) / 50 + len(self.d["badges"]) * 40)

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
        if n >= 50:
            award("fifty_trades")
        if len(self.holdings) >= 5:
            award("five_holdings")
        if any(t.get("side") == "SELL" and (t.get("realized_pl") or 0) < 0 for t in self.transactions):
            award("first_loss_take")
        if self.d["journal"]:
            award("journaled")
        ret = self.total_return_pct(prices)
        if ret >= 10:
            award("profit_10")
        if ret >= 50:
            award("profit_50")
        tv = self.total_value(prices)
        if tv >= 2 * self.d["starting_cash"]:
            award("doubled")
        for t, pos in self.holdings.items():
            if (prices.get(t, pos["avg_price"]) * pos["qty"]) / max(tv, 1) >= 0.5:
                award("concentrated")
                break
        self.d["badges"] = sorted(earned)
        return newly

    def badge_details(self):
        earned = set(self.d["badges"])
        return [{"id": b, "icon": i, "title": t, "desc": desc, "earned": b in earned} for b, i, t, desc in BADGE_DEFS]

    def reset(self):
        self.d.update(new_portfolio(self.d["name"], self.d["currency"]))


# =============================================================================
# ACCOUNTS + BROWSER STORAGE
# -----------------------------------------------------------------------------
# Everything is stored in the browser's localStorage on THIS device — there is
# no server database. That means: data persists across sessions on the same
# browser, each account is device-local, and the "password" is a lightweight
# local lock (hashed, but NOT bank-grade). We say so plainly in the UI.
# =============================================================================
import hashlib
import secrets

try:
    from streamlit_local_storage import LocalStorage
    _LS = LocalStorage()
    LS_OK = True
except Exception:  # component missing or failed to load -> session-only mode
    _LS = None
    LS_OK = False

DB_KEY = "fictrade_db_v1"


def _hash_pw(password, salt):
    return hashlib.sha256((salt + "::" + password).encode("utf-8")).hexdigest()


def _db_hash():
    return hashlib.md5(json.dumps(st.session_state.get("db", {}), sort_keys=True).encode()).hexdigest()


def load_db():
    """Load the accounts DB from localStorage into session_state.

    We keep re-reading until we either see a real value or the user acts
    (do_login/signup set db_ready), which avoids the 'stuck empty on first
    mount' race that localStorage components can have.
    """
    if st.session_state.get("db_ready"):
        return
    raw = None
    if LS_OK:
        try:
            raw = _LS.getItem(DB_KEY)
        except Exception:
            raw = None
    else:
        st.session_state.setdefault("db", {"users": {}})
        st.session_state["db_ready"] = True
        st.session_state["db_hash"] = _db_hash()
        return
    if raw:
        try:
            st.session_state["db"] = json.loads(raw)
            st.session_state["db_ready"] = True
        except Exception:
            st.session_state["db"] = {"users": {}}
    else:
        st.session_state.setdefault("db", {"users": {}})
    st.session_state["db_hash"] = _db_hash()


def save_db():
    """Persist to localStorage only when the DB actually changed."""
    if not LS_OK:
        return
    h = _db_hash()
    if st.session_state.get("db_hash") != h:
        st.session_state["_ls_n"] = st.session_state.get("_ls_n", 0) + 1
        try:
            _LS.setItem(DB_KEY, json.dumps(st.session_state["db"]), key=f"ls_set_{st.session_state['_ls_n']}")
        except Exception:
            pass
        st.session_state["db_hash"] = h


def _users():
    return st.session_state["db"].setdefault("users", {})


def signup(username, password):
    username = (username or "").strip()
    if not username or not password:
        return False, "Enter a username and a password."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if username.lower() in {u.lower() for u in _users()}:
        return False, "That username is already taken on this device."
    salt = secrets.token_hex(8)
    prof = new_portfolio("My Portfolio", "USD")
    prof["watchlist"] = ["AAPL", "TSLA", "RELIANCE.NS"]
    _users()[username] = {
        "salt": salt,
        "password_hash": _hash_pw(password, salt),
        "created_at": _now(),
        "profiles": {"My Portfolio": prof},
        "active_profile": "My Portfolio",
    }
    return True, username


def login(username, password):
    username = (username or "").strip()
    match = next((u for u in _users() if u.lower() == username.lower()), None)
    if not match:
        return False, "No account with that username on this device."
    u = _users()[match]
    if _hash_pw(password, u["salt"]) != u["password_hash"]:
        return False, "Incorrect password."
    return True, match


def do_login(username):
    """Point the session's working profiles at this account's stored data (by
    reference), so any trade the user makes mutates the DB and gets saved."""
    st.session_state["user"] = username
    u = _users()[username]
    st.session_state["profiles"] = u["profiles"]
    st.session_state["active_profile"] = u.get("active_profile") or next(iter(u["profiles"]))
    st.session_state["is_guest"] = False
    st.session_state["db_ready"] = True


def do_guest():
    gp = new_portfolio("My Portfolio", "USD")
    gp["watchlist"] = ["AAPL", "TSLA", "RELIANCE.NS"]
    st.session_state["user"] = "Guest"
    st.session_state["profiles"] = {"My Portfolio": gp}  # NOT in db -> never saved
    st.session_state["active_profile"] = "My Portfolio"
    st.session_state["is_guest"] = True


def logout():
    for k in ("user", "profiles", "active_profile", "is_guest"):
        st.session_state.pop(k, None)


def ensure_defaults():
    st.session_state.setdefault("anthropic_api_key", "")
    st.session_state.setdefault("ai_model", "claude-sonnet-5")
    st.session_state.setdefault("trade_ticker", "AAPL")
    st.session_state.setdefault("chart_ticker", "AAPL")


def sync_active_to_db():
    """Persist the current active-profile choice into the account record."""
    if not st.session_state.get("is_guest", True):
        user = st.session_state.get("user")
        if user and user in _users():
            _users()[user]["active_profile"] = st.session_state.get("active_profile")


def active_portfolio():
    profiles = st.session_state["profiles"]
    name = st.session_state.get("active_profile")
    if name not in profiles:
        name = next(iter(profiles))
        st.session_state["active_profile"] = name
    return Portfolio(profiles[name])


def auth_gate():
    """Login / signup screen shown when nobody is logged in."""
    inject_css()
    hero("Fictrade", "Practice trading with real market data and fake money. "
         "Create an account and your portfolio saves right here in your browser.", "📈")
    if not LS_OK:
        st.warning("Browser storage isn't available in this environment, so accounts will only last for "
                   "the current session (they won't be here when you come back).")
    st.caption("🔒 Lightweight local login: accounts live in THIS browser on THIS device, and the password is a "
               "simple local lock — please don't reuse an important password.")

    t_login, t_signup, t_guest = st.tabs(["🔑 Log in", "🆕 Create account", "👀 Guest"])

    with t_login:
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Log in", use_container_width=True):
                ok, res = login(u, p)
                if ok:
                    do_login(res)
                    save_db()
                    st.rerun()
                else:
                    st.error(res)

    with t_signup:
        with st.form("signup_form"):
            u = st.text_input("Choose a username")
            p = st.text_input("Choose a password", type="password")
            p2 = st.text_input("Confirm password", type="password")
            if st.form_submit_button("Create account", use_container_width=True):
                if p != p2:
                    st.error("Passwords don't match.")
                else:
                    ok, res = signup(u, p)
                    if ok:
                        do_login(res)
                        save_db()
                        st.rerun()
                    else:
                        st.error(res)

    with t_guest:
        st.caption("Play around without an account. Nothing is saved once you close the tab.")
        if st.button("Continue as guest", use_container_width=True):
            do_guest()
            st.rerun()


def price_lookup_for(pm):
    tickers = tuple(pm.holdings.keys())
    if not tickers:
        return {}
    quotes = get_quotes_batch(tickers)
    return {t: q["price"] for t, q in quotes.items() if q and q.get("ok") and q.get("price")}


# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar():
    st.sidebar.markdown("### 📈 Fictrade")
    user = st.session_state.get("user", "Guest")
    is_guest = st.session_state.get("is_guest", True)
    tag = "guest — not saved" if is_guest else "saved in this browser"
    st.sidebar.caption(f"👤 **{user}** · {tag}")
    if st.sidebar.button("Log out", use_container_width=True):
        logout()
        st.rerun()
    st.sidebar.markdown("---")

    names = list(st.session_state["profiles"].keys())
    active = st.session_state["active_profile"]
    choice = st.sidebar.selectbox("Trading profile", names, index=names.index(active) if active in names else 0)
    if choice != active:
        st.session_state["active_profile"] = choice
        sync_active_to_db()
        st.rerun()

    with st.sidebar.expander("➕ New profile"):
        with st.form("new_profile", clear_on_submit=True):
            nm = st.text_input("Name", placeholder="e.g. Warren Jr.")
            cur = st.selectbox("Market / currency", ["USD", "INR"])
            if st.form_submit_button("Create") and nm.strip():
                if nm.strip() not in st.session_state["profiles"]:
                    st.session_state["profiles"][nm.strip()] = new_portfolio(nm.strip(), cur)
                    st.session_state["active_profile"] = nm.strip()
                    sync_active_to_db()
                    st.rerun()

    pm = active_portfolio()
    prices = price_lookup_for(pm)
    st.sidebar.markdown("---")
    st.sidebar.metric("Net worth", fmt_money(pm.total_value(prices), pm.currency, compact=True),
                      f"{pm.total_return_pct(prices):+.2f}%")
    st.sidebar.progress(min(max(pm.level_progress_pct() / 100, 0.0), 1.0), text=f"Level {pm.level()} • {pm.xp()} XP")
    st.sidebar.markdown("---")

    page = st.sidebar.radio("Navigate", ["🏠 Dashboard", "💰 Trade", "📊 Portfolio", "⭐ Watchlist",
                                         "📉 Charts", "🤖 AI Coach", "📰 News", "🎓 Learn",
                                         "🏆 Leaderboard", "⚙️ Settings"], label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Simulated trading only — no real orders, money, or broker.")
    return pm, prices, page


# =============================================================================
# PAGES
# =============================================================================
def page_dashboard(pm, prices):
    hero(f"Welcome back, {pm.d['name']}",
         "Fictional trading simulator. Prices are real (Yahoo Finance via yfinance); every trade is make-believe.", "📈")
    tv = pm.total_value(prices)
    ret = pm.total_return_pct(prices)
    day_pl = sum((prices.get(t, p["avg_price"]) - p["avg_price"]) * p["qty"] for t, p in pm.holdings.items())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Worth", fmt_money(tv, pm.currency, compact=True), f"{ret:+.2f}% all-time")
    c2.metric("Cash Available", fmt_money(pm.cash, pm.currency, compact=True))
    c3.metric("Invested Value", fmt_money(pm.holdings_value(prices), pm.currency, compact=True))
    c4.metric("Open Position P&L", fmt_money(day_pl, pm.currency, compact=True))
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
            fig.add_hline(y=pm.d["starting_cash"], line_dash="dot", line_color="rgba(255,255,255,0.3)")
            fig.update_layout(**PLOTLY_LAYOUT, height=340, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Make your first trade to start tracking your net-worth curve.")
        st.markdown("#### 🤖 Today's AI briefing")
        card_open()
        wq = list(get_quotes_batch(tuple(pm.d["watchlist"])).values()) if pm.d["watchlist"] else []
        pq = list(get_quotes_batch(tuple(pm.holdings.keys())).values()) if pm.holdings else []
        st.write(daily_briefing(wq + pq))
        card_close()
    with right:
        st.markdown("#### 🏅 Level & Badges")
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
        st.markdown("#### 🧺 Top holdings")
        card_open()
        if pm.holdings:
            for t, pos in sorted(pm.holdings.items(), key=lambda kv: -(prices.get(kv[0], kv[1]["avg_price"]) * kv[1]["qty"]))[:5]:
                price = prices.get(t, pos["avg_price"])
                val = price * pos["qty"]
                plp = (price - pos["avg_price"]) / pos["avg_price"] * 100 if pos["avg_price"] else 0
                a, b, c = st.columns([1.3, 1.3, 1])
                a.markdown(f"**{t}**")
                b.markdown(f"<span class='mono'>{fmt_money(val, pm.currency, compact=True)}</span>", unsafe_allow_html=True)
                c.markdown(change_pill(plp), unsafe_allow_html=True)
        else:
            st.caption("No positions yet — go to Trade.")
        card_close()
    st.markdown("#### 🌍 Market pulse")
    universe = POPULAR_US[:8] + POPULAR_IN[:4]
    quotes = get_quotes_batch(tuple(universe))
    tape = '<div class="ticker-tape">'
    for t in universe:
        q = quotes.get(t)
        if q and q.get("ok"):
            tape += (f'<div class="ticker-item"><b>{t}</b><br><span class="mono">{fmt_money(q["price"], q.get("currency","USD"))}</span> {change_pill(q["change_pct"])}</div>')
    tape += "</div>"
    st.markdown(tape, unsafe_allow_html=True)


def page_trade(pm, prices):
    hero("Trade", "Search any real ticker, see a delayed quote, place a fictional order.", "💰")
    cs, cq = st.columns([2, 1])
    with cs:
        ticker = st.text_input("Ticker symbol", value=st.session_state.get("trade_ticker", "AAPL"),
                               placeholder="e.g. AAPL, TSLA, RELIANCE.NS",
                               help="US tickers as-is. Indian NSE stocks need a .NS suffix.").strip().upper()
        st.session_state["trade_ticker"] = ticker
    with cq:
        st.write("")
        st.write("")
        ql = POPULAR_US if pm.currency == "USD" else POPULAR_IN
        pick = st.selectbox("Or pick one", ["—"] + ql, label_visibility="collapsed")
        if pick != "—":
            ticker = pick
            st.session_state["trade_ticker"] = ticker
    if not ticker:
        st.info("Enter a ticker to begin.")
        return
    with st.spinner(f"Fetching real data for {ticker}..."):
        q = get_quote(ticker)
    if not q.get("ok"):
        st.error(f"Couldn't fetch '{ticker}'. Check the symbol (Indian stocks need '.NS'). {('Details: '+q['error']) if q.get('error') else ''}")
        return
    a, b, c, d, e = st.columns([1.6, 1, 1, 1, 1])
    a.markdown(f"### {q['name']} · `{ticker}`")
    a.markdown(change_pill(q["change_pct"]), unsafe_allow_html=True)
    b.metric("Price", fmt_money(q["price"], q["currency"]))
    c.metric("Day High", fmt_money(q.get("day_high"), q["currency"]) if q.get("day_high") else "—")
    d.metric("Day Low", fmt_money(q.get("day_low"), q["currency"]) if q.get("day_low") else "—")
    e.metric("Mkt Cap", fmt_money(q.get("market_cap"), q["currency"], compact=True) if q.get("market_cap") else "—")
    hist = get_history(ticker, "3mo", "1d")
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist["Date"], y=hist["Close"], mode="lines",
                                 line=dict(color=PRIMARY, width=2.5), fill="tozeroy", fillcolor="rgba(124,92,255,0.10)"))
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
        with st.form("buy"):
            maxq = int(pm.cash // q["price"]) if q["price"] else 0
            qty = st.number_input("Quantity", min_value=1, value=min(10, max(1, maxq)) or 1, step=1)
            st.caption(f"Est. cost: **{fmt_money(qty*q['price'], q['currency'])}** · Cash: {fmt_money(pm.cash, pm.currency)}")
            note = st.text_input("Journal note (optional)")
            if st.form_submit_button("Place Buy Order", use_container_width=True):
                ok, msg = pm.buy(ticker, int(qty), q["price"], note)
                if ok:
                    if note:
                        pm.add_journal(ticker, note)
                    pm.snapshot({**prices, ticker: q["price"]}, force=True)
                    for bid in pm.check_badges({**prices, ticker: q["price"]}):
                        st.toast(f"🏅 Badge unlocked: {dict((x['id'], x) for x in pm.badge_details())[bid]['title']}", icon="🏅")
                    st.success(msg)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)
        card_close()
    with o2:
        card_open()
        st.markdown("#### 🔴 Sell")
        if existing:
            st.caption(f"You hold **{existing['qty']}** @ avg {fmt_money(existing['avg_price'], q['currency'])}")
            st.markdown(change_pill((q["price"] - existing["avg_price"]) / existing["avg_price"] * 100), unsafe_allow_html=True)
            with st.form("sell"):
                qty = st.number_input("Quantity", min_value=1, max_value=int(existing["qty"]), value=int(existing["qty"]), step=1)
                st.caption(f"Est. proceeds: **{fmt_money(qty*q['price'], q['currency'])}**")
                note = st.text_input("Reason for selling (optional)")
                if st.form_submit_button("Place Sell Order", use_container_width=True):
                    ok, msg = pm.sell(ticker, int(qty), q["price"], note)
                    if ok:
                        if note:
                            pm.add_journal(ticker, note)
                        pm.snapshot({**prices, ticker: q["price"]}, force=True)
                        for bid in pm.check_badges({**prices, ticker: q["price"]}):
                            st.toast(f"🏅 Badge unlocked: {dict((x['id'], x) for x in pm.badge_details())[bid]['title']}", icon="🏅")
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
        st.rerun()


def page_portfolio(pm, prices):
    hero("Portfolio", "Your fictional holdings, performance, and full trade history.", "📊")
    tv = pm.total_value(prices)
    realized = sum(t.get("realized_pl") or 0 for t in pm.transactions)
    unreal = sum((prices.get(t, p["avg_price"]) - p["avg_price"]) * p["qty"] for t, p in pm.holdings.items())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Worth", fmt_money(tv, pm.currency, compact=True), f"{pm.total_return_pct(prices):+.2f}%")
    c2.metric("Realized P&L", fmt_money(realized, pm.currency, compact=True))
    c3.metric("Unrealized P&L", fmt_money(unreal, pm.currency, compact=True))
    c4.metric("Total Trades", str(len(pm.transactions)))
    t1, t2, t3, t4, t5 = st.tabs(["📦 Holdings", "🥧 Allocation", "🧾 Transactions", "📓 Journal", "🏅 Badges"])
    with t1:
        if not pm.holdings:
            st.info("No open positions. Go to Trade.")
        else:
            rows = []
            for t, pos in pm.holdings.items():
                price = prices.get(t, pos["avg_price"])
                rows.append({"Ticker": t, "Qty": pos["qty"], "Avg Cost": pos["avg_price"], "Price": price,
                             "Market Value": price * pos["qty"], "P&L": (price - pos["avg_price"]) * pos["qty"],
                             "P&L %": (price - pos["avg_price"]) / pos["avg_price"] * 100 if pos["avg_price"] else 0})
            df = pd.DataFrame(rows).sort_values("Market Value", ascending=False)
            st.dataframe(df.style.format({"Avg Cost": "{:.2f}", "Price": "{:.2f}", "Market Value": "{:,.2f}",
                                          "P&L": "{:+,.2f}", "P&L %": "{:+.2f}%"})
                         .background_gradient(subset=["P&L %"], cmap="RdYlGn", vmin=-20, vmax=20),
                         use_container_width=True, hide_index=True)
            st.markdown("##### ⚠️ Risk check")
            weights = [(t, (prices.get(t, p["avg_price"]) * p["qty"]) / max(tv, 1) * 100) for t, p in pm.holdings.items()]
            for n in risk_check(weights):
                st.markdown(f"- {n}")
    with t2:
        if not pm.holdings:
            st.info("Nothing to allocate yet.")
        else:
            labels, values = [], []
            for t, pos in pm.holdings.items():
                labels.append(t)
                values.append(prices.get(t, pos["avg_price"]) * pos["qty"])
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
                st.markdown(f"**{j['ticker']}** · <span class='mono' style='color:#9AA3B8'>{j['ts'][:16].replace('T',' ')}</span>", unsafe_allow_html=True)
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
        st.warning("Resets cash, holdings, transactions, journal, and badges for this profile.")
        if st.button("Reset this profile"):
            pm.reset()
            st.success("Reset.")
            st.rerun()


def page_watchlist(pm, prices):
    hero("Watchlist", "Track stocks you're interested in without buying them.", "⭐")
    with st.form("addw", clear_on_submit=True):
        c1, c2 = st.columns([4, 1])
        nt = c1.text_input("Add a ticker", placeholder="e.g. NVDA, HDFCBANK.NS", label_visibility="collapsed")
        if c2.form_submit_button("➕ Add", use_container_width=True) and nt.strip():
            pm.add_watch(nt.strip().upper())
            st.rerun()
    st.markdown("##### Suggestions")
    sugg = POPULAR_US if pm.currency == "USD" else POPULAR_IN
    cols = st.columns(6)
    for i, s in enumerate(sugg):
        with cols[i % 6]:
            if s not in pm.d["watchlist"] and st.button(f"+ {s}", key=f"sg_{s}", use_container_width=True):
                pm.add_watch(s)
                st.rerun()
    st.markdown("---")
    wl = pm.d["watchlist"]
    if not wl:
        st.info("Your watchlist is empty.")
        return
    quotes = get_quotes_batch(tuple(wl))
    for t in wl:
        q = quotes.get(t)
        card_open()
        cols = st.columns([1.4, 1, 1, 1, 1, 0.8])
        cols[0].markdown(f"**{t}**  \n<span style='color:#9AA3B8;font-size:0.82rem'>{q.get('name', t) if q else t}</span>", unsafe_allow_html=True)
        if q and q.get("ok"):
            cols[1].markdown(f"<span class='mono'>{fmt_money(q['price'], q['currency'])}</span>", unsafe_allow_html=True)
            cols[2].markdown(change_pill(q["change_pct"]), unsafe_allow_html=True)
            cols[3].markdown(f"52W H: <span class='mono'>{fmt_money(q.get('year_high'), q['currency']) if q.get('year_high') else '—'}</span>", unsafe_allow_html=True)
            cols[4].markdown(f"52W L: <span class='mono'>{fmt_money(q.get('year_low'), q['currency']) if q.get('year_low') else '—'}</span>", unsafe_allow_html=True)
        else:
            cols[1].write("—")
            cols[2].write("No data")
        if cols[5].button("Remove", key=f"rm_{t}"):
            pm.remove_watch(t)
            st.rerun()
        card_close()


def page_charts(pm, prices):
    hero("Charts", "Real OHLCV data with candlesticks, moving averages, Bollinger Bands, RSI & MACD.", "📉")
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        ticker = st.text_input("Ticker", value=st.session_state.get("chart_ticker", "AAPL")).strip().upper()
        st.session_state["chart_ticker"] = ticker
    with c2:
        tf = st.select_slider("Timeframe", options=list(PERIOD_INTERVAL.keys()), value="6M")
    with c3:
        overlays = st.multiselect("Overlays", ["SMA 20", "SMA 50", "Bollinger Bands"], default=["SMA 20", "SMA 50"])
    show_rsi = st.checkbox("RSI panel", value=True)
    show_macd = st.checkbox("MACD panel", value=True)
    if not ticker:
        return
    period, interval = PERIOD_INTERVAL[tf]
    with st.spinner("Loading real price history..."):
        df = get_history(ticker, period, interval)
        q = get_quote(ticker)
    if df.empty:
        st.error(f"No chart data for '{ticker}'.")
        return
    snap = signal_snapshot(df)
    if q.get("ok"):
        h1, h2, h3 = st.columns([2, 1, 1])
        h1.markdown(f"### {q['name']} · `{ticker}`  " + change_pill(q["change_pct"]), unsafe_allow_html=True)
        h2.metric("Price", fmt_money(q["price"], q["currency"]))
        h3.metric("RSI (14)", f"{snap.get('rsi', 0):.1f}" if snap.get("rsi") is not None else "—")
    rows = 1 + int(show_rsi) + int(show_macd)
    heights = [0.6] + [0.2] * (rows - 1) if rows > 1 else [1.0]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, row_heights=heights, vertical_spacing=0.03)
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
    fig.update_layout(**PLOTLY_LAYOUT, height=650, xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h", y=1.02, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown("#### 🤖 Technical read")
    card_open()
    st.write(technical_narrative(ticker, snap))
    card_close()


def page_ai(pm, prices):
    hero("AI Coach", "Educational, data-grounded commentary. Not investment advice.", "🤖")
    ticker = st.text_input("Ask about a ticker", value=st.session_state.get("chart_ticker", "AAPL")).strip().upper()
    q = snap = None
    news = []
    if ticker:
        with st.spinner("Analyzing real data..."):
            df = get_history(ticker, "6mo", "1d")
            q = get_quote(ticker)
            news = get_news(ticker, 6)
        if df.empty or not q.get("ok"):
            st.error("Couldn't load data for that ticker.")
        else:
            snap = signal_snapshot(df)
            sent = news_sentiment_summary(news)
            c1, c2, c3 = st.columns(3)
            c1.metric("Price", fmt_money(q["price"], q["currency"]), f"{q['change_pct']:+.2f}%")
            c2.metric("RSI (14)", f"{snap.get('rsi', 0):.1f}" if snap.get("rsi") is not None else "—")
            c3.metric("News tone", sent["label"])
            st.markdown("##### 📊 Technical read (always available)")
            card_open()
            st.write(technical_narrative(ticker, snap))
            card_close()
            if pm.holdings:
                st.markdown("##### ⚠️ Portfolio risk check")
                card_open()
                tv = pm.total_value(prices)
                for n in risk_check([(t, (prices.get(t, p["avg_price"]) * p["qty"]) / max(tv, 1) * 100) for t, p in pm.holdings.items()]):
                    st.markdown(f"- {n}")
                card_close()
    st.markdown("---")
    st.markdown("### 💬 Ask the live AI Coach")
    key = st.session_state.get("anthropic_api_key", "")
    if not key:
        st.info("Add an Anthropic API key in Settings to unlock conversational Q&A grounded in this data. Rule-based insights above work without a key.")
    question = st.text_area("Your question", placeholder="e.g. Why might RSI matter here? What would diversifying look like?")
    if st.button("Ask", type="primary", disabled=not question.strip()):
        ctx = {"ticker": ticker, "price": q.get("price") if q else None, "rsi": snap.get("rsi") if snap else None,
               "sma20": snap.get("sma20") if snap else None, "sma50": snap.get("sma50") if snap else None,
               "recent_headlines": [n["title"] for n in news[:5]], "user_cash": pm.cash,
               "user_currency": pm.currency, "user_holdings": dict(pm.holdings),
               "user_total_return_pct": pm.total_return_pct(prices)}
        with st.spinner("Thinking..."):
            ans = ask_ai_coach(key, st.session_state.get("ai_model", "claude-sonnet-5"), ctx, question)
        card_open()
        st.markdown(ans)
        card_close()


def page_news(pm, prices):
    hero("News", "Real headlines via yfinance, with a simple keyword-based sentiment tag.", "📰")
    pool = list(dict.fromkeys(list(pm.holdings.keys()) + pm.d["watchlist"])) or ["AAPL"]
    ticker = st.selectbox("Ticker", pool + ["Other..."])
    if ticker == "Other...":
        ticker = st.text_input("Enter ticker").strip().upper()
    if not ticker:
        return
    with st.spinner("Fetching headlines..."):
        news = get_news(ticker, 12)
    if not news:
        st.info("No recent headlines found for this ticker.")
        return
    s = news_sentiment_summary(news)
    st.markdown(f"**Overall tone:** {s['label']} · {s['pos']} positive / {s['neg']} negative / {s['neu']} neutral")
    st.write("")
    for n in news:
        sc = headline_sentiment(n["title"])
        tag = pill("Positive", "green") if sc > 0 else (pill("Negative", "red") if sc < 0 else pill("Neutral", "amber"))
        card_open()
        st.markdown(f"{tag} &nbsp; **[{n['title']}]({n['link']})**", unsafe_allow_html=True)
        st.caption(n.get("publisher", ""))
        card_close()


def page_learn(pm, prices):
    hero("Learn", "Every concept used elsewhere in Fictrade, explained simply.", "🎓")
    topics = [
        ("💵 Market order", "Buys/sells immediately at the current price. Fictrade simulates market orders only; real platforms also offer limit orders."),
        ("📉 RSI", "A 0–100 momentum gauge. Above 70 = 'overbought', below 30 = 'oversold' — a clue, not a rule, since strong trends can stay extended."),
        ("📈 Moving averages", "The average close over N days, smoothing noise so you see the trend. SMA weights days equally; EMA weights recent days more."),
        ("🎯 MACD", "Difference between a fast and slow EMA. Crossing above its signal line = momentum turning up; below = turning down."),
        ("🎈 Bollinger Bands", "A band 2 standard deviations above/below a moving average. Near the upper band = trading high vs recent volatility; a tight squeeze often precedes a bigger move."),
        ("🧺 Diversification", "Spreading money across uncorrelated assets so one bad outcome doesn't sink the portfolio. Fictrade flags when one position dominates."),
        ("💼 P/E ratio", "Price ÷ earnings per share — roughly how much investors pay per unit of profit. Useful comparing similar companies."),
        ("📉 Drawdown", "The % drop from a peak to the following trough. Measures how painful the ride was, separate from final return."),
        ("🩹 Realized vs unrealized P&L", "Unrealized = paper gain/loss on something you still hold. Realized = locked in once you actually sell."),
        ("📓 Why journal trades", "Writing down WHY you traded, before you know the outcome, is one of the few habits with real evidence for improving decisions."),
    ]
    for t, b in topics:
        with st.expander(t):
            st.write(b)
    st.markdown("---")
    st.info("🎮 Fictrade is a simulator. Prices are real (yfinance); every buy/sell is fictional play-money with no real brokerage.")


def page_leaderboard(pm, prices):
    hero("Leaderboard", "Every trading profile this session, ranked by fictional return.", "🏆")
    profiles = st.session_state["profiles"]
    if len(profiles) <= 1:
        st.info("Create more profiles from the sidebar (try different strategies side by side) to populate a leaderboard.")
    all_tickers = set()
    for d in profiles.values():
        all_tickers |= set(d["holdings"].keys())
    quotes = get_quotes_batch(tuple(all_tickers)) if all_tickers else {}
    rows = []
    for name, d in profiles.items():
        m = Portfolio(d)
        lookup = {t: q["price"] for t, q in quotes.items() if q and q.get("ok") and t in d["holdings"]}
        rows.append({"Trader": name, "Currency": d["currency"], "Net Worth": m.total_value(lookup),
                     "Return %": m.total_return_pct(lookup), "Trades": len(m.transactions),
                     "Level": m.level(), "Badges": len(d["badges"])})
    df = pd.DataFrame(rows).sort_values("Return %", ascending=False).reset_index(drop=True)
    medal = {0: "🥇", 1: "🥈", 2: "🥉"}
    df["Rank"] = [f"{medal.get(i,'')} #{i+1}" for i in range(len(df))]
    df = df[["Rank", "Trader", "Currency", "Net Worth", "Return %", "Trades", "Level", "Badges"]]
    st.dataframe(df.style.format({"Net Worth": "{:,.2f}", "Return %": "{:+.2f}%"})
                 .background_gradient(subset=["Return %"], cmap="RdYlGn", vmin=-30, vmax=30),
                 use_container_width=True, hide_index=True)


def page_settings(pm, prices):
    hero("Settings", "AI configuration and about this simulator.", "⚙️")
    st.markdown("### 🤖 AI Coach configuration")
    card_open()
    st.write("The rule-based AI Coach works with zero setup. Adding an Anthropic API key unlocks conversational Q&A on the AI Coach page, grounded in the same real market data.")
    key = st.text_input("Anthropic API key", value=st.session_state.get("anthropic_api_key", ""), type="password", placeholder="sk-ant-...")
    model = st.selectbox("Model", ["claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"],
                         index=["claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"].index(st.session_state.get("ai_model", "claude-sonnet-5")))
    if st.button("Save AI settings"):
        st.session_state["anthropic_api_key"] = key
        st.session_state["ai_model"] = model
        st.success("Saved for this session.")
    st.caption("Note: on a hosted deployment the key lives only in your browser session and is sent only to Anthropic when you ask a question.")
    card_close()
    st.markdown("### ℹ️ About Fictrade")
    card_open()
    st.markdown("- **Data:** real market data via yfinance (Yahoo Finance), typically delayed — not a live broker feed.\n"
                "- **Trading:** 100% fictional. No brokerage, no real orders, no real money, ever.\n"
                "- **Accounts & storage:** your account and all its data are saved in **this browser on this device** "
                "(localStorage) — there's no central server database. So your portfolio is here when you return on the "
                "same browser, but it doesn't follow you to other devices, and the login is a lightweight local lock, "
                "not bank-grade security. Don't reuse an important password.\n"
                "- **Not investment advice.** Every AI note is educational commentary on public data.")
    card_close()
    st.markdown("### 🔐 Account")
    card_open()
    st.write(f"Signed in as **{st.session_state.get('user','Guest')}**"
             + (" (guest — nothing is saved)" if st.session_state.get("is_guest", True) else "."))
    if st.button("Log out"):
        logout()
        st.rerun()
    card_close()


# =============================================================================
# MAIN
# =============================================================================
def main():
    load_db()
    ensure_defaults()

    # Not logged in -> show the account gate and stop.
    if "user" not in st.session_state:
        auth_gate()
        save_db()
        return

    inject_css()
    pm, prices, page = render_sidebar()
    router = {
        "🏠 Dashboard": page_dashboard, "💰 Trade": page_trade, "📊 Portfolio": page_portfolio,
        "⭐ Watchlist": page_watchlist, "📉 Charts": page_charts, "🤖 AI Coach": page_ai,
        "📰 News": page_news, "🎓 Learn": page_learn, "🏆 Leaderboard": page_leaderboard, "⚙️ Settings": page_settings,
    }
    router[page](pm, prices)

    # Persist any changes made this run (no-op for guests / unchanged state).
    save_db()


if __name__ == "__main__":
    main()
