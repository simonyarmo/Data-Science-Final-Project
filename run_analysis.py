#!/usr/bin/env python3
"""
Sample script to run the financial sentiment analysis pipeline.
This is a convenience wrapper around src/main.py with default settings.
"""

import sys
import os
import subprocess

def main():
    """Run the sentiment analysis pipeline with default settings"""
    print("Starting Financial Sentiment Analysis Pipeline")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set working directory to script directory
    os.chdir(script_dir)
    
    # Ensure the virtual environment is activated
    if not os.environ.get('VIRTUAL_ENV'):
        print("Virtual environment not activated. Please run:")
        print("  source venv/bin/activate")
        return 1
    
    # Build the command with appropriate arguments
    cmd = [
        "python", "src/main.py",
        "--reddit-limit", "50",          # Limit posts per subreddit
        "--twitter-limit", "50",         # Limit tweets per query
        "--days-back", "7"               # Look back 7 days for social media
    ]
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
        print("Pipeline completed successfully")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"Error running pipeline: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 