import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import os

from concurrent.futures import ThreadPoolExecutor

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="⚡ AI Momentum Scanner",
    layout="wide"
)

st.title("🚀 AI Momentum Stock Scanner")

st.write(
    "Find High Momentum Stocks Fast"
)

# -----------------------------------
# WATCHLIST FILE
# -----------------------------------

WATCHLIST_FILE = "watchlist.csv"

if os.path.exists(WATCHLIST_FILE):

    watchlist_df = pd.read_csv(
        WATCHLIST_FILE
    )

    watchlist = watchlist_df[
        "Stock"
    ].tolist()

else:

    watchlist = []

# -----------------------------------
# LOAD STOCKS
# -----------------------------------

stock_df = pd.read_csv(
    "stocks.csv"
)

# -----------------------------------
# FAST MODE
# -----------------------------------

stocks = stock_df[
    "Symbol"
].dropna().tolist()[:100]

# -----------------------------------
# SIDEBAR
# -----------------------------------

st.sidebar.header(
    "⚙ Scanner Settings"
)

min_price = st.sidebar.number_input(
    "Minimum Price",
    value=20
)

max_workers = st.sidebar.slider(
    "Scanning Threads",
    20,
    200,
    100
)

min_score = st.sidebar.slider(
    "Minimum AI Score",
    20,
    100,
    60
)

# -----------------------------------
# CACHE
# -----------------------------------

@st.cache_data(ttl=3600)

def analyze_stock(stock):

    try:

        # -----------------------------------
        # DOWNLOAD
        # -----------------------------------

        df = yf.download(
            stock,
            period="1mo",
            interval="1d",
            progress=False,
            auto_adjust=True,
            threads=False
        )

        # -----------------------------------
        # VALIDATION
        # -----------------------------------

        if df.empty:

            return None

        if len(df) < 20:

            return None

        # -----------------------------------
        # FIX DATA
        # -----------------------------------

        close_series = pd.Series(
            df["Close"]
            .to_numpy()
            .flatten()
        )

        high_series = pd.Series(
            df["High"]
            .to_numpy()
            .flatten()
        )

        volume_series = pd.Series(
            df["Volume"]
            .to_numpy()
            .flatten()
        )

        # -----------------------------------
        # PRICE
        # -----------------------------------

        close = float(
            close_series.iloc[-1]
        )

        if close < min_price:

            return None

        # -----------------------------------
        # RSI
        # -----------------------------------

        rsi_indicator = ta.momentum.RSIIndicator(
            close=close_series
        )

        rsi_series = rsi_indicator.rsi()

        # -----------------------------------
        # MOVING AVERAGES
        # -----------------------------------

        ma20_series = close_series.rolling(
            20
        ).mean()

        ma50_series = close_series.rolling(
            50
        ).mean()

        # -----------------------------------
        # VOLUME AVG
        # -----------------------------------

        vol_avg_series = volume_series.rolling(
            10
        ).mean()

        # -----------------------------------
        # VALUES
        # -----------------------------------

        previous_close = float(
            close_series.iloc[-2]
        )

        rsi = float(
            rsi_series.iloc[-1]
        )

        ma20 = float(
            ma20_series.iloc[-1]
        )

        ma50 = float(
            ma50_series.iloc[-1]
        )

        volume = float(
            volume_series.iloc[-1]
        )

        vol_avg = float(
            vol_avg_series.iloc[-1]
        )

        recent_high = float(
            high_series.tail(20).max()
        )

        # -----------------------------------
        # HANDLE NaN
        # -----------------------------------

        if pd.isna(rsi):

            rsi = 0

        if pd.isna(ma20):

            ma20 = 0

        if pd.isna(ma50):

            ma50 = 0

        if pd.isna(volume):

            volume = 0

        if pd.isna(vol_avg):

            vol_avg = 0

        # -----------------------------------
        # AI ENGINE
        # -----------------------------------

        score = 0

        reasons = []

        volume_ratio = 0

        # RSI

        if rsi >= 70:

            score += 30

            reasons.append(
                "Strong RSI"
            )

        elif rsi >= 60:

            score += 20

            reasons.append(
                "Positive RSI"
            )

        # VOLUME

        if vol_avg > 0:

            volume_ratio = (
                volume / vol_avg
            )

            if volume_ratio >= 3:

                score += 30

                reasons.append(
                    "Huge Volume"
                )

            elif volume_ratio >= 2:

                score += 20

                reasons.append(
                    "Volume Spike"
                )

        # TREND

        if close > ma20:

            score += 15

            reasons.append(
                "Above MA20"
            )

        if ma20 > ma50:

            score += 20

            reasons.append(
                "Bullish Trend"
            )

        # BREAKOUT

        breakout_percent = (
            close / recent_high
        ) * 100

        if breakout_percent >= 99:

            score += 25

            reasons.append(
                "Near Breakout"
            )

        # WEEKLY MOVE

        old_close = float(
            close_series.iloc[-6]
        )

        five_day_return = (
            (
                close - old_close
            ) / old_close
        ) * 100

        if five_day_return >= 10:

            score += 30

            reasons.append(
                "Strong Weekly Momentum"
            )

        elif five_day_return >= 5:

            score += 20

            reasons.append(
                "Weekly Momentum"
            )

        # DAILY MOVE

        daily_move = (
            (
                close - previous_close
            ) / previous_close
        ) * 100

        if daily_move >= 4:

            score += 20

            reasons.append(
                "Strong Daily Move"
            )

        # -----------------------------------
        # PREDICTION
        # -----------------------------------

        prediction = min(
            score,
            95
        )

        # -----------------------------------
        # BUY LEVELS
        # -----------------------------------

        buy_above = round(
            recent_high * 1.01,
            2
        )

        stoploss = round(
            ma20 * 0.97,
            2
        )

        target1 = round(
            close * 1.05,
            2
        )

        target2 = round(
            close * 1.10,
            2
        )

        # -----------------------------------
        # SIGNAL
        # -----------------------------------

        signal = "Neutral"

        if score >= 90:

            signal = "🚀 SUPER BULLISH"

        elif score >= 70:

            signal = "🔥 HIGH MOMENTUM"

        elif score >= 50:

            signal = "👍 WATCHLIST"

        # -----------------------------------
        # RETURN
        # -----------------------------------

        return {

            "Stock": stock.replace(
                ".NS",
                ""
            ),

            "Price": round(
                close,
                2
            ),

            "Prediction %": prediction,

            "AI Score": score,

            "Signal": signal,

            "RSI": round(
                rsi,
                2
            ),

            "Volume Ratio": round(
                volume_ratio,
                2
            ),

            "Buy Above": buy_above,

            "Stoploss": stoploss,

            "Target 1": target1,

            "Target 2": target2,

            "Reasons": ", ".join(
                reasons
            )

        }

    except:

        return None

# -----------------------------------
# RUN SCANNER
# -----------------------------------

st.subheader(
    "⚡ Scanning..."
)

with st.spinner(
    "Analyzing stocks..."
):

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        output = list(
            executor.map(
                analyze_stock,
                stocks
            )
        )

results = [
    x for x in output
    if x is not None
]

# -----------------------------------
# RESULTS
# -----------------------------------

if len(results) > 0:

    result_df = pd.DataFrame(
        results
    )

    # SORT

    result_df = result_df.sort_values(
        by="Prediction %",
        ascending=False
    )

    # FILTER

    top_df = result_df[
        result_df["AI Score"]
        >= min_score
    ].copy()

    # -----------------------------------
    # WATCHLIST COLUMN
    # -----------------------------------

    top_df["⭐ Watch"] = top_df[
        "Stock"
    ].isin(watchlist)

    # COLUMN ORDER

    cols = [

        "⭐ Watch",

        "Stock",

        "Price",

        "Prediction %",

        "AI Score",

        "Signal",

        "RSI",

        "Volume Ratio",

        "Buy Above",

        "Stoploss",

        "Target 1",

        "Target 2",

        "Reasons"

    ]

    top_df = top_df[cols]

    # -----------------------------------
    # EDITABLE TABLE
    # -----------------------------------

    st.subheader(
        "🚀 Top Recommended Stocks"
    )

    edited_df = st.data_editor(

        top_df,

        use_container_width=True,

        hide_index=True,

        key="watchlist_editor"

    )

    # -----------------------------------
    # SAVE WATCHLIST
    # -----------------------------------

    watchlist = edited_df[
        edited_df["⭐ Watch"] == True
    ]["Stock"].tolist()

    watchlist_save_df = pd.DataFrame({

        "Stock": watchlist

    })

    watchlist_save_df.to_csv(

        WATCHLIST_FILE,

        index=False

    )

    # -----------------------------------
    # WATCHLIST TABLE
    # -----------------------------------

    st.subheader(
        "⭐ My Watchlist"
    )

    watchlist_stocks = result_df[
        result_df["Stock"].isin(
            watchlist
        )
    ]

    st.dataframe(

        watchlist_stocks,

        use_container_width=True

    )

    # -----------------------------------
    # FULL ANALYSIS
    # -----------------------------------

    st.subheader(
        "📊 Full Market Analysis"
    )

    st.dataframe(

        result_df,

        use_container_width=True

    )

    # -----------------------------------
    # STOCK CHART
    # -----------------------------------

    selected_stock = st.selectbox(

        "📈 Select Stock Chart",

        result_df["Stock"]

    )

    chart_stock = (
        selected_stock + ".NS"
    )

    chart_df = yf.download(

        chart_stock,

        period="1mo",

        interval="1d",

        progress=False,

        auto_adjust=True

    )

    if not chart_df.empty:

        chart_close = pd.Series(

            chart_df["Close"]
            .to_numpy()
            .flatten()

        )

        st.subheader(
            f"📈 {selected_stock} Chart"
        )

        st.line_chart(
            chart_close
        )

else:

    st.warning(
        "No stock data found."
    )