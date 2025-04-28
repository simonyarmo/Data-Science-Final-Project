import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# API Keys
OPENAI_KEY = os.getenv("OPENAI_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# Reddit settings
SUBREDDITS = [
    "wallstreetbets",
    "investing",
    "stocks",
    "finance",
    "economics",
    "SecurityAnalysis",
    "options",
    "StockMarket",
    "CryptoCurrency"
]

# Twitter settings
TWITTER_SEARCH_QUERIES = [
    "$SPY", "$QQQ", "$AAPL", "$MSFT", "$AMZN", "$NVDA", "$TSLA", 
    "$META", "$GOOGL", "$BTC", "$ETH", "#stocks", "#investing",
    "#stockmarket", "#finance", "#WallStreetBets", "#crypto"
]

# Data storage settings
DATA_DIR = "data"
REDDIT_DATA_PATH = os.path.join(DATA_DIR, "reddit_data.csv")
TWITTER_DATA_PATH = os.path.join(DATA_DIR, "twitter_data.csv")
FINANCIAL_DATA_PATH = os.path.join(DATA_DIR, "financial_data.csv")
SENTIMENT_DATA_PATH = os.path.join(DATA_DIR, "sentiment_data.csv")
RECOMMENDATIONS_PATH = os.path.join(DATA_DIR, "recommendations.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Default financial data settings
DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = "2023-12-31"

# OpenAI settings
OPENAI_MODEL = "gpt-4" 
MAX_TOKENS = 1000 