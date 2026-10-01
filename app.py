import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from isamee import fetch_live, isamee_logic

st.set_page_config(page_title="Isamee Robot", page_icon="🤖", layout="wide")
st.title("🤖 Isamee Robot - LIVE")

symbol = st.sidebar.selectbox(
    "Suuqa", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "BTC-USD"]
)
refresh = st.sidebar.slider("Cusboonaysii (ilbiriqsi)", 15, 120, 30)
candles = st.sidebar.slider("Tirada shamacyada jaantuska", 30, 200, 80)
st.sidebar.caption("Signal-ku wuxuu ku salaysan yahay shamaca la xiray. "
                   "Xogta yfinance way dib u dhacdaa; faa'iido lama hubo. "
                   "Ku tijaabi akoon demo.")


@st.cache_data(ttl=15)
def get_data(sym):
    return fetch_live(sym)


@st.fragment(run_every=refresh)
def live_view():
    try:
        raw = get_data(symbol)
    except Exception as e:
        st.error(f"Khalad xogta: {e}")
        return

    if raw is None or len(raw) < 40:
        st.warning("⏳ Xog ku filan ma jirto (suuqu wuu xiranyahay ama internet ma jiro).")
        return

    price_now = raw["Close"].iloc[-1]
    df = isamee_logic(raw.iloc[:-1])  # shamaca la xiray oo keliya
    last = df.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    icon = {"BUY": "🚀 BUY", "SELL": "📉 SELL"}.get(last["Signal"], "📊 WAIT")
    c1.metric("Signal", icon)
    c2.metric("Qiimaha hadda", f"{price_now:.5f}")
    c3.metric("RSI(5)", f"{last['RSI']:.1f}")
    c4.metric("ADX(14)", f"{last['ADX']:.1f}")

    d = df.tail(candles)
    fig = go.Figure(go.Candlestick(
        x=d["Date"], open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"],
        name="Price"))
    buys, sells = d[d["Signal"] == "BUY"], d[d["Signal"] == "SELL"]
    fig.add_trace(go.Scatter(x=buys["Date"], y=buys["Low"], mode="markers", name="BUY",
                             marker=dict(symbol="triangle-up", size=11, color="green")))
    fig.add_trace(go.Scatter(x=sells["Date"], y=sells["High"], mode="markers", name="SELL",
                             marker=dict(symbol="triangle-down", size=11, color="red")))
    fig.update_layout(height=550, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Signals-kii ugu dambeeyay")
    sig = df[df["Signal"] != "WAIT"].tail(10)[["Date", "Signal", "Close", "RSI", "ADX"]]
    st.dataframe(sig.iloc[::-1], hide_index=True, use_container_width=True)
    st.caption(f"Cusboonaysiin ugu dambeeyay: {pd.Timestamp.now():%H:%M:%S}")


live_view()
