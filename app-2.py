import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from isamee import isamee_logic

st.set_page_config(page_title="Isamee Robot", page_icon="🤖", layout="wide")

# ---------- DESIGN ----------
st.markdown(
    """
<style>
.stApp {
    background: radial-gradient(1200px 600px at 10% -10%, #1b2a4a 0%, #0b1020 55%, #070a14 100%);
    color: #e8ecf5;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; max-width: 1100px; }
.brand { display:flex; align-items:center; gap:12px; margin-bottom:.4rem; }
.brand .logo { font-size:2.2rem; }
.brand h1 { margin:0; font-size:1.7rem; letter-spacing:.5px;
    background: linear-gradient(90deg,#7aa2ff,#9b7bff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.live-dot { display:inline-block; width:10px; height:10px; border-radius:50%;
    background:#00e676; margin-right:6px; animation:pulse 1.2s infinite; }
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(0,230,118,.7);} 100%{box-shadow:0 0 0 12px rgba(0,230,118,0);} }
.sigcard { border-radius:20px; padding:22px 24px; margin:10px 0 14px 0;
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;
    border:1px solid rgba(255,255,255,.08); backdrop-filter: blur(6px); }
.sig-buy  { background:linear-gradient(135deg,rgba(0,200,83,.28),rgba(0,200,83,.07)); border-color:rgba(0,230,118,.5); }
.sig-sell { background:linear-gradient(135deg,rgba(255,23,68,.28),rgba(255,23,68,.07)); border-color:rgba(255,82,82,.5); }
.sig-wait { background:linear-gradient(135deg,rgba(255,193,7,.18),rgba(255,193,7,.05)); border-color:rgba(255,193,7,.35); }
.sig-live { background:linear-gradient(135deg,rgba(80,120,255,.22),rgba(80,120,255,.05)); border-color:rgba(122,162,255,.4); }
div.stButton > button { border-radius:16px; padding:.85rem 1rem; font-size:1.1rem; font-weight:700;
    border:1px solid rgba(255,255,255,.15); }
div.stButton > button[kind="primary"] { background:linear-gradient(90deg,#4f7bff,#8a5cff); color:white; border:none; }
.sigcard .big { font-size:2.4rem; font-weight:800; line-height:1; }
.sigcard .sub { opacity:.75; font-size:.9rem; margin-top:4px; }
.sigcard .price { font-size:1.9rem; font-weight:700; text-align:right; }
.metric-box { background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08);
    border-radius:16px; padding:14px 16px; text-align:center; }
.metric-box .l { opacity:.65; font-size:.8rem; text-transform:uppercase; letter-spacing:1px; }
.metric-box .v { font-size:1.5rem; font-weight:700; margin-top:2px; }
div[data-baseweb="select"] > div { background:rgba(255,255,255,.06); border-radius:12px; border:1px solid rgba(255,255,255,.12); }
.foot { opacity:.5; font-size:.78rem; margin-top:10px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="brand"><span class="logo">🤖</span><h1>Isamee Robot</h1></div>'
    '<div><span class="live-dot"></span>LIVE · suuqa wuu socdaa, signal-ka marka aad weydiiso ayuu soo baxaa</div>',
    unsafe_allow_html=True,
)

# ---------- DOORASHO ----------
MARKETS = {
    "🌍 Forex": {
        "🇪🇺🇺🇸  EUR/USD": "EURUSD=X",
        "🇬🇧🇺🇸  GBP/USD": "GBPUSD=X",
        "🇺🇸🇯🇵  USD/JPY": "USDJPY=X",
        "🇦🇺🇺🇸  AUD/USD": "AUDUSD=X",
        "🇺🇸🇨🇦  USD/CAD": "USDCAD=X",
        "🇺🇸🇨🇭  USD/CHF": "USDCHF=X",
        "🇳🇿🇺🇸  NZD/USD": "NZDUSD=X",
        "🇪🇺🇬🇧  EUR/GBP": "EURGBP=X",
        "🇪🇺🇯🇵  EUR/JPY": "EURJPY=X",
        "🇬🇧🇯🇵  GBP/JPY": "GBPJPY=X",
    },
    "₿ Crypto": {
        "₿  BTC/USD": "BTC-USD",
        "Ξ  ETH/USD": "ETH-USD",
        "◎  SOL/USD": "SOL-USD",
        "🪙  BNB/USD": "BNB-USD",
        "✕  XRP/USD": "XRP-USD",
        "🐕  DOGE/USD": "DOGE-USD",
        "🔷  ADA/USD": "ADA-USD",
    },
    "📈 Stocks": {
        "🇺🇸  Apple (AAPL)": "AAPL",
        "🇺🇸  Tesla (TSLA)": "TSLA",
        "🇺🇸  Nvidia (NVDA)": "NVDA",
        "🇺🇸  Microsoft (MSFT)": "MSFT",
        "🇺🇸  Amazon (AMZN)": "AMZN",
        "🇺🇸  Google (GOOGL)": "GOOGL",
        "🇺🇸  Meta (META)": "META",
    },
    "🥇 Commodities": {
        "🥇  Gold (XAU)": "GC=F",
        "🥈  Silver (XAG)": "SI=F",
        "🛢️  Oil (WTI)": "CL=F",
        "🛢️  Oil (Brent)": "BZ=F",
        "🔥  Natural Gas": "NG=F",
    },
    "🏛️ Indices": {
        "🇺🇸  S&P 500": "^GSPC",
        "🇺🇸  Nasdaq": "^IXIC",
        "🇺🇸  Dow Jones": "^DJI",
        "🇩🇪  DAX": "^GDAXI",
        "🇬🇧  FTSE 100": "^FTSE",
        "🇯🇵  Nikkei 225": "^N225",
    },
}
# magac: (interval, period)
TIMEFRAMES = {
    "1 daqiiqo": ("1m", "1d"),
    "2 daqiiqo": ("2m", "5d"),
    "5 daqiiqo": ("5m", "5d"),
    "15 daqiiqo": ("15m", "5d"),
    "30 daqiiqo": ("30m", "1mo"),
    "1 saac": ("1h", "1mo"),
}

market = st.radio("Suuqa", list(MARKETS.keys()), horizontal=True)
if market != "₿ Crypto":
    st.caption("ℹ️ Suuqan wuxuu leeyahay saacado furan; dhammaadka toddobaadka ama habeenkii xog cusub ma timaado.")

c1, c2, c3 = st.columns([2, 1.3, 1])
pairs = MARKETS[market]
pair_name = c1.selectbox("Lacagta / Hanti", list(pairs.keys()), key=f"pair_{market}")
tf_name = c2.selectbox("Waqtiga (timeframe)", list(TIMEFRAMES.keys()))
candles = c3.selectbox("Shamacyo", [40, 60, 80, 120], index=1)

symbol = pairs[pair_name]
interval, period = TIMEFRAMES[tf_name]


@st.cache_data(ttl=2, show_spinner=False)
def get_data(sym, itv, per):
    df = yf.download(sym, period=per, interval=itv, progress=False, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    df = df.rename(columns={df.columns[0]: "Date"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    return df[["Date", "Open", "High", "Low", "Close"]].dropna().reset_index(drop=True)


def fmt(p):
    return f"{p:.5f}" if p < 10 else f"{p:,.2f}"


def metric(label, value):
    return f'<div class="metric-box"><div class="l">{label}</div><div class="v">{value}</div></div>'


def compute_signal(sym, itv, per):
    """Xogta cusub ayaa la qaadaa, signal-kuna waa shamaca ugu dambeeyay ee la xiray."""
    raw = get_data(sym, itv, per)
    if raw is None or len(raw) < 40:
        return None
    df = isamee_logic(raw.iloc[:-1])
    last = df.iloc[-1]
    return {
        "key": (sym, itv),
        "signal": last["Signal"],
        "price": float(raw["Close"].iloc[-1]),
        "rsi": float(last["RSI"]),
        "adx": float(last["ADX"]),
        "candle": last["Date"],
        "ts": time.time(),
    }


# ---------- BADHANKA: IISHEEG ----------
ask = st.button("🎯  Ii sheeg: BUY mise SELL?", type="primary", use_container_width=True)
if ask:
    try:
        res = compute_signal(symbol, interval, period)
        if res is None:
            st.warning("⏳ Xog ku filan ma jirto (suuqu wuu xiranyahay, ama internet ma jiro).")
        else:
            st.session_state["answer"] = res
    except Exception as e:
        st.error(f"Khalad xogta: {e}")


@st.fragment(run_every=2)
def live_view(sym, itv, per, pname, tfname, n):
    try:
        raw = get_data(sym, itv, per)
    except Exception as e:
        st.error(f"Khalad xogta: {e}")
        return

    if raw is None or len(raw) < 40:
        st.warning("⏳ Xog ku filan ma jirto (suuqu wuu xiranyahay, ama internet ma jiro).")
        return

    price_now = float(raw["Close"].iloc[-1])
    df = isamee_logic(raw.iloc[:-1])  # shamaca la xiray oo keliya
    last = df.iloc[-1]

    # --- qiimaha live ---
    st.markdown(
        f'<div class="sigcard sig-live"><div><div class="big" style="font-size:1.4rem">{pname}</div>'
        f'<div class="sub">{tfname} · LIVE</div></div>'
        f'<div class="price">{fmt(price_now)}</div></div>',
        unsafe_allow_html=True,
    )

    # --- jawaabta (kaliya markii la weydiiyo) ---
    ans = st.session_state.get("answer")
    if ans and ans["key"] == (sym, itv):
        sig = ans["signal"]
        cls = {"BUY": "sig-buy", "SELL": "sig-sell"}.get(sig, "sig-wait")
        txt = {"BUY": "🚀 BUY", "SELL": "📉 SELL"}.get(sig, "📊 WAIT")
        hint = {"BUY": "Trend-ku wuu kor u socdaa", "SELL": "Trend-ku wuu hoos u socdaa"}.get(
            sig, "Fursad cad ma jirto, sug")
        age = int(time.time() - ans["ts"])
        move = (price_now - ans["price"]) / ans["price"] * 100
        st.markdown(
            f'<div class="sigcard {cls}"><div><div class="big">{txt}</div>'
            f'<div class="sub">{hint}</div>'
            f'<div class="sub">La weydiiyay {age} ilbiriqsi ka hor · qiimo markaas {fmt(ans["price"])} '
            f'· isbeddel {move:+.3f}%</div></div>'
            f'<div class="price" style="font-size:1.1rem">RSI {ans["rsi"]:.1f}<br>ADX {ans["adx"]:.1f}</div></div>',
            unsafe_allow_html=True,
        )
        if age > 120:
            st.caption("⚠️ Jawaabtan way duugowday, riix badhanka mar kale si aad u hesho mid cusub.")
    else:
        st.info("Riix **🎯 Ii sheeg** si aad u hesho signal-ka suuqan hadda.")

    m1, m2, m3 = st.columns(3)
    m1.markdown(metric("RSI (5)", f"{last['RSI']:.1f}"), unsafe_allow_html=True)
    m2.markdown(metric("ADX (14)", f"{last['ADX']:.1f}"), unsafe_allow_html=True)
    m3.markdown(metric("Shamac la xiray", f"{last['Date']:%H:%M}"), unsafe_allow_html=True)

    d = df.tail(n)
    fig = go.Figure(
        go.Candlestick(
            x=d["Date"], open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"],
            increasing_line_color="#00e676", decreasing_line_color="#ff5252", name="Price",
        )
    )
    fig.update_layout(
        template="plotly_dark", height=520, xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
        margin=dict(l=8, r=8, t=8, b=8), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f'<div class="foot">Cusboonaysiin: {pd.Timestamp.now():%H:%M:%S} · '
        "Xogta yfinance way dib u dhacdaa, faa'iido lama hubo. Ku tijaabi akoon demo.</div>",
        unsafe_allow_html=True,
    )


live_view(symbol, interval, period, pair_name.strip(), tf_name, candles)
