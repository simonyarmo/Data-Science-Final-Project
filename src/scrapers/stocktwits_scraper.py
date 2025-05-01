#!/usr/bin/env python3
import requests
import pandas as pd
import os
import re
from datetime import datetime
import sys

# allow import from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STOCKTWITS_SYMBOLS, STOCKTWITS_DATA_PATH, logger


class StockTwitsScraper:
    """Scraper for collecting messages from StockTwits public streams."""

    BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"

    def __init__(self):
        logger.info("StockTwits scraper initialized")

    def scrape_messages(self, symbols=None, limit=50):
        """
        Pull the latest messages for each symbol.

        Args:
            symbols (list[str]): list of ticker symbols (e.g. ["AAPL","MSFT"])
            limit (int): max messages per symbol

        Returns:
            pd.DataFrame: id, symbol, body, created_at, user, ticker_symbols
        """
        symbols = symbols or STOCKTWITS_SYMBOLS
        all_msgs = []

        for sym in symbols:
            url = self.BASE_URL.format(symbol=sym)
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json().get("messages", [])[:limit]
            except Exception as e:
                logger.error(f"Error fetching {sym}: {e}")
                continue

            for m in data:
                # parse timestamp
                dt = m.get("created_at")
                try:
                    created = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                except:
                    created = None

                # extract any tickers StockTwits recognized
                stix = m.get("symbols", []) or m.get("entities", {}).get("symbols", [])
                tickers = [s.get("symbol") for s in stix if s.get("symbol")]

                all_msgs.append({
                    "id": m.get("id"),
                    "symbol": sym,
                    "body": m.get("body", ""),
                    "created_at": created,
                    "user": m.get("user", {}).get("username", ""),
                    "watchlist_count": m.get("user", {}).get("watchlist_count", None),
                    "ticker_symbols": tickers
                })

        df = pd.DataFrame(all_msgs)
        if not df.empty:
            df.drop_duplicates(subset="id", inplace=True)
            logger.info(f"Scraped {len(df)} messages from StockTwits")
        else:
            logger.warning("No StockTwits messages scraped")
        return df

    def save_data(self, df, output_path=None):
        """
        Save the scraped DataFrame to CSV.
        """
        path = output_path or STOCKTWITS_DATA_PATH
        if df.empty:
            logger.warning("Nothing to save to StockTwits CSV")
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"StockTwits data saved to {path}")
        return path

    def run(self, symbols=None, limit=50, output_path=None):
        """
        Full scrape → save pipeline.
        """
        df = self.scrape_messages(symbols=symbols, limit=limit)
        self.save_data(df, output_path=output_path)
        return df


if __name__ == "__main__":
    scraper = StockTwitsScraper()
    df = scraper.run(limit=30)
    print(f"Scraped {len(df)} StockTwits messages")
    print(df.head().to_string(index=False))
