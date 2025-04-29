#!/usr/bin/env python3
import argparse
import pandas as pd
import os
import json
from datetime import datetime, timedelta

# Import project modules
from scrapers.reddit_scraper import RedditScraper
from scrapers.twitter_scraper import TwitterScraper
from data.financial_data import FinancialDataCollector
from analysis.sentiment_analyzer import SentimentAnalyzer
from analysis.visualizer import DataVisualizer
from config import (
    SUBREDDITS, TWITTER_SEARCH_QUERIES, REDDIT_DATA_PATH, TWITTER_DATA_PATH,
    FINANCIAL_DATA_PATH, SENTIMENT_DATA_PATH, RECOMMENDATIONS_PATH, logger
)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Financial Sentiment Analysis Pipeline')

    # parser.add_argument('--skip-reddit', action='store_true', help='Skip Reddit scraping')
    parser.add_argument('--skip-twitter', action='store_true', help='Skip Twitter scraping')
    parser.add_argument('--skip-financial', action='store_true', help='Skip financial data collection')
    parser.add_argument('--skip-sentiment', action='store_true', help='Skip sentiment analysis')
    parser.add_argument('--skip-visualization', action='store_true', help='Skip visualization generation')

    # parser.add_argument('--reddit-limit', type=int, default=100, help='Maximum posts to scrape per subreddit')
    parser.add_argument('--twitter-limit', type=int, default=10, help='Maximum tweets to scrape per query')
    parser.add_argument('--days-back', type=int, default=7, help='Number of days to look back for social media')

    parser.add_argument('--start-date', type=str, help='Start date for financial data (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for financial data (YYYY-MM-DD)')

    # parser.add_argument('--subreddits', type=str, help='Comma-separated list of subreddits to scrape')
    parser.add_argument('--twitter-queries', type=str, help='Comma-separated list of Twitter search queries')

    parser.add_argument('--visualize-tickers', type=str, help='Comma-separated list of tickers to visualize')

    return parser.parse_args()


def scrape_social_media(args):
    """Scrape data from social media platforms"""
    # reddit_df = pd.DataFrame()
    twitter_df = pd.DataFrame()

    # Scrape Reddit if not skipped
    # if not args.skip_reddit:
    #     logger.info("Starting Reddit scraping")

    #     # Use custom subreddits if provided
    #     subreddits = SUBREDDITS
    #     if args.subreddits:
    #         subreddits = args.subreddits.split(',')

    #     reddit_scraper = RedditScraper()
    #     try:
    #         reddit_df = reddit_scraper.run(
    #             subreddits=subreddits,
    #             limit=args.reddit_limit,
    #             time_filter='week',
    #             output_path=REDDIT_DATA_PATH
    #         )
    #         logger.info(f"Scraped {len(reddit_df)} posts from Reddit")
    #     except Exception as e:
    #         logger.error(f"Error scraping Reddit: {str(e)}")
    # else:
    #     # Load existing Reddit data if available
    #     if os.path.exists(REDDIT_DATA_PATH):
    #         reddit_df = pd.read_csv(REDDIT_DATA_PATH)
    #         logger.info(f"Loaded {len(reddit_df)} existing Reddit posts")

    # Scrape Twitter if not skipped
    if not args.skip_twitter:
        logger.info("Starting Twitter scraping")

        # Use custom Twitter queries if provided
        queries = TWITTER_SEARCH_QUERIES
        if args.twitter_queries:
            queries = args.twitter_queries.split(',')

        twitter_scraper = TwitterScraper()
        try:
            twitter_df = twitter_scraper.run(
                queries=queries,
                limit=args.twitter_limit,
                days_back=args.days_back,
                output_path=TWITTER_DATA_PATH
            )
            logger.info(f"Scraped {len(twitter_df)} tweets from Twitter")
        except Exception as e:
            logger.error(f"Error scraping Twitter: {str(e)}")
    else:
        # Load existing Twitter data if available
        if os.path.exists(TWITTER_DATA_PATH):
            twitter_df = pd.read_csv(TWITTER_DATA_PATH)
            logger.info(f"Loaded {len(twitter_df)} existing tweets")

    return twitter_df


def collect_financial_data(args, ticker_symbols):
    """Collect financial data for the identified tickers"""
    financial_df = pd.DataFrame()
    stock_info = {}

    if not args.skip_financial and ticker_symbols:
        logger.info(f"Starting financial data collection for {len(ticker_symbols)} tickers")

        # Set date range
        start_date = args.start_date
        end_date = args.end_date

        # If no end date is provided, use today
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # If no start date is provided, use 1 year ago
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # Collect financial data
        collector = FinancialDataCollector()
        try:
            financial_df, stock_info = collector.collect_data_for_tickers(
                ticker_symbols=ticker_symbols,
                start_date=start_date,
                end_date=end_date,
                output_path=FINANCIAL_DATA_PATH
            )
            logger.info(f"Collected financial data: {len(financial_df)} rows for {len(stock_info)} tickers")
        except Exception as e:
            logger.error(f"Error collecting financial data: {str(e)}")
    else:
        # Load existing financial data if available
        if os.path.exists(FINANCIAL_DATA_PATH):
            financial_df = pd.read_csv(FINANCIAL_DATA_PATH)
            logger.info(f"Loaded {len(financial_df)} existing financial data points")

        # Load existing stock info if available
        info_path = FINANCIAL_DATA_PATH.replace('.csv', '_info.json')
        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                stock_info = json.load(f)
            logger.info(f"Loaded info for {len(stock_info)} tickers")

    return financial_df, stock_info


def analyze_sentiment(args, twitter_df):
    """Analyze sentiment in social media data"""
    # reddit_sentiment_df = pd.DataFrame()
    twitter_sentiment_df = pd.DataFrame()

    if not args.skip_sentiment:
        logger.info("Starting sentiment analysis")

        analyzer = SentimentAnalyzer()

        # Analyze Reddit sentiment
        # if not reddit_df.empty:
        #     try:
        #         # Combine title and text for analysis
        #         reddit_df['text_for_analysis'] = reddit_df['title'] + " " + reddit_df['selftext'].fillna('')

        #         # Run analysis
        #         reddit_sentiment_df = analyzer.analyze_social_media_data(
        #             df=reddit_df,
        #             text_column='text_for_analysis',
        #             batch_size=5  # Smaller batch size to avoid rate limits
        #         )
        #         logger.info(f"Completed sentiment analysis for {len(reddit_sentiment_df)} Reddit posts")
        #     except Exception as e:
        #         logger.error(f"Error analyzing Reddit sentiment: {str(e)}")

        # Analyze Twitter sentiment
        if not twitter_df.empty:
            try:
                # Run analysis
                twitter_sentiment_df = analyzer.analyze_social_media_data(
                    df=twitter_df,
                    text_column='text',
                    batch_size=5  # Smaller batch size to avoid rate limits
                )
                logger.info(f"Completed sentiment analysis for {len(twitter_sentiment_df)} tweets")
            except Exception as e:
                logger.error(f"Error analyzing Twitter sentiment: {str(e)}")

        # Combine and save sentiment data
        combined_sentiment = pd.concat([twitter_sentiment_df], ignore_index=True)
        if not combined_sentiment.empty:
            analyzer.save_data(combined_sentiment, SENTIMENT_DATA_PATH)
            logger.info(f"Saved combined sentiment data: {len(combined_sentiment)} items")
    else:
        # Load existing sentiment data if available
        if os.path.exists(SENTIMENT_DATA_PATH):
            combined_sentiment = pd.read_csv(SENTIMENT_DATA_PATH)
            logger.info(f"Loaded {len(combined_sentiment)} existing sentiment analysis results")
            return combined_sentiment

    return pd.concat([twitter_sentiment_df], ignore_index=True)


def extract_tickers(twitter_df):
    """Extract unique ticker symbols from social media data"""
    all_tickers = set()

    # Extract tickers from Twitter
    if not twitter_df.empty and 'ticker_symbols' in twitter_df.columns:
        for tickers in twitter_df['ticker_symbols']:
            if isinstance(tickers, list):
                all_tickers.update(tickers)
            elif isinstance(tickers, str):
                # If stored as string representation of list, convert to actual list
                try:
                    ticker_list = eval(tickers)
                    if isinstance(ticker_list, list):
                        all_tickers.update(ticker_list)
                except:
                    pass

    # Filter tickers to remove likely invalid ones
    valid_tickers = [t for t in all_tickers if t.isalpha() and len(t) <= 5 and len(t) >= 1]

    logger.info(f"Extracted {len(valid_tickers)} unique ticker symbols from social media data")
    return valid_tickers


def generate_visualizations(args, sentiment_df, financial_df, tickers):
    """Generate visualizations of sentiment and market data"""
    if args.skip_visualization:
        logger.info("Skipping visualization generation")
        return

    if sentiment_df.empty:
        logger.warning("No sentiment data available for visualization")
        return

    logger.info("Generating visualizations")

    # Initialize visualizer
    visualizer = DataVisualizer()

    # Convert ticker list values from strings to actual lists if needed
    if 'mentioned_tickers' in sentiment_df.columns and sentiment_df['mentioned_tickers'].dtype == 'object':
        sentiment_df['mentioned_tickers'] = sentiment_df['mentioned_tickers'].apply(
            lambda x: eval(x) if isinstance(x, str) else x
        )

    # Aggregate sentiment by ticker
    ticker_sentiment = SentimentAnalyzer().aggregate_ticker_sentiment(sentiment_df)

    # Generate visualizations
    try:
        # Plot sentiment by ticker
        visualizer.plot_sentiment_by_ticker(ticker_sentiment)

        # Plot sentiment distribution
        visualizer.plot_sentiment_distribution(sentiment_df)

        # Plot sentiment over time (overall)
        visualizer.plot_sentiment_over_time(sentiment_df)

        # Get specific tickers to visualize
        if args.visualize_tickers:
            tickers_to_visualize = args.visualize_tickers.split(',')
        else:
            # Use top mentioned tickers by default
            top_tickers = ticker_sentiment.sort_values('sentiment_score_count', ascending=False)
            tickers_to_visualize = top_tickers.head(5)['mentioned_tickers'].tolist()

        # Generate ticker-specific visualizations
        for ticker in tickers_to_visualize:
            # Plot sentiment over time for this ticker
            visualizer.plot_sentiment_over_time(sentiment_df, ticker=ticker)

            # Plot price vs sentiment if financial data is available
            if not financial_df.empty:
                visualizer.plot_price_vs_sentiment(sentiment_df, financial_df, ticker)

        # Plot correlation heatmap
        if not financial_df.empty and len(tickers_to_visualize) > 0:
            visualizer.plot_sentiment_correlation_heatmap(sentiment_df, financial_df, tickers_to_visualize)

        logger.info("Visualizations generated successfully")
    except Exception as e:
        logger.error(f"Error generating visualizations: {str(e)}")


def generate_recommendations(sentiment_df, financial_df, stock_info):
    """Generate investment recommendations based on sentiment and market data"""
    if sentiment_df.empty or financial_df.empty:
        logger.warning("Insufficient data for generating recommendations")
        return None

    logger.info("Generating investment recommendations")

    try:
        # Aggregate sentiment by ticker
        ticker_sentiment = SentimentAnalyzer().aggregate_ticker_sentiment(sentiment_df)

        # Generate recommendations
        analyzer = SentimentAnalyzer()
        recommendations = analyzer.generate_investment_recommendations(
            sentiment_df=ticker_sentiment,
            financial_data_df=financial_df,
            company_info_dict=stock_info
        )

        logger.info(f"Generated {len(recommendations.get('recommendations', []))} investment recommendations")
        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return None


def main():
    """Run the complete financial sentiment analysis pipeline"""
    # Parse command line arguments
    args = parse_arguments()

    logger.info("Starting financial sentiment analysis pipeline")

    # Step 1: Scrape social media data
    twitter_df = scrape_social_media(args)

    # Step 2: Extract ticker symbols from social media data
    ticker_symbols = extract_tickers(twitter_df)

    # Step 3: Collect financial data for the identified tickers
    financial_df, stock_info = collect_financial_data(args, ticker_symbols)

    # Step 4: Analyze sentiment in social media data
    sentiment_df = analyze_sentiment(args, twitter_df)

    # Step 5: Generate visualizations
    generate_visualizations(args, sentiment_df, financial_df, ticker_symbols)

    # Step 6: Generate investment recommendations
    recommendations = generate_recommendations(sentiment_df, financial_df, stock_info)

    logger.info("Financial sentiment analysis pipeline completed")

    # Print summary of results
    print("\n===== PIPELINE SUMMARY =====")
    print(f"Social Media Data: {len(twitter_df)} tweets")
    print(f"Ticker Symbols: {len(ticker_symbols)} unique tickers identified")
    print(f"Financial Data: {len(financial_df)} data points for {len(stock_info)} companies")
    print(f"Sentiment Analysis: {len(sentiment_df)} texts analyzed")

    if recommendations:
        print("\n===== TOP INVESTMENT RECOMMENDATIONS =====")
        for rec in recommendations.get('recommendations', [])[:5]:
            print(f"{rec.get('ticker', '')}: {rec.get('recommendation', '')} - Target: {rec.get('target_price', '')}")

        print(f"\nFull recommendations saved to: {RECOMMENDATIONS_PATH}")

    print("\nVisualizations saved to: visualizations/")
    print("==========================================")


if __name__ == "__main__":
    main()
