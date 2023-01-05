import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np
import time
import re

# Get the categories of food items and the nutrients we want to extract
from constants import *

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
def extract_product_info(product_url, category):

    # Wait for 1 second to prevent overloading the server
    time.sleep(1)

    data = {}

    try:
        html = requests.get(product_url, headers=AGENT, timeout=None).text
    except requests.exceptions.ReadTimeout:
        print("Time out for product, skipping...")
        return

    soup = BeautifulSoup(html, 'html.parser')

     # Get the name of the product
    name = soup.find('h1').text
    
    # Print the name for logging progress
    print(name)
    data['Name'] = name
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
def parse_category(dataframe, base_url, category):

    print(f"Began category {category}")

    # Represents the number of products to skip
    offset = 0

    # Create temp variable for stopping loop by checking if duplication occurs
    temp = None

    while (True):

        print(f"Page: {offset // 24 + 1}")

        # Request the html content of the page and parse it
        # Retry if the request times out
        try:
            html = requests.get(f"{base_url}/producten/{category}?offset={offset}", headers=AGENT, timeout=None).text
        except requests.exceptions.ReadTimeout:
            print("Time out for page, retrying...")
            continue

        soup = BeautifulSoup(html, 'html.parser')

        # Get href of all the products
        products = soup.find_all(attrs={"analytics-tag" : "product card"})

        # Stop if the product page starts looping
        if (temp == products):
            print(f"Finished category {category}")
            return
            

        # Loop through all the products
        for product in products:
            product_addend = product.find('a').get('href')
            product_url = base_url + product_addend
            
            info = extract_product_info(product_url, category)

            if info:
                dataframe.append(info)
        
        temp = products.copy()
        
        # There are 24 products per page
        offset += 24
    

def main():

    # Set website URL of Albert Hijn
    url = 'https://www.jumbo.com'
    nutritional_information = []

    # Loop through all the categories
    for category in CATEGORIES:
        parse_category(nutritional_information, url, category)

    # Create a dataframe from the nutritional information
    df = pd.DataFrame(nutritional_information)

    df.to_csv('groceries.csv', index=False)


if __name__ == '__main__':
    main()