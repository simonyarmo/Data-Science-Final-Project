import csv  # Import the csv module
from yahoo_finace import scrape_yahoo_finance

if __name__=="__main__":
    tickers = [['Tesla', 'TSLA'], ['Apple', 'AAPL'], ['Microsoft', 'MSFT']]
    
    # Open a CSV file for writing
    with open('scraped_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Ticker', 'Current Price', 'Market Cap', 'P/E Ratio'])  # Write the header
        
        for ticker in tickers:
            name, ticker = ticker
            print(f"Scraping data for {name} ({ticker})...")
            data = scrape_yahoo_finance(ticker)
            print(data)
            
            # Write the name, ticker, and selected data to the CSV file
            writer.writerow([name, ticker, data['Current Price'], data['Market Cap'], data['P/E Ratio']])  # Write the selected data row
            
    print("Data has been written to scraped_data.csv")