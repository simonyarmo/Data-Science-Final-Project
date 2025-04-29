#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from data.reddit_scraper import RedditScraper


def main():
    test_subreddits = ["stocks", "investing"]
    limit = 5

    os.makedirs("outputs", exist_ok=True)
    out_csv = "tests/outputs/test_reddit.csv"

    scraper = RedditScraper()
    df = scraper.run(
        subreddits=test_subreddits,
        limit=limit,
        time_filter="day",
        output_path=out_csv
    )

    assert not df.empty, "[WARNING] No Reddit posts scraped!"
    assert os.path.exists(out_csv), "[WARNING] Output CSV was not written"
    assert "ticker_symbols" in df.columns, "[WARNING] Missing ticker_symbols column"

    print(f"[CORRECT] Scraped {len(df)} posts from Reddit")
    print("\n–– sample rows ––")
    print(df[["subreddit", "title", "ticker_symbols"]].head().to_string(index=False))


if __name__ == "__main__":
    main()
