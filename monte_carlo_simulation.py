#!/usr/bin/env python3
import pandas as pd
import numpy as np
import argparse
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

def prepare_data(df: pd.DataFrame,
                 date_col: str,
                 sentiment_col: str = 'sentiment_score_mean',
                 price_col: str = 'Close') -> pd.DataFrame:
    """
    Sorts by date, computes next-day returns and lagged sentiment.
    Returns only the rows where both return and lagged sentiment exist.
    """
    df = df.sort_values(by=date_col).reset_index(drop=True)
    # next‐day return
    df['future_close'] = df[price_col].shift(-1)
    df['return'] = (df['future_close'] - df[price_col]) / df[price_col]
    # sentiment lagged by one day
    df['sentiment_lag'] = df[sentiment_col].shift(1)
    # drop rows missing either
    return df.dropna(subset=['return', 'sentiment_lag']).reset_index(drop=True)

def fit_models(df: pd.DataFrame,
               sentiment_col: str = 'sentiment_score_mean'):
    """
    Fits:
      1) AR(1) on sentiment: sentiment_t = φ * sentiment_{t-1} + εₛ
      2) next-day RETURN on lagged sentiment: return_t = α + β * sentiment_{t-1} + εᵣ
    Returns φ, εₛ-history, α, β, εᵣ-history.
    """
    # AR(1) for sentiment levels
    Xs = df[['sentiment_lag']].values
    ys = df[sentiment_col].values
    ar = LinearRegression().fit(Xs, ys)
    phi = ar.coef_[0]
    eps_s = ys - ar.predict(Xs)

    # return on lagged sentiment
    Xr = Xs
    yr = df['return'].values
    lr = LinearRegression().fit(Xr, yr)
    alpha = lr.intercept_
    beta = lr.coef_[0]
    eps_r = yr - lr.predict(Xr)

    return phi, eps_s, alpha, beta, eps_r

def simulate_paths(
    S0: float,
    P0: float,
    phi: float,
    eps_s_hist: np.ndarray,
    alpha: float,
    beta: float,
    eps_r_hist: np.ndarray,
    horizon: int = 30,
    sims: int = 1000,
    seed: int = None
) -> np.ndarray:
    """
    Monte Carlo forward simulation:
      - simulate sentiment level via AR(1) + bootstrapped εₛ
      - simulate return via α + β·sentiment + bootstrapped εᵣ
      - compound returns to get price paths
    """
    rng = np.random.default_rng(seed)
    paths = np.zeros((sims, horizon+1), dtype=float)
    paths[:, 0] = P0
    sent = np.full(sims, S0, dtype=float)

    for t in range(1, horizon+1):
        # step sentiment
        ds = rng.choice(eps_s_hist, size=sims, replace=True)
        sent = phi * sent + ds

        # step price via return
        dr = rng.choice(eps_r_hist, size=sims, replace=True)
        ret = alpha + beta * sent + dr

        paths[:, t] = paths[:, t-1] * (1 + ret)

    return paths

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Monte Carlo simulate price paths driven by lagged sentiment"
    )
    parser.add_argument('--data_csv',  required=True,
                        help="CSV with Date (or as_of_date), Close, sentiment_score_mean")
    parser.add_argument('--horizon',   type=int,   default=30,
                        help="Days to simulate forward")
    parser.add_argument('--sims',      type=int,   default=1000,
                        help="Number of Monte Carlo paths")
    parser.add_argument('--seed',      type=int,   default=None,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    # --- load and detect date column ---
    df = pd.read_csv(args.data_csv)
    if 'as_of_date' in df.columns:
        date_col = 'as_of_date'
    elif 'Date' in df.columns:
        date_col = 'Date'
    else:
        raise RuntimeError("No 'Date' or 'as_of_date' column found")

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])

    # check required columns
    for col in ['Close', 'sentiment_score_mean']:
        if col not in df.columns:
            raise RuntimeError(f"Missing required column: {col}")

    # prepare, fit, simulate
    df2 = prepare_data(df, date_col)
    phi, eps_s_hist, alpha, beta, eps_r_hist = fit_models(df2)

    print(f"Fitted models → φ={phi:.4f}, α={alpha:.4f}, β={beta:.4f}")

    # starting values from last observed day
    last = df.sort_values(by=date_col).iloc[-1]
    P0 = float(last['Close'])
    S0 = float(last['sentiment_score_mean'])

    paths = simulate_paths(
        S0, P0,
        phi, eps_s_hist,
        alpha, beta, eps_r_hist,
        horizon=args.horizon,
        sims=args.sims,
        seed=args.seed
    )

    # compute percentiles
    days = np.arange(args.horizon+1)
    pctiles = [1, 5, 25, 50, 75, 95, 99]
    summary = {f"P{p}": np.percentile(paths, p, axis=0) for p in pctiles}
    summary_df = pd.DataFrame({'day': days, **summary})
    summary_df.to_csv("mc_price_percentiles.csv", index=False)
    print("→ mc_price_percentiles.csv written")

    # plot a few quantiles
    plt.figure(figsize=(10,6))
    for q in ['P5', 'P50', 'P95']:
        plt.plot(days, summary_df[q], label=q)
    plt.title("Monte Carlo Forecast Percentiles")
    plt.xlabel("Day")
    plt.ylabel("Price")
    plt.legend()
    plt.tight_layout()
    plt.savefig("mc_price_forecast.png")
    print("→ mc_price_forecast.png written")
