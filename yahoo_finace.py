from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

def scrape_yahoo_finance(ticker):
    # Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Set your driver path here
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        driver.get(url)
        
        time.sleep(1)  # Wait for page to load
        
        # Get current stock price
        try:
            price = driver.find_element(By.CSS_SELECTOR, '[data-testid="qsp-price"]').text

        except Exception:
            price = "N/A"

        # Get Market Cap
        try:
            market_cap_element = driver.find_element(By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[3]/ul/li[9]/span[2]/fin-streamer')
            market_cap = market_cap_element.text
        except Exception:
            market_cap = "N/A"

        # Get P/E Ratio
        try:
            pe_ratio_element = driver.find_element(By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[3]/ul/li[11]/span[2]/fin-streamer')
            pe_ratio = pe_ratio_element.text
        except Exception:
            pe_ratio = "N/A"

        return {
            'Ticker': ticker,
            'Current Price': price,
            'Market Cap': market_cap,
            'P/E Ratio': pe_ratio
        }

    finally:
        driver.quit()

# Example usage:
if __name__ == "__main__":
    stock_data = scrape_yahoo_finance('FOUR')
    print(stock_data)
