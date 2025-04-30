import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "results/finnhub_with_sentiment.csv"
TICKER = "TSLA"
DATE_COLUMN = "as_of_date"
ROLLING_WINDOW_30 = 30  # Number of posts for moving average
ROLLING_WINDOW_70 = 70  # Number of posts for moving average
ROLLING_WINDOW_100 = 100  # Number of posts for moving average


def main():
    try:
        df = pd.read_csv(CSV_PATH)
        df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
        df = df.dropna(subset=[DATE_COLUMN])
        df = df[df['ticker'] == TICKER]

        if df.empty:
            print(f"No data found for ticker '{TICKER}'.")
            return

        # Sort by timestamp
        df = df.sort_values(DATE_COLUMN)

        # Rolling average over N past rows (posts), not time
        df['rolling_sentiment_30'] = df['sentiment_score'].rolling(window=ROLLING_WINDOW_30, min_periods=1).mean()
        df['rolling_sentiment_70'] = df['sentiment_score'].rolling(window=ROLLING_WINDOW_70, min_periods=1).mean()
        df['rolling_sentiment_100'] = df['sentiment_score'].rolling(window=ROLLING_WINDOW_100, min_periods=1).mean()


        # Plot
        plt.figure(figsize=(14, 6))
        plt.plot(df[DATE_COLUMN], df['sentiment_score'], marker='.', label='Raw Sentiment', alpha=0.4)
        plt.plot(df[DATE_COLUMN], df['rolling_sentiment_30'], color='red', label=f'{ROLLING_WINDOW_30}-Post Moving Average 30')
        plt.plot(df[DATE_COLUMN], df['rolling_sentiment_70'], color='orange', label=f'{ROLLING_WINDOW_70}-Post Moving Average 70')
        plt.plot(df[DATE_COLUMN], df['rolling_sentiment_100'], color='yellow', label=f'{ROLLING_WINDOW_100}-Post Moving Average 100')

        plt.title(f"Intraday Sentiment Score and Rolling Window-Post MA for {TICKER}")
        plt.xlabel("Timestamp")
        plt.ylabel("Sentiment Score")
        plt.ylim(-1.1, 1.1)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
