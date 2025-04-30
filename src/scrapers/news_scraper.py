import sys
import os
import argparse

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import logging
from typing import List, Dict, Optional
import config

class NewsCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1/company-news"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Define target tickers
        self.target_tickers = ['TSLA', 'NVDA', 'BA']
        
        # Define time period - Nov 2024 to Apr 2025
        self.end_date = datetime(2025, 4, 30)
        self.start_date = datetime(2024, 11, 1)
        
        # Setup data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
        os.makedirs(self.data_dir, exist_ok=True)

    def _make_request(self, ticker: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Make a request to Finnhub API with proper error handling"""
        try:
            params = {
                'symbol': ticker,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'token': self.api_key
            }
            
            # Log the exact request being made
            self.logger.info(f"Making request for {ticker} with params: {params}")
            self.logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                verify=True
            )
            
            # Log the response status and headers
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response headers: {response.headers}")
            self.logger.info(f"Response content: {response.text[:500]}")  # Log first 500 chars of response
            
            response.raise_for_status()
            
            # Check if response is empty
            if len(response.content) <= 2:  # Empty response is usually '[]' or '{}'
                self.logger.warning(f"Empty response received for {ticker}")
                return None
                
            data = response.json()
            
            # Validate API key
            if isinstance(data, dict) and 'error' in data:
                self.logger.error(f"API Error for {ticker}: {data['error']}")
                return None
                
            return data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request for {ticker}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response text: {e.response.text}")
                self.logger.error(f"Response headers: {e.response.headers}")
            return None

    def _process_article(self, article: Dict, ticker: str) -> Dict:
        """Process a single article into our standard format"""
        try:
            # Convert Unix timestamp to datetime
            if 'datetime' in article and article['datetime']:
                pub_date = datetime.fromtimestamp(article['datetime']).strftime('%Y-%m-%d %H:%M:%S')
            else:
                self.logger.warning(f"Missing datetime for article: {article.get('headline', 'Unknown headline')}")
                pub_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'as_of_date': pub_date,
                'ticker': ticker,
                'headline': article.get('headline', ''),
                'news_text': article.get('summary', ''),
                'source': article.get('source', 'Finnhub'),
                'url': article.get('url', '')
            }
        except Exception as e:
            self.logger.error(f"Error processing article: {str(e)}")
            self.logger.error(f"Article data: {article}")
            return None

    def collect_news(self) -> pd.DataFrame:
        """
        Collect news for all target tickers and combine into a single DataFrame
        """
        all_news = []
        
        for ticker in self.target_tickers:
            self.logger.info(f"Collecting news for {ticker}")
            
            # Split the date range into 30-day chunks
            current_start = self.start_date
            while current_start < self.end_date:
                current_end = min(current_start + timedelta(days=30), self.end_date)
                
                # Make request for this chunk
                response = self._make_request(ticker, current_start, current_end)
                if not response:
                    current_start = current_end
                    continue
                
                # Process articles
                for article in response:
                    processed_article = self._process_article(article, ticker)
                    if processed_article:
                        all_news.append(processed_article)
                
                # Log the date range of articles received
                if response:
                    try:
                        dates = [datetime.fromtimestamp(article['datetime']) for article in response if 'datetime' in article and article['datetime']]
                        if dates:
                            min_date = min(dates)
                            max_date = max(dates)
                            self.logger.info(f"Received articles from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
                    except Exception as e:
                        self.logger.error(f"Error processing dates: {str(e)}")
                
                # Move to next chunk
                current_start = current_end
                
                # Respect rate limits (60 calls per minute)
                time.sleep(1)
            
            self.logger.info(f"Collected {len([n for n in all_news if n['ticker'] == ticker])} articles for {ticker}")
        
        if all_news:
            df = pd.DataFrame(all_news)
            
            # Ensure consistent column order
            columns = ['as_of_date', 'ticker', 'headline', 'news_text', 'source', 'url']
            df = df[columns]
            
            # Sort by date (most recent first)
            df = df.sort_values('as_of_date', ascending=False)
            
            # Remove duplicates based on headline
            df = df.drop_duplicates(subset=['headline'], keep='first')
            
            # Log the final date range
            if not df.empty:
                try:
                    min_date = pd.to_datetime(df['as_of_date']).min()
                    max_date = pd.to_datetime(df['as_of_date']).max()
                    self.logger.info(f"Final date range of collected articles: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
                except Exception as e:
                    self.logger.error(f"Error calculating final date range: {str(e)}")
            
            return df
        
        return pd.DataFrame(columns=['as_of_date', 'ticker', 'headline', 'news_text', 'source', 'url'])

    def save_news(self, df: pd.DataFrame, custom_filename: str = None) -> str:
        """
        Save the news DataFrame to CSV and JSON
        
        Args:
            df: DataFrame containing news articles
            custom_filename: Optional custom filename (without extension)
        """
        if df.empty:
            self.logger.warning("No news to save")
            return ""
            
        if custom_filename:
            # Remove .csv extension if present
            base_filename = custom_filename.replace('.csv', '')
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f'finnhub_news_{timestamp}'
        
        # Save CSV
        csv_file = os.path.join(self.data_dir, f'{base_filename}.csv')
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Save JSON with additional metadata
        json_data = {
            'metadata': {
                'collection_time': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'total_articles': len(df),
                'tickers_covered': list(df['ticker'].unique()),
                'date_range': {
                    'start': self.start_date.strftime('%Y-%m-%d'),
                    'end': self.end_date.strftime('%Y-%m-%d')
                }
            },
            'news_data': df.to_dict(orient='records')
        }
        
        json_file = os.path.join(self.data_dir, f'{base_filename}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        
        self.logger.info(f"Saved {len(df)} news items to {csv_file} and {json_file}")
        return csv_file

def main():
    """
    Main function to run the news collector
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Collect financial news using Finnhub API')
    parser.add_argument('--ticker', type=str, help='Single ticker symbol to collect news for')
    parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str, help='End date in YYYY-MM-DD format')
    parser.add_argument('--all', action='store_true', help='Collect news for all target tickers')
    parser.add_argument('--output', type=str, help='Custom output filename (without extension)')
    
    args = parser.parse_args()
    
    # Get API key from config
    api_key = config.FINNHUB_API_KEY
    if not api_key:
        print("Error: FINNHUB_API_KEY not found in config")
        return
    
    # Create collector instance
    collector = NewsCollector(api_key)
    
    # Override dates if provided
    if args.start_date:
        try:
            collector.start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid start date format. Use YYYY-MM-DD")
            return
            
    if args.end_date:
        try:
            collector.end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid end date format. Use YYYY-MM-DD")
            return
    
    # Override tickers if provided
    if args.ticker:
        collector.target_tickers = [args.ticker.upper()]
    elif not args.all:
        print("Error: Either specify a ticker with --ticker or use --all for all tickers")
        return
    
    print("Starting news collection...")
    print(f"Time period: {collector.start_date.strftime('%Y-%m-%d')} to {collector.end_date.strftime('%Y-%m-%d')}")
    print(f"Target tickers: {', '.join(collector.target_tickers)}")
    
    news_df = collector.collect_news()
    
    if not news_df.empty:
        saved_file = collector.save_news(news_df, args.output)
        
        print(f"\nCollected {len(news_df)} news articles")
        print("\nNews distribution by ticker:")
        print(news_df['ticker'].value_counts())
        
        print("\nDate range coverage:")
        for ticker in news_df['ticker'].unique():
            ticker_df = news_df[news_df['ticker'] == ticker]
            min_date = pd.to_datetime(ticker_df['as_of_date']).min()
            max_date = pd.to_datetime(ticker_df['as_of_date']).max()
            print(f"{ticker}: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        
        print("\nMost recent news items:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(news_df[['as_of_date', 'ticker', 'headline']].head())
    else:
        print("No news articles were collected. Check the logs for errors.")

if __name__ == "__main__":
    main()
