#!/usr/bin/env python3
import os
import pprint
from data.reddit_scraper import RedditScraper


def main():
    # 1) basic config
    test_subreddits = ["stocks", "investing"]
    limit = 5  # keep it small for testing
    out_csv = "test_reddit.csv"

    # 2) invoke the scraper
    scraper = RedditScraper()
    df = scraper.run(
        subreddits=test_subreddits,
        limit=limit,
        time_filter="day",
        output_path=out_csv
    )

    # 3) basic checks
    assert not df.empty, "[WARNING] No Reddit posts scraped!"
    assert os.path.exists(out_csv), "[WARNING] Output CSV was not written"
    assert "ticker_symbols" in df.columns, "[WARNING] Missing ticker_symbols column"

    # 4) inspect sample
    print(f"[CORRECT] Scraped {len(df)} posts from Reddit")
    print("\n–– sample rows ––")
    print(df[["subreddit", "title", "ticker_symbols"]].head().to_string(index=False))


if __name__ == "__main__":
    main()
