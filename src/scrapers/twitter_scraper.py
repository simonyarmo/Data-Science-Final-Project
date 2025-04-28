import tweepy
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET, TWITTER_SEARCH_QUERIES, TWITTER_DATA_PATH, logger
)

class TwitterScraper:
    """Scraper for collecting financial tweets from Twitter/X"""
    
    def __init__(self):
        """Initialize the Twitter scraper with API credentials"""
        if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
            logger.error("Twitter API credentials not found in environment variables")
            raise ValueError("Twitter API credentials are required")
        
        # Set up Twitter API client
        self.auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY, 
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN, 
            TWITTER_ACCESS_SECRET
        )
        self.api = tweepy.API(self.auth, wait_on_rate_limit=True)
        logger.info("Twitter scraper initialized")
        
    def scrape_tweets(self, queries=None, limit=100, days_back=1):
        """
        Scrape tweets based on search queries
        
        Args:
            queries (list): List of search terms to find tweets
            limit (int): Maximum number of tweets to retrieve per query
            days_back (int): How many days back to search
            
        Returns:
            pandas.DataFrame: DataFrame containing the scraped tweets
        """
        if queries is None:
            queries = TWITTER_SEARCH_QUERIES
            
        logger.info(f"Scraping tweets for {len(queries)} queries")
        
        all_tweets = []
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        for query in queries:
            try:
                tweets = self.api.search_tweets(
                    q=query,
                    count=limit,
                    tweet_mode="extended",
                    lang="en",
                    since=since_date
                )
                
                for tweet in tweets:
                    tweet_data = {
                        'id': tweet.id_str,
                        'text': tweet.full_text,
                        'created_at': tweet.created_at,
                        'user': tweet.user.screen_name,
                        'user_followers': tweet.user.followers_count,
                        'retweet_count': tweet.retweet_count,
                        'favorite_count': tweet.favorite_count,
                        'query': query
                    }
                    all_tweets.append(tweet_data)
                
                logger.info(f"Scraped query: {query} - found {len(tweets)} tweets")
                
            except Exception as e:
                logger.error(f"Error scraping tweets for query {query}: {str(e)}")
        
        # Create DataFrame and remove duplicates
        df = pd.DataFrame(all_tweets)
        if not df.empty:
            df.drop_duplicates(subset='id', inplace=True)
            logger.info(f"Scraped {len(df)} unique tweets")
        else:
            logger.warning("No tweets were scraped")
            
        return df
    
    def extract_ticker_symbols(self, df):
        """
        Extract potential stock ticker symbols from tweets
        
        Args:
            df (pandas.DataFrame): DataFrame containing tweet data
            
        Returns:
            pandas.DataFrame: DataFrame with added ticker_symbols column
        """
        if df.empty:
            return df
        
        def extract_tickers(text):
            if not isinstance(text, str):
                return []
            
            # Find all instances of $ followed by 1-5 uppercase letters
            tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
            
            # Also look for cashtags without spaces
            cashtags = re.findall(r'#([A-Z]{1,5})\b', text)
            
            # Combine and remove duplicates
            all_tickers = list(set(tickers + cashtags))
            
            return all_tickers
        
        # Extract tickers from tweet text
        df['ticker_symbols'] = df['text'].apply(extract_tickers)
        
        return df
    
    def save_data(self, df, output_path=None):
        """
        Save the scraped data to a CSV file
        
        Args:
            df (pandas.DataFrame): DataFrame containing the scraped tweets
            output_path (str): Path where the CSV file will be saved
            
        Returns:
            str: Path where the data was saved
        """
        if output_path is None:
            output_path = TWITTER_DATA_PATH
            
        if df.empty:
            logger.warning("No data to save")
            return None
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to CSV
            df.to_csv(output_path, index=False)
            logger.info(f"Data saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return None
    
    def run(self, queries=None, limit=100, days_back=1, output_path=None):
        """
        Run the complete scraping process
        
        Args:
            queries (list): List of search terms to find tweets
            limit (int): Maximum number of tweets to retrieve per query
            days_back (int): How many days back to search
            output_path (str): Path where the CSV file will be saved
            
        Returns:
            pandas.DataFrame: DataFrame containing the scraped and processed tweets
        """
        # Scrape tweets
        df = self.scrape_tweets(queries, limit, days_back)
        
        # Extract ticker symbols
        df = self.extract_ticker_symbols(df)
        
        # Save data
        self.save_data(df, output_path)
        
        return df

if __name__ == "__main__":
    # When run directly, scrape all configured queries
    scraper = TwitterScraper()
    result_df = scraper.run()
    print(f"Scraped {len(result_df)} tweets from Twitter") 