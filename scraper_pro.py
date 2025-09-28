from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_product(url):
    """
    Takes a Flipkart URL and returns the product title and price.
    """
    driver = None
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)

        title = None
        price = None

        price_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.GURu5w._5V8g3p"))
        )
        price_str = price_element.text.strip()
        price = float(price_str.replace("₹", "").replace(",", ""))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        title_element = soup.find("meta", {"property": "og:title"})
        if title_element:
            title = title_element["content"].strip()
        
        return title, price

    except Exception as e:
        print(f"❌ An error occurred during scraping: {e}")
        return None, None

    finally:
        if driver:
            driver.quit()