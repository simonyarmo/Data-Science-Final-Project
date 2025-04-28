# Financial Sentiment Analysis Project

This project analyzes sentiment from financial news and social media to evaluate its correlation with market movements.

## Features

1. **Social Media Scraping**: Collects trending financial discussions from Reddit and Twitter (X)
2. **Financial Data Collection**: Gathers market data from Yahoo Finance based on trends found in social media
3. **AI-Powered Analysis**: Uses OpenAI to analyze sentiment and generate investment recommendations

## Setup

1. Clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment:
   - On macOS/Linux: `source venv/bin/activate`
   - On Windows: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your API keys (see Configuration section)
6. Run the application: `python src/main.py`

## Configuration

Create a `.env` file in the root directory with the following variables:

```
OPENAI_KEY="your-openai-api-key"
REDDIT_CLIENT_ID="your-reddit-client-id"
REDDIT_CLIENT_SECRET="your-reddit-client-secret"
REDDIT_USER_AGENT="your-user-agent"
TWITTER_API_KEY="your-twitter-api-key"
TWITTER_API_SECRET="your-twitter-api-secret"
TWITTER_ACCESS_TOKEN="your-twitter-access-token"
TWITTER_ACCESS_SECRET="your-twitter-access-secret"
```

## Project Structure

- `src/scrapers/`: Contains scripts for scraping social media platforms
- `src/data/`: Handles data collection and storage
- `src/analysis/`: Contains sentiment analysis and market correlation code 