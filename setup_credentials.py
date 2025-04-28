#!/usr/bin/env python3
"""
Helper script to set up API credentials for the financial sentiment analysis pipeline.
This script will guide the user through setting up the necessary API keys and credentials.
"""

import os
import sys
from dotenv import load_dotenv, set_key

def get_input(prompt, default=None, required=True):
    """Get input from user with a prompt and optional default value"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
        
    value = input(prompt).strip()
    
    if not value and default:
        return default
    elif not value and required:
        print("This field is required.")
        return get_input(prompt, default, required)
    else:
        return value

def setup_openai():
    """Set up OpenAI API credentials"""
    print("\n=== OpenAI API Setup ===")
    print("You need an OpenAI API key to use the sentiment analysis features.")
    print("If you don't have one, go to: https://platform.openai.com/account/api-keys")
    
    # Check if key already exists
    existing_key = os.getenv("OPENAI_KEY")
    
    if existing_key:
        print(f"Found existing OpenAI API key: {existing_key[:8]}...{existing_key[-4:]}")
        update = get_input("Do you want to update this key? (y/n)", "n", required=False).lower()
        if update != "y":
            return existing_key
    
    # Get new key
    openai_key = get_input("Enter your OpenAI API key")
    return openai_key

def setup_reddit():
    """Set up Reddit API credentials"""
    print("\n=== Reddit API Setup ===")
    print("You need Reddit API credentials to scrape data from Reddit.")
    print("To get these, go to: https://www.reddit.com/prefs/apps")
    print("Create a new app, select 'script' as the type.")
    
    # Check if credentials already exist
    existing_client_id = os.getenv("REDDIT_CLIENT_ID")
    existing_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    existing_user_agent = os.getenv("REDDIT_USER_AGENT")
    
    if existing_client_id and existing_client_secret:
        print(f"Found existing Reddit API credentials.")
        update = get_input("Do you want to update these credentials? (y/n)", "n", required=False).lower()
        if update != "y":
            return {
                "REDDIT_CLIENT_ID": existing_client_id,
                "REDDIT_CLIENT_SECRET": existing_client_secret,
                "REDDIT_USER_AGENT": existing_user_agent or "Financial Sentiment Bot by /u/your_username"
            }
    
    # Get new credentials
    client_id = get_input("Enter your Reddit Client ID")
    client_secret = get_input("Enter your Reddit Client Secret")
    user_agent = get_input("Enter your Reddit User Agent", "Financial Sentiment Bot by /u/your_username")
    
    return {
        "REDDIT_CLIENT_ID": client_id,
        "REDDIT_CLIENT_SECRET": client_secret,
        "REDDIT_USER_AGENT": user_agent
    }

def setup_twitter():
    """Set up Twitter API credentials"""
    print("\n=== Twitter API Setup ===")
    print("You need Twitter API credentials to scrape data from Twitter.")
    print("To get these, go to: https://developer.twitter.com/en/portal/dashboard")
    print("Create a new Project and App, and create access tokens.")
    
    # Check if credentials already exist
    existing_api_key = os.getenv("TWITTER_API_KEY")
    existing_api_secret = os.getenv("TWITTER_API_SECRET")
    existing_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    existing_access_secret = os.getenv("TWITTER_ACCESS_SECRET")
    
    if existing_api_key and existing_api_secret and existing_access_token and existing_access_secret:
        print(f"Found existing Twitter API credentials.")
        update = get_input("Do you want to update these credentials? (y/n)", "n", required=False).lower()
        if update != "y":
            return {
                "TWITTER_API_KEY": existing_api_key,
                "TWITTER_API_SECRET": existing_api_secret,
                "TWITTER_ACCESS_TOKEN": existing_access_token,
                "TWITTER_ACCESS_SECRET": existing_access_secret
            }
    
    # Get new credentials
    api_key = get_input("Enter your Twitter API Key")
    api_secret = get_input("Enter your Twitter API Secret")
    access_token = get_input("Enter your Twitter Access Token")
    access_secret = get_input("Enter your Twitter Access Token Secret")
    
    return {
        "TWITTER_API_KEY": api_key,
        "TWITTER_API_SECRET": api_secret,
        "TWITTER_ACCESS_TOKEN": access_token,
        "TWITTER_ACCESS_SECRET": access_secret
    }

def main():
    """Run the credential setup process"""
    print("=== Financial Sentiment Analysis API Credential Setup ===")
    print("This script will help you set up the API credentials needed for the sentiment analysis pipeline.")
    
    # Load existing environment variables
    env_file = ".env"
    load_dotenv(env_file)
    
    # Dictionary to store all credentials
    credentials = {}
    
    # OpenAI is required
    openai_key = setup_openai()
    credentials["OPENAI_KEY"] = openai_key
    
    # Reddit is optional
    setup_reddit_api = get_input("Do you want to set up Reddit API credentials? (y/n)", "y", required=False).lower()
    if setup_reddit_api == "y":
        reddit_creds = setup_reddit()
        credentials.update(reddit_creds)
    
    # Twitter is optional
    setup_twitter_api = get_input("Do you want to set up Twitter API credentials? (y/n)", "y", required=False).lower()
    if setup_twitter_api == "y":
        twitter_creds = setup_twitter()
        credentials.update(twitter_creds)
    
    # Save credentials to .env file
    print("\nSaving credentials to .env file...")
    
    for key, value in credentials.items():
        set_key(env_file, key, value)
    
    print("Credentials saved successfully!")
    print("\nYou can now run the sentiment analysis pipeline with:")
    print("  source venv/bin/activate")
    print("  python run_analysis.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 