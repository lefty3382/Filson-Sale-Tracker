#!/usr/bin/env python3
"""
Test limited scrape to verify original price extraction
"""

import sys
import os
sys.path.append('src')

from scraper import WebScraper
import logging

# Set up logging to see debug info but not too verbose  
logging.basicConfig(level=logging.INFO)

# Create a test config
test_config = {
    'user_agent': 'Sale-Tracker-Test/1.0',
    'request_delay': 1000,
    'timeout': 30000,
    'max_retries': 2
}

# Website config for Filson (using working outlet URL)
website_config = {
    'name': 'Filson',
    'base_url': 'https://www.filson.com',
    'url': 'https://www.filson.com/collections/outlet',
    'selectors': {
        'item_container': '.card, .product-card, .grid__item, .card-wrapper, product-card, .collection-product-card',
        'title': '.card__heading, .card__information h3, .product-title, .card-title, .product-card-title',
        'price': '.price .money, .price__regular .money, .card__price .money, .price-item--regular, .price-current',
        'original_price': '.price__sale .money, .compare-at-price .money, .was-price, .price-item--sale',
        'discount': '.badge, .sale-badge, .price__badges, .card__badge',
        'url': 'a',
        'image': 'img'
    }
}

scraper = WebScraper(test_config)

print(f"Testing limited scrape from Filson sale page...")

# Get first 5 items only by patching the limit
original_parse_items = scraper._parse_items

def limited_parse_items(html_content, website_config):
    # Call original method but limit results
    items = original_parse_items(html_content, website_config)
    return items[:5]  # Only first 5 items

# Temporarily replace the method
scraper._parse_items = limited_parse_items

# Scrape 
items = scraper.scrape_website(website_config)

print(f"\nFound {len(items)} items:")
print("="*80)

for i, item in enumerate(items, 1):
    print(f"{i}. {item.title}")
    print(f"   Price: ${item.price}" if item.price else "   Price: Not found")
    print(f"   Original Price: ${item.original_price}" if item.original_price else "   Original Price: None")
    print(f"   Discount: {item.discount}" if item.discount else "   Discount: None")
    
    if item.price and item.original_price and item.original_price > item.price:
        discount = ((item.original_price - item.price) / item.original_price) * 100
        savings = item.original_price - item.price
        print(f"   🔥 CALCULATED DISCOUNT: {discount:.1f}% off (Save ${savings:.2f})")
    
    print(f"   URL: {item.url}")
    print("   " + "-"*75)

# Count items with original prices
items_with_original_price = sum(1 for item in items if item.original_price)
print(f"\nSUMMARY: {items_with_original_price} out of {len(items)} items have original price data")

if items_with_original_price > 0:
    print("✅ SUCCESS: Original price extraction is working!")
else:
    print("❌ ISSUE: No original prices found")