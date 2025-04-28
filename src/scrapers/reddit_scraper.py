import praw
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    SUBREDDITS, REDDIT_DATA_PATH, logger
)

class RedditScraper:
    """Scraper for collecting financial discussions from Reddit"""
    
    def __init__(self):
        """Initialize the Reddit scraper with API credentials"""
        if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
            logger.error("Reddit API credentials not found in environment variables")
            raise ValueError("Reddit API credentials are required")
            
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        logger.info("Reddit scraper initialized")
        
    def scrape_posts(self, subreddits=None, limit=100, time_filter='day'):
        """
        Scrape posts from specified subreddits
        
        Args:
            subreddits (list): List of subreddit names to scrape
            limit (int): Maximum number of posts to scrape per subreddit
            time_filter (str): One of 'hour', 'day', 'week', 'month', 'year', 'all'
            
        Returns:
            pandas.DataFrame: DataFrame containing the scraped posts
        """
        if subreddits is None:
            subreddits = SUBREDDITS
            
        logger.info(f"Scraping {len(subreddits)} subreddits: {', '.join(subreddits)}")
        
        all_posts = []
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get top posts
                for post in subreddit.top(time_filter=time_filter, limit=limit):
                    post_data = {
                        'id': post.id,
                        'subreddit': subreddit_name,
                        'title': post.title,
                        'selftext': post.selftext,
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'created_utc': datetime.fromtimestamp(post.created_utc),
                        'url': post.url,
                        'permalink': f"https://www.reddit.com{post.permalink}"
                    }
                    all_posts.append(post_data)
                
                # Get hot posts
                for post in subreddit.hot(limit=limit):
                    post_data = {
                        'id': post.id,
                        'subreddit': subreddit_name,
                        'title': post.title,
                        'selftext': post.selftext,
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'created_utc': datetime.fromtimestamp(post.created_utc),
                        'url': post.url,
                        'permalink': f"https://www.reddit.com{post.permalink}"
                    }
                    all_posts.append(post_data)
                
                logger.info(f"Scraped subreddit: {subreddit_name}")
                
            except Exception as e:
                logger.error(f"Error scraping subreddit {subreddit_name}: {str(e)}")
                
        # Create DataFrame and remove duplicates
        df = pd.DataFrame(all_posts)
        if not df.empty:
            df.drop_duplicates(subset='id', inplace=True)
            logger.info(f"Scraped {len(df)} unique Reddit posts")
        else:
            logger.warning("No posts were scraped from Reddit")
            
        return df
    
    def extract_ticker_symbols(self, df):
        """
        Extract potential stock ticker symbols from post titles and content
        
        Args:
            df (pandas.DataFrame): DataFrame containing post data
            
        Returns:
            pandas.DataFrame: DataFrame with added ticker_symbols column
        """
        if df.empty:
            return df
            
        # Common pattern for tickers is $ followed by uppercase letters
        # This is a simple approach and might need refinement
        def extract_tickers(text):
            import re
            if not isinstance(text, str):
                return []
            
            # Find all instances of $ followed by 1-5 uppercase letters
            tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
            
            # Also look for common stock mentions without $ (e.g., "AAPL is...")
            standalone_tickers = re.findall(r'\b([A-Z]{2,5})\b', text)
            
            # Combine and remove duplicates
            all_tickers = list(set(tickers + standalone_tickers))
            
            return all_tickers
        
        # Extract tickers from title and content
        df['ticker_symbols'] = df.apply(
            lambda row: extract_tickers(str(row['title']) + " " + str(row['selftext'])), 
            axis=1
        )
        
        return df
    
    def save_data(self, df, output_path=None):
        """
        Save the scraped data to a CSV file
        
        Args:
            df (pandas.DataFrame): DataFrame containing the scraped posts
            output_path (str): Path where the CSV file will be saved
            
        Returns:
            str: Path where the data was saved
        """
        if output_path is None:
            output_path = REDDIT_DATA_PATH
            
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
    
    def run(self, subreddits=None, limit=100, time_filter='day', output_path=None):
        """
        Run the complete scraping process
        
        Args:
            subreddits (list): List of subreddit names to scrape
            limit (int): Maximum number of posts to scrape per subreddit
            time_filter (str): One of 'hour', 'day', 'week', 'month', 'year', 'all'
            output_path (str): Path where the CSV file will be saved
            
        Returns:
            pandas.DataFrame: DataFrame containing the scraped and processed posts
        """
        # Scrape posts
        df = self.scrape_posts(subreddits, limit, time_filter)
        
        # Extract ticker symbols
        df = self.extract_ticker_symbols(df)
        
        # Save data
        self.save_data(df, output_path)
        
        return df

if __name__ == "__main__":
    # When run directly, scrape all configured subreddits
    scraper = RedditScraper()
    result_df = scraper.run()
    print(f"Scraped {len(result_df)} posts from Reddit") 