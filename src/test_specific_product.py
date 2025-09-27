import logging
from scraper import WebScraper

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Create a minimal config
config = {'user_agent': 'Mozilla/5.0'}
scraper = WebScraper(config)

# Test the specific product
product_url = 'https://www.filson.com/products/lined-mackinaw-wool-jac-shirt-acid-green-black-heritage-plaid-x'
print(f"Testing size extraction for: {product_url}")

sizes = scraper._fetch_product_sizes(product_url)
print(f"Extracted sizes: {sizes}")
print(f"Number of sizes: {len(sizes)}")