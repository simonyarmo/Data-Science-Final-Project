import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    FINANCIAL_DATA_PATH, DEFAULT_START_DATE, DEFAULT_END_DATE, logger
)

class FinancialDataCollector:
    """Collects financial data for stocks and markets from Yahoo Finance"""
    
    def __init__(self):
        """Initialize the financial data collector"""
        logger.info("Financial data collector initialized")
    
    def get_stock_data(self, ticker_symbols, start_date=None, end_date=None):
        """
        Get historical stock data for specified tickers
        
        Args:
            ticker_symbols (list): List of ticker symbols to retrieve data for
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            dict: Dictionary with ticker symbols as keys and DataFrames as values
        """
        if not ticker_symbols:
            logger.warning("No ticker symbols provided")
            return {}
            
        if start_date is None:
            start_date = DEFAULT_START_DATE
        if end_date is None:
            end_date = DEFAULT_END_DATE
            
        logger.info(f"Getting stock data for {len(ticker_symbols)} tickers from {start_date} to {end_date}")
        
        # Filter out invalid tickers
        valid_tickers = []
        for ticker in ticker_symbols:
            if isinstance(ticker, str) and ticker.isalpha() and len(ticker) >= 1 and len(ticker) <= 5:
                valid_tickers.append(ticker)
            
        if not valid_tickers:
            logger.warning("No valid ticker symbols after filtering")
            return {}
            
        # Get data for each ticker
        stock_data = {}
        for ticker in valid_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    # Add ticker column
                    hist['Ticker'] = ticker
                    stock_data[ticker] = hist
                    logger.info(f"Retrieved data for {ticker}: {len(hist)} rows")
                else:
                    logger.warning(f"No data found for ticker {ticker}")
                    
            except Exception as e:
                logger.error(f"Error getting data for ticker {ticker}: {str(e)}")
                
        return stock_data
    
    def get_ticker_info(self, ticker_symbols):
        """
        Get company information for specified tickers
        
        Args:
            ticker_symbols (list): List of ticker symbols to retrieve info for
            
        Returns:
            dict: Dictionary with ticker symbols as keys and company info as values
        """
        if not ticker_symbols:
            logger.warning("No ticker symbols provided")
            return {}
            
        logger.info(f"Getting company info for {len(ticker_symbols)} tickers")
        
        # Filter out invalid tickers
        valid_tickers = []
        for ticker in ticker_symbols:
            if isinstance(ticker, str) and ticker.isalpha() and len(ticker) >= 1 and len(ticker) <= 5:
                valid_tickers.append(ticker)
                
        if not valid_tickers:
            logger.warning("No valid ticker symbols after filtering")
            return {}
            
        # Get info for each ticker
        ticker_info = {}
        for ticker in valid_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                if info:
                    # Extract key information
                    key_info = {
                        'name': info.get('shortName', ''),
                        'sector': info.get('sector', ''),
                        'industry': info.get('industry', ''),
                        'market_cap': info.get('marketCap', None),
                        'fiftytwo_week_high': info.get('fiftyTwoWeekHigh', None),
                        'fiftytwo_week_low': info.get('fiftyTwoWeekLow', None),
                        'average_volume': info.get('averageVolume', None),
                        'trailing_pe': info.get('trailingPE', None),
                        'forward_pe': info.get('forwardPE', None),
                        'dividend_yield': info.get('dividendYield', None),
                        'beta': info.get('beta', None),
                        'description': info.get('longBusinessSummary', '')
                    }
                    ticker_info[ticker] = key_info
                    logger.info(f"Retrieved info for {ticker}")
                else:
                    logger.warning(f"No info found for ticker {ticker}")
                    
            except Exception as e:
                logger.error(f"Error getting info for ticker {ticker}: {str(e)}")
                
        return ticker_info
    
    def get_market_indices(self, start_date=None, end_date=None):
        """
        Get data for major market indices
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            dict: Dictionary with index symbols as keys and DataFrames as values
        """
        if start_date is None:
            start_date = DEFAULT_START_DATE
        if end_date is None:
            end_date = DEFAULT_END_DATE
            
        # Major indices to track
        indices = ['^GSPC', '^DJI', '^IXIC', '^VIX', '^FTSE', '^N225']
        index_names = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^VIX': 'VIX',
            '^FTSE': 'FTSE 100',
            '^N225': 'Nikkei 225'
        }
        
        logger.info(f"Getting data for {len(indices)} market indices from {start_date} to {end_date}")
        
        # Get data for each index
        index_data = {}
        for idx in indices:
            try:
                index = yf.Ticker(idx)
                hist = index.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    # Add index name column
                    hist['Index'] = index_names.get(idx, idx)
                    index_data[idx] = hist
                    logger.info(f"Retrieved data for {index_names.get(idx, idx)}: {len(hist)} rows")
                else:
                    logger.warning(f"No data found for index {index_names.get(idx, idx)}")
                    
            except Exception as e:
                logger.error(f"Error getting data for index {index_names.get(idx, idx)}: {str(e)}")
                
        return index_data
    
    def combine_stock_data(self, stock_data):
        """
        Combine stock data for multiple tickers into a single DataFrame
        
        Args:
            stock_data (dict): Dictionary with ticker symbols as keys and DataFrames as values
            
        Returns:
            pandas.DataFrame: Combined DataFrame
        """
        if not stock_data:
            return pd.DataFrame()
            
        all_data = []
        for ticker, data in stock_data.items():
            if not data.empty:
                # Reset index to make date a column
                df = data.reset_index()
                all_data.append(df)
                
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Combined stock data: {len(combined_df)} rows")
            return combined_df
        else:
            logger.warning("No data to combine")
            return pd.DataFrame()
    
    def save_data(self, df, stock_info=None, output_path=None):
        """
        Save the financial data to files
        
        Args:
            df (pandas.DataFrame): DataFrame containing stock data
            stock_info (dict): Dictionary with company information
            output_path (str): Path where the CSV file will be saved
            
        Returns:
            str: Path where the data was saved
        """
        if output_path is None:
            output_path = FINANCIAL_DATA_PATH
            
        if df.empty:
            logger.warning("No data to save")
            return None
            
        try:
            # Create directory if it doesn't exist
            folder = os.path.dirname(output_path)
            if folder:
                os.makedirs(folder, exist_ok=True)

            # Save stock data to CSV
            df.to_csv(output_path, index=False)
            logger.info(f"Stock data saved to {output_path}")
            
            # If we have stock info, save it to JSON
            if stock_info:
                info_path = output_path.replace('.csv', '_info.json')
                with open(info_path, 'w') as f:
                    json.dump(stock_info, f, indent=2)
                logger.info(f"Stock info saved to {info_path}")
                
            return output_path
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return None
    
    def collect_data_for_tickers(self, ticker_symbols, start_date=None, end_date=None, output_path=None):
        """
        Collect and save all financial data for specified tickers
        
        Args:
            ticker_symbols (list): List of ticker symbols to retrieve data for
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            output_path (str): Path where the CSV file will be saved
            
        Returns:
            tuple: (DataFrame with stock data, dict with company info)
        """
        # Get stock price data
        stock_data = self.get_stock_data(ticker_symbols, start_date, end_date)
        
        # Get company information
        stock_info = self.get_ticker_info(ticker_symbols)
        
        # Get market indices for reference
        index_data = self.get_market_indices(start_date, end_date)
        
        # Combine all stock data
        all_stock_data = {**stock_data, **index_data}
        combined_df = self.combine_stock_data(all_stock_data)
        
        # Save data
        self.save_data(combined_df, stock_info, output_path)
        
        return combined_df, stock_info

if __name__ == "__main__":
    # Example usage
    collector = FinancialDataCollector()
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    df, info = collector.collect_data_for_tickers(tickers)
    print(f"Collected data for {len(info)} tickers") 