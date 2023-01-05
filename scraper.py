import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import numpy as np
import time
import re

# Get the categories of food items and the nutrients we want to extract
from constants import *

# Set up the browser to parse the website
#user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'
chrome_options = Options()
# chrome_options.add_argument("--headless")
#chrome_options.add_argument(f'user-agent={user_agent}')
# chrome_options.add_argument("--window-size=1920,1080")

# Finds the first number in a string
def find_first_number(text):
  # Find the first occurrence of a number in the text
  match = re.search(r'\b\d+(?:\.\d+)?\b', text)
  if match:
    # Return the number if found
    return float(match.group())
  else:
    # Return None if no number was found
    return None


# Extracts the product information from the HTML content on each page
def extract_product_info(product_url, category, browser):

    # Wait for 10 seconds to prevent overloading the server
    # This is the value set in the robots.txt file
    time.sleep(10)

    data = {}

    try:
        browser.get(product_url)
        html = browser.page_source
    except:
        print("Time out for product, skipping...")
        return

    soup = BeautifulSoup(html, 'html.parser')

     # Get the name of the product
    name = soup.find('h1').text
    price = soup.find(attrs={'class': 'current-price'}).text
    
    # Print the name for logging progress
    print(name, ".".join(price.split()))
    data['Name'] = name
    data['Price'] = ".".join(price.split())
    data['Category'] = category

    table = soup.find('tbody').find_all('tr')

    for row in table:

        details = row.find_all('td')

        if (len(details) < 2):
            continue

        nutrient = details[0].text

        if not nutrient:
            nutrient = 'Joules'

        value = find_first_number(details[1].text)

        data[nutrient] = value

    return data

# Gets all the products from a category
def parse_category(dataframe, base_url, category, browser, subBrowser):

    print(f"Began category {category}")

    # Represents the number of products to skip
    offset = 0

    # Go to the first page of the category
    browser.get(f"{base_url}/producten/{category}?&offset={offset}")

    # Create temp variable for stopping loop by checking if duplication occurs
    temp = None

    while (True):

        print(f"Page: {offset // 24 + 1}")

        # Request the html content of the page and parse it. Wait a while for the website to load
        # Retry if the request times out
        try:
            WebDriverWait(browser, 10).until(lambda x: x.find_element_by_class_name('page'))
            time.sleep(3)
            html = browser.page_source
        except:
            print("Time out for page, skipping...")
            return

        soup = BeautifulSoup(html, 'html.parser')

        # Get href of all the products
        products = soup.find_all(attrs={"analytics-tag" : "product card"})

        #? It may be better to handle duplicates in the end
        # # Stop if the product page starts looping
        # if (temp == products):

        #     try:
        #         element = browser.find_element_by_name("next").click()
        #     except:
        #         print(f"Finished category {category}")
        #         subBrowser.quit()
        #         return

        #     continue
            
        # Loop through all the products
        for product in products:
            product_addend = product.find('a').get('href')
            product_url = base_url + product_addend
            
            try:
                info = extract_product_info(product_url, category, subBrowser)
            except:
                print("Error extracting product info, skipping...")
                continue

            if info:
                dataframe.append(info)
        
        temp = products.copy()
        
        # There are 24 products per page
        offset += 24

        try:
            element = browser.find_element_by_name("next").click()
        except:
            print(f"Finished category {category}")
            return
    

def main():

    # Set website URL of Albert Hijn
    url = 'https://www.jumbo.com'
    nutritional_information = []

    browser = Chrome(options=chrome_options)
    browser.get(f"{url}")
    time.sleep(1)
    browser.find_element_by_id('onetrust-accept-btn-handler').click()
    time.sleep(1)

    try:
        # Get rid of the emergency popup
        element = browser.find_element_by_css_selector(".jum-button.close.tertiary.icon")
        print('Element', element)
        element.click()
        time.sleep(1)
    except:
        print('No emergency popup')

    # Create a secondary browser to get the product information
    subBrowser = Chrome(options=chrome_options)

    # Loop through all the categories
    for category in CATEGORIES:
        parse_category(nutritional_information, url, category, browser, subBrowser)

    # Create a dataframe from the nutritional information
    df = pd.DataFrame(nutritional_information)

    df.to_csv('groceries.csv', index=False)

    browser.quit()
    subBrowser.quit()


if __name__ == '__main__':
    main()