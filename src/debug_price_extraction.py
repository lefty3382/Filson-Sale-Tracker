#!/usr/bin/env python3
"""Debug price extraction for specific products."""

import requests
import re
from scraper import WebScraper

# Test the Tin Cloth Primaloft Jacket specifically
test_url = "https://www.filson.com/products/tin-cloth-primaloft%C2%AE-jacket-black"

print(f"Testing price extraction for: {test_url}")

# Create a minimal config for testing
config = {
    'user_agent': 'Sale-Tracker/1.0',
    'max_retries': 3,
    'timeout': 30000,
    'request_delay': 1000
}

scraper = WebScraper(config)
price, original_price = scraper._fetch_product_price(test_url)

print(f"Extracted price: ${price}")
print(f"Extracted original_price: ${original_price}")

if price and original_price and original_price > price:
    discount_percent = ((original_price - price) / original_price) * 100
    print(f"Discount: {discount_percent:.1f}% off")
else:
    print("No discount detected or missing price data")

# Let's also test the other one
test_url2 = "https://www.filson.com/products/tin-cloth-primaloft%C2%AE-vest-black"

print(f"\nTesting price extraction for: {test_url2}")
price2, original_price2 = scraper._fetch_product_price(test_url2)

print(f"Extracted price: ${price2}")
print(f"Extracted original_price: ${original_price2}")

if price2 and original_price2 and original_price2 > price2:
    discount_percent2 = ((original_price2 - price2) / original_price2) * 100
    print(f"Discount: {discount_percent2:.1f}% off")
else:
    print("No discount detected or missing price data")