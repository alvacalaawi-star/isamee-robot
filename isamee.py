"""
ISAMEE ROBOT (hal fayl) - wuxuu leeyahay laba habka:
  python isamee.py            -> LIVE (xogta suuqa oo marwalba socota)
  python isamee.py csv        -> Xogta faylka CSV (PocketOption_EURUSD.csv)
  python isamee.py csv GBPUSD -> CSV kale

Rakib: pip install pandas numpy yfinance mplfinance
Jooji LIVE: Ctrl + C
"""
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

# mplfinance waa ikhtiyaari (haddii aan la rakibin, jaantuska waa la boodayaa)
try:
    import mplfinance as mpf
except ImportError:
    mpf = None


# ---------- 1. XOGTA ----------
def load_data(symbol="EURUSD"):
    """CSV-ga waa inuu leeyahay: Date, Open, High, Low, Close (Volume ikhtiyaari)."""
    file = f"PocketOption_{symbol}.csv"
    try:
        df = pd.read_csv(file)
    except FileNotFoundError:
        raise SystemExit(f"Faylka '{file}' lama helin. Dhig isla folder-ka code-ka.")

    needed = {"Date", "Open", "High", "Low", "Close"}
    missing = needed - set(df.columns)
    if missing:
        raise SystemExit(f"CSV-ga wuxuu ka maqan yahay tiirarkan: {missing}")

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


# ---------- 2. INDICATORS (pandas_ta looma baahna) ----------
def rsi(close, length=14):
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / length, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / length, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def adx(high, low, close, length=14):
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)

    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)

    alpha = 1 / length
    atr = tr.ewm(alpha=alpha, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=high.index).ewm(alpha=alpha, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(alpha=alpha, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(alpha=alpha, adjust=False).mean()


# ---------- 3. LOGIC-KA ----------
def isamee_logic(df, fast=5, slow=20):
    df = df.copy()
    df[f"MA_{fast}"] = df["Close"].rolling(fast).mean()
    df[f"MA_{slow}"] = df["Close"].rolling(slow).mean()
    df["RSI"] = rsi(df["Close"], 5)           # RSI(5) - degdeg
    df["ADX"] = adx(df["High"], df["Low"], df["Close"], 14)  # ADX(14)
    df["High_Momentum"] = df["High"].rolling(20).max().shift(1)  # sare 20-shamac ee hore

    trend = df["ADX"] > 25
    up = df[f"MA_{fast}"] > df[f"MA_{slow}"]
    down = df[f"MA_{fast}"] < df[f"MA_{slow}"]

    # Shuruudaha ka yimid extrait__1_.py
    buy_trend = trend & up & (df["RSI"] > 35) & (df["RSI"] < 55)
    sell_trend = trend & down & (df["RSI"] > 45) & (df["RSI"] < 65)
    # Breakout degdeg ah
    buy_break = df["Close"] > df["High_Momentum"]

    df["Signal"] = "WAIT"
    df.loc[sell_trend, "Signal"] = "SELL"
    df.loc[buy_trend | buy_break, "Signal"] = "BUY"
    return df


# ---------- 4. ARAG ----------
def display_robot(df):
    last = df.iloc[-1]
    print(f"\n🤖 ISAMEE ROBOT - {last['Date']}\n")
    if last["Signal"] == "BUY":
        print("🚀 HABKA: BUY (Trend-ku wuu kor u socdaa)\n")
    elif last["Signal"] == "SELL":
        print("📉 HABKA: SELL (Trend-ku wuu hoos u socdaa)\n")
    else:
        print("📊 HABKA: WAIT (Sugo)\n")


def plot_chart(df):
    if mpf is None:
        print("mplfinance lama rakibin: pip install mplfinance")
        return
    d = df.set_index("Date")  # mplfinance wuxuu u baahan yahay DatetimeIndex
    buys = d["Close"].where(d["Signal"] == "BUY")
    sells = d["Close"].where(d["Signal"] == "SELL")
    add = []
    if buys.notna().any():
        add.append(mpf.make_addplot(buys, type="scatter", marker="^", markersize=50, color="g"))
    if sells.notna().any():
        add.append(mpf.make_addplot(sells, type="scatter", marker="v", markersize=50, color="r"))
    mpf.plot(
        d, type="candle", style="charles", title="Isamee Robot",
        ylabel="Price", volume="Volume" in d.columns, addplot=add,
    )


# ---------- 5. LIVE ----------
SYMBOL = "EURUSD=X"     # EUR/USD (yfinance). Tusaale kale: GBPUSD=X, USDJPY=X
INTERVAL = "1m"         # shamac 1 daqiiqo ah
REFRESH_SECONDS = 30    # mar kasta oo xogta la cusboonaysiiyo


def fetch_live(symbol=SYMBOL, interval=INTERVAL):
    """Soo qaad shamacyadii ugu dambeeyay oo u beddel qaab robot-ku aqoonsado."""
    if yf is None:
        raise SystemExit("Marka hore: pip install yfinance")

    df = yf.download(symbol, period="1d", interval=interval,
                     progress=False, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()

    # yfinance cusub wuxuu mararka qaar soo celiyaa tiirar MultiIndex ah
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df = df.rename(columns={df.columns[0]: "Date"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    return df[["Date", "Open", "High", "Low", "Close"]].dropna().reset_index(drop=True)


def run_live(fetch=fetch_live, refresh=REFRESH_SECONDS, max_loops=None):
    print(f"🤖 Isamee LIVE bilaabmay - {SYMBOL} ({INTERVAL}). Ctrl+C si aad u joojiso.\n")
    last_candle = None
    last_signal = None
    loops = 0

    while True:
        loops += 1
        try:
            df = fetch()
            if len(df) < 40:
                print("⏳ Xog ku filan ma jirto weli (suuqu wuu xiranyahay?)...")
            else:
                price_now = df["Close"].iloc[-1]          # qiimaha hadda
                closed = df.iloc[:-1]                     # shamaca la xiray oo keliya
                closed = isamee_logic(closed)
                row = closed.iloc[-1]

                new_candle = row["Date"] != last_candle
                changed = row["Signal"] != last_signal
                now = datetime.now().strftime("%H:%M:%S")

                if new_candle or changed:
                    icon = {"BUY": "🚀", "SELL": "📉"}.get(row["Signal"], "📊")
                    print(f"[{now}] {icon} {row['Signal']:<4} | shamac {row['Date']:%H:%M} "
                          f"| RSI {row['RSI']:.1f} | ADX {row['ADX']:.1f} | qiimo {price_now:.5f}")
                    last_candle, last_signal = row["Date"], row["Signal"]
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"⚠️ Khalad xogta: {e} - dib ayaan isku dayayaa...")

        if max_loops and loops >= max_loops:
            return
        time.sleep(refresh)


try:
    import yfinance as yf
except ImportError:
    yf = None


if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "live"
    if mode == "csv":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "EURUSD"
        data = isamee_logic(load_data(symbol))
        display_robot(data)
        for _, row in data.tail(30).iterrows():
            print(f"{row['Date']} - Signal: {row['Signal']} - Price: {row['Close']:.5f}")
        plot_chart(data)
    else:
        try:
            run_live()
        except KeyboardInterrupt:
            print("\n🛑 Waa la joojiyay.")
