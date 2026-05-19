import pandas as pd
import yfinance as yf

# -----------------------------------
# NSE STOCK LIST
# -----------------------------------

url = (
    "https://archives.nseindia.com/"
    "content/equities/EQUITY_L.csv"
)

print("Downloading NSE stock list...")

df = pd.read_csv(url)

# -----------------------------------
# ADD .NS
# -----------------------------------

df["Symbol"] = (
    df["SYMBOL"] + ".NS"
)

# -----------------------------------
# FILTER FUNCTION
# -----------------------------------

clean_stocks = []

for stock in df["Symbol"]:

    try:

        stock_data = yf.download(
            stock,
            period="1mo",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if stock_data.empty:
            continue

        close = float(
            stock_data["Close"]
            .to_numpy()
            .flatten()[-1]
        )

        volume = float(
            stock_data["Volume"]
            .to_numpy()
            .flatten()[-1]
        )

        # -----------------------------------
        # FILTERS
        # -----------------------------------

        # REMOVE PENNY STOCKS

        if close < 20:
            continue

        # REMOVE LOW VOLUME

        if volume < 100000:
            continue

        # KEEP GOOD STOCK

        clean_stocks.append(stock)

        print(
            f"Added: {stock}"
        )

    except:

        pass

# -----------------------------------
# SAVE CSV
# -----------------------------------

clean_df = pd.DataFrame({
    "Symbol": clean_stocks
})

clean_df.to_csv(
    "stocks.csv",
    index=False
)

print("\n✅ CLEAN STOCK CSV CREATED")

print(
    "Total Stocks:",
    len(clean_df)
)