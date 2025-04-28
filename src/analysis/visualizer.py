import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import logger

class DataVisualizer:
    """Generates visualizations for sentiment and market data"""
    
    def __init__(self, output_dir="visualizations"):
        """Initialize the visualizer with output directory"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Data visualizer initialized with output directory: {output_dir}")
        
        # Set up the visualization style
        sns.set(style="whitegrid")
        plt.rcParams["figure.figsize"] = (12, 8)
        plt.rcParams["font.size"] = 12
    
    def plot_sentiment_by_ticker(self, sentiment_df, top_n=15):
        """
        Plot sentiment scores for top mentioned tickers
        
        Args:
            sentiment_df (pandas.DataFrame): Aggregated sentiment data by ticker
            top_n (int): Number of top tickers to include in the plot
            
        Returns:
            str: Path to the saved visualization
        """
        if sentiment_df.empty:
            logger.warning("No sentiment data to visualize")
            return None
            
        logger.info(f"Plotting sentiment for top {top_n} tickers")
        
        # Sort by mention count and get top N
        top_tickers = sentiment_df.sort_values('sentiment_score_count', ascending=False).head(top_n)
        
        # Create a figure for the plot
        plt.figure(figsize=(14, 8))
        
        # Create a color map based on sentiment score
        colors = ['red' if score < -0.2 else 'green' if score > 0.2 else 'gray' 
                 for score in top_tickers['sentiment_score_mean']]
        
        # Create the bar plot
        ax = sns.barplot(
            x='mentioned_tickers', 
            y='sentiment_score_mean', 
            data=top_tickers,
            palette=colors
        )
        
        # Add error bars for confidence intervals
        for i, row in enumerate(top_tickers.itertuples()):
            ax.errorbar(
                i, row.sentiment_score_mean, 
                yerr=[[row.sentiment_score_mean - row.sentiment_confidence_interval_low], 
                     [row.sentiment_confidence_interval_high - row.sentiment_score_mean]],
                fmt='none', ecolor='black', capsize=5
            )
        
        # Add mention count as text on top of each bar
        for i, (_, row) in enumerate(top_tickers.iterrows()):
            plt.text(
                i, 
                row['sentiment_score_mean'] + (0.05 if row['sentiment_score_mean'] >= 0 else -0.15),
                f"n={int(row['sentiment_score_count'])}",
                ha='center'
            )
        
        # Customize the plot
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.title("Sentiment Score by Ticker (with 95% Confidence Intervals)")
        plt.xlabel("Ticker Symbol")
        plt.ylabel("Average Sentiment Score")
        plt.ylim(-1.1, 1.1)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, "sentiment_by_ticker.png")
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Sentiment by ticker plot saved to {output_path}")
        return output_path
    
    def plot_sentiment_distribution(self, sentiment_df):
        """
        Plot the distribution of sentiment scores
        
        Args:
            sentiment_df (pandas.DataFrame): Sentiment data with sentiment_score column
            
        Returns:
            str: Path to the saved visualization
        """
        if sentiment_df.empty or 'sentiment_score' not in sentiment_df.columns:
            logger.warning("No valid sentiment data for distribution plot")
            return None
            
        logger.info("Plotting sentiment score distribution")
        
        plt.figure(figsize=(12, 6))
        
        # Plot the distribution
        sns.histplot(
            sentiment_df['sentiment_score'].dropna(),
            bins=20,
            kde=True,
            color='blue'
        )
        
        # Add a vertical line for the mean
        mean_sentiment = sentiment_df['sentiment_score'].mean()
        plt.axvline(mean_sentiment, color='red', linestyle='--')
        plt.text(
            mean_sentiment + 0.05, 
            plt.ylim()[1] * 0.9,
            f"Mean: {mean_sentiment:.2f}",
            color='red'
        )
        
        # Customize the plot
        plt.title("Distribution of Sentiment Scores")
        plt.xlabel("Sentiment Score")
        plt.ylabel("Frequency")
        plt.xlim(-1.1, 1.1)
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, "sentiment_distribution.png")
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Sentiment distribution plot saved to {output_path}")
        return output_path
    
    def plot_sentiment_over_time(self, df, ticker=None, window=3):
        """
        Plot sentiment scores over time, optionally filtered by ticker
        
        Args:
            df (pandas.DataFrame): Social media data with sentiment and timestamp
            ticker (str): Optional ticker to filter by
            window (int): Window size for rolling average
            
        Returns:
            str: Path to the saved visualization
        """
        if df.empty or 'sentiment_score' not in df.columns:
            logger.warning("No valid sentiment data for time series plot")
            return None
            
        # Ensure we have a datetime column
        if 'created_utc' in df.columns:
            date_col = 'created_utc'
        elif 'created_at' in df.columns:
            date_col = 'created_at'
        else:
            logger.warning("No timestamp column found for time series plot")
            return None
            
        # Make a copy to avoid modifying the original
        plot_df = df.copy()
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(plot_df[date_col]):
            plot_df[date_col] = pd.to_datetime(plot_df[date_col])
        
        # Filter by ticker if specified
        if ticker:
            # Only include rows where the ticker is mentioned
            plot_df = plot_df[plot_df['mentioned_tickers'].apply(
                lambda tickers: ticker in tickers if isinstance(tickers, list) else False
            )]
            
            if plot_df.empty:
                logger.warning(f"No data found for ticker {ticker}")
                return None
                
            logger.info(f"Plotting sentiment over time for ticker {ticker}")
            title_suffix = f" for {ticker}"
            filename_suffix = f"_{ticker}"
        else:
            logger.info("Plotting overall sentiment over time")
            title_suffix = ""
            filename_suffix = ""
        
        # Sort by date
        plot_df = plot_df.sort_values(date_col)
        
        # Group by day and calculate mean sentiment
        plot_df['date'] = plot_df[date_col].dt.date
        daily_sentiment = plot_df.groupby('date')['sentiment_score'].agg(['mean', 'count']).reset_index()
        daily_sentiment.columns = ['date', 'sentiment', 'count']
        
        # Convert date back to datetime for plotting
        daily_sentiment['date'] = pd.to_datetime(daily_sentiment['date'])
        
        # Calculate rolling average
        daily_sentiment['sentiment_rolling'] = daily_sentiment['sentiment'].rolling(window=window, min_periods=1).mean()
        
        # Plot the time series
        plt.figure(figsize=(16, 8))
        
        # Plot daily sentiment as points
        plt.scatter(
            daily_sentiment['date'],
            daily_sentiment['sentiment'],
            s=daily_sentiment['count'] * 2,  # Size points by count
            alpha=0.5,
            label='Daily Sentiment'
        )
        
        # Plot rolling average as a line
        plt.plot(
            daily_sentiment['date'],
            daily_sentiment['sentiment_rolling'],
            color='red',
            linewidth=2,
            label=f'{window}-Day Rolling Average'
        )
        
        # Add a horizontal line at neutral sentiment
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        
        # Customize the plot
        plt.title(f"Sentiment Score Over Time{title_suffix}")
        plt.xlabel("Date")
        plt.ylabel("Average Sentiment Score")
        plt.ylim(-1.1, 1.1)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, f"sentiment_time_series{filename_suffix}.png")
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Sentiment time series plot saved to {output_path}")
        return output_path
    
    def plot_price_vs_sentiment(self, sentiment_df, financial_df, ticker, days=30):
        """
        Plot stock price against sentiment for a specific ticker
        
        Args:
            sentiment_df (pandas.DataFrame): Social media data with sentiment
            financial_df (pandas.DataFrame): Financial market data
            ticker (str): Ticker symbol to plot
            days (int): Number of days to include in the plot
            
        Returns:
            str: Path to the saved visualization
        """
        if sentiment_df.empty or financial_df.empty:
            logger.warning("Missing data for price vs sentiment plot")
            return None
            
        logger.info(f"Plotting price vs sentiment for {ticker}")
        
        # Filter financial data for the ticker
        ticker_data = financial_df[financial_df['Ticker'] == ticker].copy()
        
        if ticker_data.empty:
            logger.warning(f"No financial data found for ticker {ticker}")
            return None
            
        # Ensure Date is datetime
        if 'Date' in ticker_data.columns and not pd.api.types.is_datetime64_any_dtype(ticker_data['Date']):
            ticker_data['Date'] = pd.to_datetime(ticker_data['Date'])
            
        # Sort by date and limit to the specified number of days
        ticker_data = ticker_data.sort_values('Date')
        if len(ticker_data) > days:
            ticker_data = ticker_data.tail(days)
            
        # Filter sentiment data for the ticker
        ticker_sentiment = sentiment_df[sentiment_df['mentioned_tickers'].apply(
            lambda tickers: ticker in tickers if isinstance(tickers, list) else False
        )].copy()
        
        if ticker_sentiment.empty:
            logger.warning(f"No sentiment data found for ticker {ticker}")
            return None
            
        # Get timestamps from sentiment data
        if 'created_utc' in ticker_sentiment.columns:
            date_col = 'created_utc'
        elif 'created_at' in ticker_sentiment.columns:
            date_col = 'created_at'
        else:
            logger.warning("No timestamp column found in sentiment data")
            return None
            
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(ticker_sentiment[date_col]):
            ticker_sentiment[date_col] = pd.to_datetime(ticker_sentiment[date_col])
            
        # Group sentiment by day
        ticker_sentiment['date'] = ticker_sentiment[date_col].dt.date
        daily_sentiment = ticker_sentiment.groupby('date')['sentiment_score'].mean().reset_index()
        daily_sentiment['date'] = pd.to_datetime(daily_sentiment['date'])
        
        # Limit to the same date range as the financial data
        min_date = ticker_data['Date'].min()
        max_date = ticker_data['Date'].max()
        daily_sentiment = daily_sentiment[
            (daily_sentiment['date'] >= min_date) & (daily_sentiment['date'] <= max_date)
        ]
        
        # Create a figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(16, 8))
        
        # Plot stock price
        color = 'tab:blue'
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Stock Price ($)', color=color)
        ax1.plot(ticker_data['Date'], ticker_data['Close'], color=color, linewidth=2)
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Create second y-axis for sentiment
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Sentiment Score', color=color)
        ax2.scatter(daily_sentiment['date'], daily_sentiment['sentiment_score'], color=color, alpha=0.7)
        ax2.plot(daily_sentiment['date'], daily_sentiment['sentiment_score'], color=color, linestyle='--', alpha=0.5)
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim(-1.1, 1.1)
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
        
        # Add title and legend
        plt.title(f"{ticker} Stock Price vs. Sentiment Score")
        plt.grid(False)
        fig.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, f"price_vs_sentiment_{ticker}.png")
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Price vs sentiment plot saved to {output_path}")
        return output_path
    
    def plot_sentiment_correlation_heatmap(self, sentiment_df, financial_df, tickers, lag_days=5):
        """
        Plot a heatmap of correlations between sentiment and price movements
        
        Args:
            sentiment_df (pandas.DataFrame): Social media data with sentiment
            financial_df (pandas.DataFrame): Financial market data
            tickers (list): List of ticker symbols to include
            lag_days (int): Maximum number of lag days to include
            
        Returns:
            str: Path to the saved visualization
        """
        if sentiment_df.empty or financial_df.empty or not tickers:
            logger.warning("Missing data for correlation heatmap")
            return None
            
        logger.info(f"Plotting sentiment correlation heatmap for {len(tickers)} tickers")
        
        # Create a dataframe to store correlations
        correlations = pd.DataFrame(index=tickers, columns=[f"Lag_{i}" for i in range(lag_days+1)])
        
        for ticker in tickers:
            # Filter financial data for the ticker
            ticker_data = financial_df[financial_df['Ticker'] == ticker].copy()
            
            if ticker_data.empty:
                logger.warning(f"No financial data found for ticker {ticker}")
                continue
                
            # Calculate daily price changes
            ticker_data = ticker_data.sort_values('Date')
            ticker_data['Price_Change'] = ticker_data['Close'].pct_change() * 100
            
            # Filter sentiment data for the ticker
            ticker_sentiment = sentiment_df[sentiment_df['mentioned_tickers'].apply(
                lambda tickers: ticker in tickers if isinstance(tickers, list) else False
            )].copy()
            
            if ticker_sentiment.empty:
                logger.warning(f"No sentiment data found for ticker {ticker}")
                continue
                
            # Get timestamps from sentiment data
            if 'created_utc' in ticker_sentiment.columns:
                date_col = 'created_utc'
            elif 'created_at' in ticker_sentiment.columns:
                date_col = 'created_at'
            else:
                logger.warning("No timestamp column found in sentiment data")
                continue
                
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(ticker_sentiment[date_col]):
                ticker_sentiment[date_col] = pd.to_datetime(ticker_sentiment[date_col])
                
            # Group sentiment by day
            ticker_sentiment['date'] = ticker_sentiment[date_col].dt.date
            daily_sentiment = ticker_sentiment.groupby('date')['sentiment_score'].mean().reset_index()
            daily_sentiment['date'] = pd.to_datetime(daily_sentiment['date'])
            
            # Ensure Date is datetime in ticker_data
            if not pd.api.types.is_datetime64_any_dtype(ticker_data['Date']):
                ticker_data['Date'] = pd.to_datetime(ticker_data['Date'])
                
            # Merge datasets on date
            merged_data = pd.merge(daily_sentiment, ticker_data[['Date', 'Price_Change']], 
                                   left_on='date', right_on='Date', how='inner')
            
            # Calculate correlations for different lags
            for lag in range(lag_days+1):
                if lag == 0:
                    # Same-day correlation
                    corr = merged_data['sentiment_score'].corr(merged_data['Price_Change'])
                else:
                    # Sentiment leading price changes by 'lag' days
                    merged_data[f'Price_Change_Lag_{lag}'] = merged_data['Price_Change'].shift(-lag)
                    corr = merged_data['sentiment_score'].corr(merged_data[f'Price_Change_Lag_{lag}'])
                
                correlations.loc[ticker, f"Lag_{lag}"] = corr
        
        # Drop any tickers with no data
        correlations = correlations.dropna(how='all')
        
        if correlations.empty:
            logger.warning("No correlation data to plot")
            return None
        
        # Plot the heatmap
        plt.figure(figsize=(10, max(8, len(correlations) * 0.4)))
        
        # Create a custom colormap centered at zero
        cmap = sns.diverging_palette(10, 240, as_cmap=True)
        
        # Plot the heatmap
        ax = sns.heatmap(
            correlations,
            cmap=cmap,
            center=0,
            vmin=-1, vmax=1,
            annot=True,
            fmt=".2f",
            linewidths=.5
        )
        
        # Customize the plot
        plt.title("Correlation between Sentiment and Future Price Changes")
        plt.xlabel("Days Between Sentiment and Price Change")
        plt.ylabel("Ticker Symbol")
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, "sentiment_correlation_heatmap.png")
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Correlation heatmap saved to {output_path}")
        return output_path

if __name__ == "__main__":
    # Example usage
    import random
    from datetime import datetime, timedelta
    
    # Create some sample data
    visualizer = DataVisualizer()
    
    # Sample sentiment data
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
    sentiment_data = []
    
    for ticker in tickers:
        sentiment_mean = random.uniform(-0.8, 0.8)
        count = random.randint(10, 100)
        std = random.uniform(0.1, 0.4)
        
        sentiment_data.append({
            'mentioned_tickers': ticker,
            'sentiment_score_mean': sentiment_mean,
            'sentiment_score_count': count,
            'sentiment_score_std': std,
            'bullish_probability': max(0, sentiment_mean + 0.5) / 2,
            'bearish_probability': max(0, -sentiment_mean + 0.5) / 2,
            'neutral_probability': 0.5 - abs(sentiment_mean) / 2,
            'confidence': random.uniform(0.6, 0.9),
            'sentiment_std_error': std / (count ** 0.5),
            'sentiment_confidence_interval_low': sentiment_mean - std / (count ** 0.5) * 1.96,
            'sentiment_confidence_interval_high': sentiment_mean + std / (count ** 0.5) * 1.96
        })
    
    sentiment_df = pd.DataFrame(sentiment_data)
    
    # Create a sample visualization
    visualizer.plot_sentiment_by_ticker(sentiment_df)
    print("Created example visualization")