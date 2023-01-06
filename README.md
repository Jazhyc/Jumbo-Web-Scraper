# Jumbo Web Scraper and Food Products Dataset

A lightweight web scraper for scraping product data of food items from the supermarket chain Jumbo.nl. The program uses beautiful soup to parse the HTML and extract data regarding name, price, nutrition facts, and category. In order to circumvent the dynamic loading of products, the program uses Selenium to interact with the javascript. The program also complies with the robots.txt file of Jumbo.nl by sending one request every 10 seconds. Once the data is scraped, it is saved in a csv file.
