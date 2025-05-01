import pandas as pd
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def merge_news_files(input_dir: str = '../data/raw', output_dir: str = '../data/processed') -> None:
    """
    Merge multiple news CSV files into a single dataframe and save it.
    
    Args:
        input_dir: Directory containing the input CSV files
        output_dir: Directory to save the merged output
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # List of files to merge
    files_to_merge = ['tesla_news.csv', 'nvda_news.csv', 'ba_news.csv']
    
    # Initialize empty list to store dataframes
    dfs = []
    
    # Read and process each file
    for file in files_to_merge:
        file_path = os.path.join(input_dir, file)
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                logger.info(f"Successfully read {file} with {len(df)} rows")
                dfs.append(df)
            except Exception as e:
                logger.error(f"Error reading {file}: {str(e)}")
        else:
            logger.warning(f"File not found: {file}")
    
    if not dfs:
        logger.error("No dataframes to merge. Check if input files exist.")
        return
    
    # Merge all dataframes
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Sort by date (most recent first)
    merged_df['as_of_date'] = pd.to_datetime(merged_df['as_of_date'])
    merged_df = merged_df.sort_values('as_of_date', ascending=False)
    
    # Remove any duplicates based on headline and ticker
    merged_df = merged_df.drop_duplicates(subset=['headline', 'ticker'], keep='first')
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'merged_news_{timestamp}.csv')
    
    # Save merged dataframe
    merged_df.to_csv(output_file, index=False)
    
    # Log summary statistics
    logger.info(f"\nMerged News Summary:")
    logger.info(f"Total articles: {len(merged_df)}")
    logger.info(f"\nArticles by ticker:")
    logger.info(merged_df['ticker'].value_counts())
    logger.info(f"\nDate range:")
    logger.info(f"Earliest: {merged_df['as_of_date'].min()}")
    logger.info(f"Latest: {merged_df['as_of_date'].max()}")
    logger.info(f"\nSaved merged data to: {output_file}")

if __name__ == "__main__":
    merge_news_files() 