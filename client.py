import asyncio
from twikit import Client
import pandas as pd

USERNAME = 'DataForSci'
EMAIL = 'simonyarmo@utexas.edu'
PASSWORD = 'Redcar123!'

# Initialize client
client = Client('en-US')

def generate_stock_keywords(name, ticker, extras=[]):
    base = [
        name, f"${ticker}", f"{name} stock", f"{name} Tarrifs", f"#{ticker}"
    ]
    return base + extras

stocks = {
    "Tesla": generate_stock_keywords("Tesla", "TSLA", ["EV stock", "Tesla earnings",]),
    "Boeing Company": generate_stock_keywords("Boeing Company", "BA", ["Boeing",  "Boeing earnings"]),
    "Nvidia": generate_stock_keywords("Nvidia", "NVDA", ["Nvidia earnings", "Nvidia AI stock",])
    }


async def main():
    await client.login(
        auth_info_1=USERNAME,
        auth_info_2=EMAIL,
        password=PASSWORD,
        cookies_file='cookies.json'
    )
    tweet_data={
        "Tesla": [],
        "Boeing Company": [],
        "Nvidia": []
    }
    for name in stocks.keys():
        for item in stocks[name]:
            tweets = await client.search_tweet(item, 'Top',15)
            for tweet in tweets:
                tweet_data[name].append([tweet.created_at,"stocks[name][1]",tweet.text])
    
    return tweet_data

def toCSV(tweet_data):
    all_tweets = []
    for company, tweets in tweet_data.items():
        for tweet in tweets:
            all_tweets.append({
                'company': company,
                'timestamp': tweet[0],
                'ticker': tweet[1],
                'tweet_text': tweet[2]
            })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(all_tweets)
    df.to_csv('stock_tweets.csv', index=False)



if __name__ == "__main__":
    tweet_data =asyncio.run(main())
    toCSV(tweet_data)

