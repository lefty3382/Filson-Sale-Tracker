#!/usr/bin/env python3
"""
Test script to verify price extraction from Tin Cloth Cruiser product page
"""

import sys
import os
sys.path.append('src')

from scraper import WebScraper
import logging

# Set up logging to see debug info
logging.basicConfig(level=logging.DEBUG)

# Create a test config
test_config = {
    'user_agent': 'Sale-Tracker-Test/1.0',
    'request_delay': 1000,
    'timeout': 30000,
    'max_retries': 2
}

scraper = WebScraper(test_config)

# Test the Tin Cloth Cruiser URL
test_url = "https://www.filson.com/products/tin-cloth-cruiser-jacket-realtree-hardwoods-camo"

print(f"Testing price extraction for: {test_url}")

price, original_price = scraper._fetch_product_price(test_url)

print(f"\nResults:")
print(f"Current Price: ${price}" if price else "Current Price: Not found")
print(f"Original Price: ${original_price}" if original_price else "Original Price: Not found")

if price and original_price and original_price > price:
    discount = ((original_price - price) / original_price) * 100
    savings = original_price - price
    print(f"Discount: {discount:.1f}% off (Save ${savings:.2f})")
    print("🎉 SUCCESS: Found discount!")
elif price:
    print("ℹ️  Found current price but no discount")
else:
    print("❌ Failed to extract any price")