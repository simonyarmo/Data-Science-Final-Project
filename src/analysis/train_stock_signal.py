"""
This file represents our initial framework for training stock signal models.
It served as a starting point for our sentiment analysis approach.
However, the final models and analysis were ultimately implemented and refined
in the individual Jupyter notebooks (Tesla_Analysis.ipynb, Nvidia_Analysis.ipynb,
and Boeing.ipynb) to allow for more interactive development and visualization
of results.

This file is kept for historical reference but is not used in the final analysis.
"""

#!/usr/bin/env python3
import pandas as pd
import numpy as np
import argparse
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def preprocess(sentiment_csv: str, financial_csv: str) -> pd.DataFrame:
    # --- load & aggregate sentiment by day ---
    df_s = pd.read_csv(sentiment_csv, parse_dates=['as_of_date'], infer_datetime_format=True)
    # floor to date only
    df_s['date'] = df_s['as_of_date'].dt.floor('d')
    # daily means
    daily = df_s.groupby('date').agg({
        'sentiment_score':'mean',
        'bullish_probability':'mean',
        'bearish_probability':'mean',
        'neutral_probability':'mean'
    }).rename(columns={
        'sentiment_score':'sentiment_score_mean',
        'bullish_probability':'bullish_mean',
        'bearish_probability':'bearish_mean',
        'neutral_probability':'neutral_mean'
    })
    # add a count column
    daily['sentiment_count'] = df_s.groupby('date').size()

    # --- load & clean financial data ---
    df_f = pd.read_csv(financial_csv, parse_dates=['Date'], infer_datetime_format=True)
    # strip dollar signs & commas from money columns
    for c in ['Close/Last','Close','Open','High','Low','Volume']:
        if c in df_f.columns:
            df_f[c] = (df_f[c]
                .astype(str)
                .str.replace(r'[\$,]', '', regex=True)
                .astype(float))
    # unify column name
    if 'Close/Last' in df_f.columns and 'Close' not in df_f.columns:
        df_f = df_f.rename(columns={'Close/Last':'Close'})

    # --- merge on dates present in both sets ---
    df = pd.merge(df_f, daily,
                  left_on='Date', right_on='date',
                  how='inner')
    df = df.sort_values('Date').reset_index(drop=True)
    df.to_csv("merged_ba_daily.csv", index=False)
    print("Wrote merged_ba_daily.csv with columns:", list(df.columns))
    return df

def make_labels(df: pd.DataFrame, threshold: float = 0.001) -> pd.DataFrame:
    df = df.copy()
    # next‐day return
    df['future_close'] = df['Close'].shift(-1)
    df['return'] = (df['future_close'] - df['Close']) / df['Close']
    # assign labels
    def label(r):
        if r > threshold:   return 'buy'
        if r < -threshold:  return 'sell'
        return 'hold'
    df['signal'] = df['return'].apply(label)
    # drop last row (no future_close)
    return df.dropna(subset=['future_close']).reset_index(drop=True)

def train_and_evaluate(df: pd.DataFrame):
    features = [
        'Open','High','Low','Close','Volume',
        'sentiment_score_mean',
        'bullish_mean','bearish_mean','neutral_mean',
        'sentiment_count'
    ]
    X = df[features]
    y = df['signal']

    # time‐based split: first 80% train, last 20% test
    split = int(len(df)*0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n=== Classification Report ===")
    print(classification_report(y_test, y_pred))
    return model, features

def predict_next_day(model, features, last_row: pd.Series):
    X = last_row[features].values.reshape(1, -1)
    return model.predict(X)[0]

def main():
    p = argparse.ArgumentParser(
        description="Train & evaluate next-day stock signal model"
    )
    p.add_argument('--sentiment_csv', required=True,
                   help="CSV of headlines+FinBERT scores (with as_of_date)")
    p.add_argument('--financial_csv', required=True,
                   help="Daily stock CSV (Date, Close/Last, Volume, Open, High, Low)")
    args = p.parse_args()

    print("Loading & merging data…")
    df = preprocess(args.sentiment_csv, args.financial_csv)

    print("Creating buy/sell/hold labels…")
    df = make_labels(df, threshold=0.001)

    print("Training & evaluating model…")
    model, features = train_and_evaluate(df)

    # demo prediction
    last = df.iloc[[-1]]
    sig = predict_next_day(model, features, last.squeeze())
    day = last['Date'].dt.date.iloc[0]
    print(f"\n→ Predicted signal for next trading day after {day}: {sig!r}")

if __name__ == "__main__":
    main()
