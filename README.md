# Financial News Sentiment Analysis Project

This project analyzes financial news sentiment for major tech and aerospace companies (TSLA, NVDA, BA) using natural language processing and machine learning techniques. The project combines news data collection with sentiment analysis to understand market sentiment trends.

## Project Overview

The project consists of three main components:

1. **News Data Collection**
   - Utilizes Finnhub API to gather financial news articles
   - Collects news for Tesla (TSLA), NVIDIA (NVDA), and Boeing (BA)
   - Implements automated data collection and storage pipeline

2. **Sentiment Analysis**
   - Employs FinBERT model for financial sentiment analysis
   - Processes news headlines and content
   - Generates sentiment scores and bullish/bearish probabilities
   - Aggregates sentiment data for trend analysis

3. **Analysis & Visualization**
   - Individual analysis notebooks for each company:
     - Tesla Analysis
     - NVIDIA Analysis
     - Boeing Analysis
   - Sentiment trend visualization
   - News impact assessment

## Project Structure

```
src/
├── analysis/           # Analysis scripts and notebooks
│   ├── Tesla_Analysis.ipynb
│   ├── Nvidia_Analysis.ipynb
│   ├── Boeing.ipynb
│   ├── sentiment_analyzer.py
│   └── train_stock_signal.py
├── scrapers/          # Data collection modules
│   ├── news_scraper.py
│   └── merge_news.py
└── data/              # Data storage
    ├── processed/     # Cleaned and analyzed data
    └── raw/          # Raw collected data
```

## Technologies Used

- Python 3.x
- Pandas for data manipulation
- FinBERT for sentiment analysis
- Finnhub API for financial news data
- Jupyter Notebooks for analysis and visualization 