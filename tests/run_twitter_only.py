#!/usr/bin/env python3
import os

from scrapers.twitter_scraper import TwitterScraper, TwitterScraperV2


def main():
    test_queries = ["AAPL", "MSFT"]
    limit = 5
    os.makedirs("tests/outputs", exist_ok=True)
    out_csv = "tests/outputs/test_twitter.csv"

    scraper = TwitterScraperV2() # if v2, put the bearer token here, else put nothing
    df = scraper.run(
        queries=test_queries,
        limit=limit,
        days_back=1,
        output_path=out_csv
    )

    assert not df.empty, "[WARNING] No Twitter data scraped"
    assert os.path.exists(out_csv), "[WARNING] CSV was not written"
    assert "ticker_symbols" in df.columns, "[WARNING] ticker_symbols column missing"

    print(f"[CORRECT] Scraped {len(df)} tweets")
    print("\n–– sample rows ––")
    print(df[["text", "ticker_symbols"]].head().to_string(index=False))


if __name__ == "__main__":
    main()
