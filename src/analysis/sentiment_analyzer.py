import os
import json
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

from config import (
    SENTIMENT_DATA_PATH, RECOMMENDATIONS_PATH,
    TWITTER_DATA_PATH, REDDIT_DATA_PATH, logger
)


class SentimentAnalyzer:
    """Analyzer for financial text sentiment using FinBERT and rule-based recommendations."""

    def __init__(self, finbert_model: str = "ProsusAI/finbert"):
        # Initialize FinBERT for sentiment
        logger.info(f"Loading FinBERT model: {finbert_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(finbert_model)
        self.model = AutoModelForSequenceClassification.from_pretrained(finbert_model)
        self.nlp = pipeline(
            "sentiment-analysis",
            model=self.model,
            tokenizer=self.tokenizer,
            return_all_scores=True
        )
        logger.info("FinBERT sentiment pipeline initialized")

    def analyze_text_batch(self, texts, batch_size: int = 16):
        """
        Analyze sentiment using FinBERT.
        Returns list of dicts with sentiment_score, bullish/bearish/neutral probabilities, category, confidence.
        """
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            preds = self.nlp(batch)
            for scores in preds:
                score_map = {entry['label'].lower(): entry['score'] for entry in scores}
                total = sum(score_map.values()) or 1
                for k in score_map:
                    score_map[k] /= total
                sentiment_score = score_map.get('positive', 0) - score_map.get('negative', 0)
                if sentiment_score > 0.05:
                    cat = 'bullish'
                elif sentiment_score < -0.05:
                    cat = 'bearish'
                else:
                    cat = 'neutral'
                results.append({
                    'sentiment_score': sentiment_score,
                    'bullish_probability': score_map.get('positive', 0),
                    'bearish_probability': score_map.get('negative', 0),
                    'neutral_probability': score_map.get('neutral', 0),
                    'sentiment_category': cat,
                    'confidence': max(score_map.values()),
                    # 'mentioned_tickers': [],
                    'key_points': []
                })
        return results

    def analyze_social_media_data(self, df: pd.DataFrame, text_column: str, batch_size: int = 16):
        """
        Run sentiment analysis on DataFrame of social media posts.
        Appends sentiment columns for downstream processing.
        """
        if df.empty:
            logger.warning("No data provided for sentiment analysis")
            return df
        texts = df[text_column].fillna('').astype(str).tolist()
        results = self.analyze_text_batch(texts, batch_size)
        # Add to DataFrame
        df['sentiment_score'] = [r['sentiment_score'] for r in results]
        df['bullish_probability'] = [r['bullish_probability'] for r in results]
        df['bearish_probability'] = [r['bearish_probability'] for r in results]
        df['neutral_probability'] = [r['neutral_probability'] for r in results]
        df['sentiment_category'] = [r['sentiment_category'] for r in results]
        df['confidence'] = [r['confidence'] for r in results]
        # df['mentioned_tickers'] = [[] for _ in results]
        df['key_points'] = [[] for _ in results]
        logger.info(f"Sentiment analysis completed for {len(df)} items")
        return df

    def aggregate_ticker_sentiment(self, df: pd.DataFrame, tickers=None) -> pd.DataFrame:
        """
        Aggregate sentiment by ticker: mean, count, std, std_error, confidence intervals.
        """
        if df.empty or 'ticker' not in df.columns:
            return pd.DataFrame()
        df_with = df[df['ticker'].apply(lambda x: bool(x) if isinstance(x, list) else False)]
        if df_with.empty:
            return pd.DataFrame()
        exploded = df_with.explode('ticker')
        if tickers:
            exploded = exploded[exploded['ticker'].isin(tickers)]
        agg = exploded.groupby('ticker').agg({
            'sentiment_score': ['mean', 'count', 'std'],
            'bullish_probability': 'mean',
            'bearish_probability': 'mean',
            'neutral_probability': 'mean',
            'confidence': 'mean'
        })
        agg.columns = ['_'.join(c) for c in agg.columns]
        agg['sentiment_std_error'] = agg['sentiment_score_std'] / np.sqrt(agg['sentiment_score_count'])
        agg['sentiment_confidence_interval_low'] = agg['sentiment_score_mean'] - 1.96 * agg['sentiment_std_error']
        agg['sentiment_confidence_interval_high'] = agg['sentiment_score_mean'] + 1.96 * agg['sentiment_std_error']
        result = agg.reset_index()
        logger.info(f"Aggregated sentiment for {len(result)} tickers")
        return result

    def save_data(self, df: pd.DataFrame, output_path: str = None):
        """Save sentiment DataFrame to CSV."""
        path = output_path or SENTIMENT_DATA_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"Sentiment data saved to {path}")
        return path

    def generate_investment_recommendations(self, sentiment_df: pd.DataFrame, financial_df: pd.DataFrame,
                                            company_info_dict: dict) -> dict:
        """
        Generate simple rule-based recommendations from FinBERT sentiment and financial data.
        """
        recommendations = {'recommendations': []}
        if sentiment_df.empty or financial_df.empty:
            logger.warning("Insufficient data for recommendations")
            return recommendations

        # Compute recent price
        recent = financial_df.sort_values('Date').groupby('Ticker').tail(1)
        for _, row in recent.iterrows():
            ticker = row['ticker']
            sentiment_row = sentiment_df[sentiment_df['ticker'] == ticker]
            score_mean = (sentiment_row['sentiment_score_mean'].iloc[0]
                          if not sentiment_row.empty else 0)
            price = row['Close']
            # Rule-based logic
            if score_mean > 0.2:
                action = 'buy'
                target = price * 1.1
                size = 'medium'
                risk = 'medium'
            elif score_mean < -0.2:
                action = 'sell'
                target = price * 0.9
                size = 'small'
                risk = 'high'
            else:
                action = 'hold'
                target = price
                size = 'small'
                risk = 'low'

            recommendations['recommendations'].append({
                'ticker': ticker,
                'action': action,
                'target_price': round(target, 2),
                'position_size': size,
                'risk_level': risk,
                'rationale': f"Sentiment score {score_mean:.2f} led to {action} recommendation."
            })

        recommendations['generated_at'] = datetime.now().isoformat()
        # save to file
        path = RECOMMENDATIONS_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(recommendations, f, indent=2)
        logger.info(f"Rule-based recommendations saved to {path}")
        return recommendations


if __name__ == "__main__":
    # Example usage
    from src.data.financial_data import FinancialDataCollector

    # Load some example data (you may need to adapt this based on your actual data)
    analyzer = SentimentAnalyzer()

    # Sample texts for testing
    sample_texts = [
        "AAPL is going to crush earnings this quarter. Their new iPhone is amazing and selling out everywhere.",
        "TSLA is overvalued and facing increasing competition. I'm bearish on the stock for Q3.",
        "MSFT cloud business continues to grow steadily. Neutral but leaning positive for the next 6 months."
    ]

    # Run sentiment analysis on sample texts
    results = analyzer.analyze_text_batch(sample_texts)
    print(json.dumps(results, indent=2))
