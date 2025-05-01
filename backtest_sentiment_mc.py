#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

def fit_models(df):
    """
    Fit AR(1) on sentiment and linear return-on-lagged-sentiment.
    Returns φ, eps_s (sentiment residuals), α, β, eps_r (return residuals).
    """
    # build a tidy DataFrame with unique column names
    dfc = pd.DataFrame({
        'sent': df['sentiment_score_mean'],
        'lag':  df['sentiment_score_mean'].shift(1),
        'ret':  df['Close'].pct_change(),
    }).dropna()

    # AR(1) on sentiment
    Xs = dfc[['lag']].values
    Ys = dfc['sent'].values
    ar = LinearRegression().fit(Xs, Ys)
    phi   = ar.coef_[0]
    eps_s = Ys - ar.predict(Xs)

    # return regression on lagged sentiment
    lr = LinearRegression().fit(Xs, dfc['ret'].values)
    alpha = lr.intercept_
    beta  = lr.coef_[0]
    eps_r = dfc['ret'].values - lr.predict(Xs)

    return phi, eps_s, alpha, beta, eps_r

def simulate_median_return(S0, P0, phi, eps_s, alpha, beta, eps_r, sims, seed):
    """
    Monte Carlo simulate 1-day ahead. Returns the median simulated return.
    """
    rng = np.random.default_rng(seed)
    ds = rng.choice(eps_s, size=sims, replace=True)
    dr = rng.choice(eps_r, size=sims, replace=True)

    # simulate next-day return = α + β·S0 + noise
    R1 = alpha + beta * S0 + dr
    P1 = P0 * (1 + R1)

    # median return
    med_price = np.percentile(P1, 50)
    return (med_price - P0) / P0

def backtest(df, sims=1000, seed=42):
    """
    Walk-forward backtest: at each t, fit on [0..t), simulate next-day,
    go long if median>price else short, realize next-day actual return.
    """
    df = df.sort_values('Date').reset_index(drop=True)
    prices = df['Close'].values
    sents  = df['sentiment_score_mean'].values

    records = []
    for i in range(2, len(df)-1):
        train = df.iloc[:i]
        phi, eps_s, alpha, beta, eps_r = fit_models(train)

        P0 = prices[i]
        S0 = sents[i]
        pred_ret  = simulate_median_return(S0, P0, phi, eps_s, alpha, beta, eps_r, sims, seed)
        actual_ret = (prices[i+1] - P0) / P0
        strat_ret  = actual_ret if pred_ret > 0 else -actual_ret

        records.append({
            'Date':          df.loc[i,'Date'],
            'predicted_ret': pred_ret,
            'actual_ret':    actual_ret,
            'strategy_ret':  strat_ret
        })

    out = pd.DataFrame(records)
    out['cum_strategy'] = (1 + out['strategy_ret']).cumprod() - 1
    out['cum_bh']       = (1 + out['actual_ret']).cumprod() - 1
    return out

def main():
    p = argparse.ArgumentParser(
        description="Backtest sentiment-driven Monte Carlo strategy"
    )
    p.add_argument('--data_csv', required=True,
                   help="Merged CSV with columns Date,Close,sentiment_score_mean")
    p.add_argument('--sims',    type=int, default=1000,
                   help="Monte Carlo paths per date")
    p.add_argument('--seed',    type=int, default=42,
                   help="Random seed")
    args = p.parse_args()

    df = pd.read_csv(args.data_csv, parse_dates=['Date'])
    results = backtest(df, sims=args.sims, seed=args.seed)

    # final summary
    final = results.iloc[-1]
    print(f"Strategy final return:   {final.cum_strategy:.2%}")
    print(f"Buy-and-hold return:      {final.cum_bh:.2%}")

    # save and plot
    results.to_csv("backtest_results.csv", index=False)
    plt.figure(figsize=(10,6))
    plt.plot(results['Date'], results['cum_strategy'], label='MC Strategy')
    plt.plot(results['Date'], results['cum_bh'],       label='Buy & Hold')
    plt.legend()
    plt.title("Cumulative Returns")
    plt.xlabel("Date")
    plt.ylabel("Return")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("backtest_equity.png")
    print("→ backtest_results.csv and backtest_equity.png written")

if __name__=="__main__":
    main()
