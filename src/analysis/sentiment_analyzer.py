from openai import OpenAI
import pandas as pd
import numpy as np
import sys
import os
import json
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    OPENAI_KEY, SENTIMENT_DATA_PATH, RECOMMENDATIONS_PATH,
    OPENAI_MODEL, MAX_TOKENS, logger
)

class SentimentAnalyzer:
    """Analyzes sentiment in financial text data using OpenAI API"""
    
    def __init__(self):
        """Initialize the sentiment analyzer with API client"""
        if not OPENAI_KEY:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key is required")
            
        self.client = OpenAI(api_key=OPENAI_KEY)
        logger.info("Sentiment analyzer initialized")
    
    def analyze_text_batch(self, texts, max_batch_size=10, delay=1):
        """
        Analyze sentiment for a batch of texts
        
        Args:
            texts (list): List of text strings to analyze
            max_batch_size (int): Maximum number of texts to analyze in one batch
            delay (int): Delay between API calls in seconds
            
        Returns:
            list: List of sentiment analysis results
        """
        if not texts:
            logger.warning("No texts provided for sentiment analysis")
            return []
            
        logger.info(f"Analyzing sentiment for {len(texts)} texts")
        
        results = []
        for i in range(0, len(texts), max_batch_size):
            batch = texts[i:i+max_batch_size]
            batch_results = []
            
            for text in batch:
                try:
                    if not isinstance(text, str) or not text.strip():
                        # Skip empty or non-string texts
                        batch_results.append({
                            'sentiment_score': 0.0,
                            'bullish_probability': 0.0,
                            'bearish_probability': 0.0,
                            'neutral_probability': 0.0,
                            'sentiment_category': 'neutral',
                            'confidence': 0.0,
                            'mentioned_tickers': [],
                            'key_points': []
                        })
                        continue
                        
                    # Truncate very long texts
                    if len(text) > 4000:
                        text = text[:4000] + "..."
                    
                    # Call OpenAI API for sentiment analysis
                    response = self.client.chat.completions.create(
                        model=OPENAI_MODEL,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": """
                            You are a financial sentiment analyzer. Analyze the following financial text and extract:
                            1. An overall sentiment score from -1.0 (extremely bearish) to 1.0 (extremely bullish)
                            2. Probabilities for bullish, bearish, and neutral sentiment (should sum to 1.0)
                            3. A sentiment category (bullish, bearish, or neutral)
                            4. Confidence level in your analysis (0.0 to 1.0)
                            5. Any stock ticker symbols mentioned in the text
                            6. Key points or claims made in the text
                            
                            Return the analysis in JSON format.
                            """},
                            {"role": "user", "content": text}
                        ],
                        max_tokens=MAX_TOKENS,
                        temperature=0.0  # Use deterministic output
                    )
                    
                    # Parse JSON response
                    result = json.loads(response.choices[0].message.content)
                    batch_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error analyzing text: {str(e)}")
                    # Add a placeholder result on error
                    batch_results.append({
                        'sentiment_score': 0.0,
                        'bullish_probability': 0.0,
                        'bearish_probability': 0.0,
                        'neutral_probability': 1.0,
                        'sentiment_category': 'neutral',
                        'confidence': 0.0,
                        'mentioned_tickers': [],
                        'key_points': ["Error in analysis"]
                    })
                    
                # Delay between API calls to avoid rate limiting
                if delay > 0:
                    time.sleep(delay)
                    
            results.extend(batch_results)
            logger.info(f"Analyzed batch of {len(batch)} texts")
            
        return results
    
    def analyze_social_media_data(self, df, text_column, batch_size=10, delay=1):
        """
        Analyze sentiment for social media posts/tweets
        
        Args:
            df (pandas.DataFrame): DataFrame containing social media data
            text_column (str): Column name that contains the text to analyze
            batch_size (int): Maximum number of texts to analyze in one batch
            delay (int): Delay between API calls in seconds
            
        Returns:
            pandas.DataFrame: Original DataFrame with added sentiment columns
        """
        if df.empty:
            logger.warning("No data provided for sentiment analysis")
            return df
            
        # Prepare texts for analysis
        texts = df[text_column].fillna('').astype(str).tolist()
        logger.info(f"Analyzing sentiment for {len(texts)} social media items")
        
        # Run sentiment analysis
        results = self.analyze_text_batch(texts, batch_size, delay)
        
        # Add results to DataFrame
        df['sentiment_score'] = [r.get('sentiment_score', 0.0) for r in results]
        df['bullish_probability'] = [r.get('bullish_probability', 0.0) for r in results]
        df['bearish_probability'] = [r.get('bearish_probability', 0.0) for r in results]
        df['neutral_probability'] = [r.get('neutral_probability', 0.0) for r in results]
        df['sentiment_category'] = [r.get('sentiment_category', 'neutral') for r in results]
        df['confidence'] = [r.get('confidence', 0.0) for r in results]
        df['mentioned_tickers'] = [r.get('mentioned_tickers', []) for r in results]
        df['key_points'] = [r.get('key_points', []) for r in results]
        
        logger.info(f"Sentiment analysis completed for {len(df)} items")
        return df
    
    def aggregate_ticker_sentiment(self, df, tickers=None):
        """
        Aggregate sentiment by ticker symbol
        
        Args:
            df (pandas.DataFrame): DataFrame with sentiment analysis results
            tickers (list): Optional list of specific tickers to include
            
        Returns:
            pandas.DataFrame: Aggregated sentiment data by ticker
        """
        if df.empty:
            return pd.DataFrame()
            
        logger.info("Aggregating sentiment by ticker")
        
        # Explode the mentioned_tickers column to get one row per ticker mention
        if 'mentioned_tickers' not in df.columns:
            logger.warning("No 'mentioned_tickers' column found in data")
            return pd.DataFrame()
            
        # Filter out rows without ticker mentions
        df_with_tickers = df[df['mentioned_tickers'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
        
        if df_with_tickers.empty:
            logger.warning("No ticker mentions found in data")
            return pd.DataFrame()
            
        # Explode ticker mentions
        exploded_df = df_with_tickers.explode('mentioned_tickers')
        
        # Filter to specific tickers if provided
        if tickers:
            exploded_df = exploded_df[exploded_df['mentioned_tickers'].isin(tickers)]
            
        # Group by ticker and calculate aggregate statistics
        ticker_sentiment = exploded_df.groupby('mentioned_tickers').agg({
            'sentiment_score': ['mean', 'count', 'std'],
            'bullish_probability': 'mean',
            'bearish_probability': 'mean',
            'neutral_probability': 'mean',
            'confidence': 'mean'
        })
        
        # Flatten multi-level columns
        ticker_sentiment.columns = ['_'.join(col).strip('_') for col in ticker_sentiment.columns.values]
        
        # Calculate sentiment standard error
        ticker_sentiment['sentiment_std_error'] = ticker_sentiment['sentiment_score_std'] / np.sqrt(ticker_sentiment['sentiment_score_count'])
        
        # Calculate confidence interval
        ticker_sentiment['sentiment_confidence_interval_low'] = ticker_sentiment['sentiment_score_mean'] - (1.96 * ticker_sentiment['sentiment_std_error'])
        ticker_sentiment['sentiment_confidence_interval_high'] = ticker_sentiment['sentiment_score_mean'] + (1.96 * ticker_sentiment['sentiment_std_error'])
        
        # Reset index to make ticker a column
        ticker_sentiment = ticker_sentiment.reset_index()
        
        logger.info(f"Aggregated sentiment for {len(ticker_sentiment)} tickers")
        return ticker_sentiment
    
    def save_data(self, df, output_path=None):
        """
        Save the sentiment analysis results to a CSV file
        
        Args:
            df (pandas.DataFrame): DataFrame with sentiment analysis results
            output_path (str): Path where the CSV file will be saved
            
        Returns:
            str: Path where the data was saved
        """
        if output_path is None:
            output_path = SENTIMENT_DATA_PATH
            
        if df.empty:
            logger.warning("No data to save")
            return None
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to CSV
            df.to_csv(output_path, index=False)
            logger.info(f"Sentiment data saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return None
    
    def generate_investment_recommendations(self, sentiment_df, financial_data_df, company_info_dict):
        """
        Generate investment recommendations based on sentiment and financial data
        
        Args:
            sentiment_df (pandas.DataFrame): Aggregated sentiment data by ticker
            financial_data_df (pandas.DataFrame): Financial market data
            company_info_dict (dict): Dictionary with company information
            
        Returns:
            dict: Investment recommendations
        """
        if sentiment_df.empty or financial_data_df.empty:
            logger.warning("Insufficient data for generating recommendations")
            return {}
            
        logger.info("Generating investment recommendations")
        
        # Prepare the prompt with market data, sentiment data, and company info
        prompt = self._prepare_recommendation_prompt(sentiment_df, financial_data_df, company_info_dict)
        
        try:
            # Call OpenAI API for generating recommendations
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": """
                    You are a financial advisor specializing in sentiment-based market analysis.
                    Your task is to analyze the provided market data and sentiment analysis,
                    and generate actionable investment recommendations.
                    
                    For each recommendation, provide:
                    1. The ticker symbol
                    2. A buy/sell/hold recommendation
                    3. A target price point or range
                    4. Suggested position size (small/medium/large)
                    5. Risk level (low/medium/high)
                    6. A short rationale for the recommendation
                    7. Key factors that influenced your decision
                    
                    Return your analysis in JSON format with an array of recommendations
                    and overall market outlook.
                    """},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS * 2,
                temperature=0.2  # Slightly creative but mostly consistent
            )
            
            # Parse JSON response
            recommendations = json.loads(response.choices[0].message.content)
            
            # Add timestamp
            recommendations['generated_at'] = datetime.now().isoformat()
            
            # Save recommendations to file
            self._save_recommendations(recommendations)
            
            logger.info(f"Generated {len(recommendations.get('recommendations', []))} investment recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {}
    
    def _prepare_recommendation_prompt(self, sentiment_df, financial_data_df, company_info_dict):
        """
        Prepare a prompt for the recommendation generation
        
        Args:
            sentiment_df (pandas.DataFrame): Aggregated sentiment data by ticker
            financial_data_df (pandas.DataFrame): Financial market data
            company_info_dict (dict): Dictionary with company information
            
        Returns:
            str: Formatted prompt for OpenAI
        """
        # Format sentiment data
        sentiment_str = "SENTIMENT DATA:\n"
        if not sentiment_df.empty:
            for _, row in sentiment_df.iterrows():
                ticker = row['mentioned_tickers']
                sentiment_str += (f"Ticker: {ticker}\n"
                                 f"  - Sentiment score: {row['sentiment_score_mean']:.2f}\n"
                                 f"  - Mention count: {row['sentiment_score_count']}\n"
                                 f"  - Bullish probability: {row['bullish_probability']:.2f}\n"
                                 f"  - Bearish probability: {row['bearish_probability']:.2f}\n"
                                 f"  - Confidence: {row['confidence']:.2f}\n\n")
        
        # Format market data for key tickers
        market_str = "MARKET DATA (Most Recent):\n"
        if not financial_data_df.empty:
            # Get the most recent data for each ticker
            recent_data = financial_data_df.sort_values('Date').groupby('Ticker').last().reset_index()
            
            for _, row in recent_data.iterrows():
                ticker = row.get('Ticker', '')
                if ticker and isinstance(ticker, str) and ticker not in ['^GSPC', '^DJI', '^IXIC', '^VIX']:
                    market_str += (f"Ticker: {ticker}\n"
                                  f"  - Close: ${row.get('Close', 0):.2f}\n"
                                  f"  - Volume: {row.get('Volume', 0)}\n"
                                  f"  - 52-week high: ${company_info_dict.get(ticker, {}).get('fiftytwo_week_high', 0):.2f}\n"
                                  f"  - 52-week low: ${company_info_dict.get(ticker, {}).get('fiftytwo_week_low', 0):.2f}\n\n")
        
        # Format index data
        index_str = "MARKET INDICES (Most Recent):\n"
        if not financial_data_df.empty:
            indices = ['^GSPC', '^DJI', '^IXIC', '^VIX']
            index_names = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                '^VIX': 'VIX'
            }
            
            for idx in indices:
                idx_data = financial_data_df[financial_data_df['Ticker'] == idx].sort_values('Date').last()
                if not idx_data.empty:
                    index_str += (f"{index_names.get(idx, idx)}:\n"
                                 f"  - Close: {idx_data.get('Close', 0):.2f}\n"
                                 f"  - Change: {idx_data.get('Close', 0) - idx_data.get('Open', 0):.2f}\n\n")
        
        # Format company information
        company_str = "COMPANY INFORMATION:\n"
        for ticker, info in company_info_dict.items():
            company_str += (f"Ticker: {ticker}\n"
                           f"  - Name: {info.get('name', '')}\n"
                           f"  - Sector: {info.get('sector', '')}\n"
                           f"  - Industry: {info.get('industry', '')}\n"
                           f"  - Market Cap: {info.get('market_cap', 0)}\n"
                           f"  - P/E Ratio: {info.get('trailing_pe', 0):.2f}\n\n")
        
        # Combine all data into one prompt
        prompt = (f"Please analyze the following financial data and provide investment recommendations.\n\n"
                 f"{sentiment_str}\n{market_str}\n{index_str}\n{company_str}\n"
                 f"Based on this data, what are your investment recommendations? Consider sentiment trends,"
                 f"correlations with market movements, and potential entry/exit points.")
        
        return prompt
    
    def _save_recommendations(self, recommendations, output_path=None):
        """
        Save recommendations to a JSON file
        
        Args:
            recommendations (dict): Investment recommendations
            output_path (str): Path where the JSON file will be saved
            
        Returns:
            str: Path where the data was saved
        """
        if output_path is None:
            output_path = RECOMMENDATIONS_PATH
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to JSON
            with open(output_path, 'w') as f:
                json.dump(recommendations, f, indent=2)
                
            logger.info(f"Recommendations saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving recommendations: {str(e)}")
            return None

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