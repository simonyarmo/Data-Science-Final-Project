#!/usr/bin/env python3
import argparse
import pandas as pd
from analysis.sentiment_analyzer import SentimentAnalyzer

def parse_args():
    p = argparse.ArgumentParser(
        description="Load a CSV of texts, run FinBERT-based sentiment, and dump the augmented DataFrame."
    )
    p.add_argument(
        "infile",
        help="Path to your input CSV (must contain a column of raw text)."
    )
    p.add_argument(
        "--text-col",
        default="body",
        help="Name of the column in which your text lives (default: %(default)s)."
    )
    p.add_argument(
        "--outfile",
        default="sentiment_output.csv",
        help="Where to write out the CSV with sentiment columns added."
    )
    return p.parse_args()

def main():
    args = parse_args()

    # 1) load your CSV
    df = pd.read_csv(args.infile)

    # 2) instantiate the analyzer once
    analyzer = SentimentAnalyzer()

    # 3) run sentiment on the specified text column
    #    this will append sentiment_score, bullish_probability, etc.
    sentiment_df = analyzer.analyze_social_media_data(df, text_column=args.text_col)

    # 4) save it out
    sentiment_df.to_csv(args.outfile, index=False)
    print(f"✅ Wrote {len(sentiment_df)} rows with new sentiment columns to {args.outfile}")

if __name__ == "__main__":
    main()
