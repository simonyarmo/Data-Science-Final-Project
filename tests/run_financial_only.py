#!/usr/bin/env python3
import os
import pprint

from data.financial_data import FinancialDataCollector


def main():
    tickers = ["AAPL", "MSFT", "GOOGL"]
    start_date = "2023-01-01"
    end_date = "2023-03-31"

    os.makedirs("outputs", exist_ok=True)
    out_csv = "tests/outputs/test_financial.csv"

    collector = FinancialDataCollector()
    df, info = collector.collect_data_for_tickers(
        ticker_symbols=tickers,
        start_date=start_date,
        end_date=end_date,
        output_path=out_csv
    )

    assert not df.empty, "[WARNING] No rows fetched"
    for t in tickers:
        assert t in info, f"[WARNING] Missing info for {t}"

    assert os.path.exists(out_csv), f"[WARNING] {out_csv} not found"
    assert os.path.exists(out_csv.replace(".csv", "_info.json")), "[WARNING] JSON info missing"

    print(f"[CORRECT] Pulled {len(df)} rows across {len(info)} tickers")
    print("\n–– sample rows ––")
    print(df.head().to_string(index=False))
    print("\n–– sample info ––")
    pprint.pprint({k: info[k] for k in tickers}, width=80)


if __name__ == "__main__":
    main()
