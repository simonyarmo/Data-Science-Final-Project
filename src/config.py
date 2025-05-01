import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Directory paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# News settings
NEWS_DATA_PATH = os.path.join(DATA_DIR, "financial_news.csv") 