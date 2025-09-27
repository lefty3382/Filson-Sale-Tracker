import requests
import json
from bs4 import BeautifulSoup
import logging

# Set up logging to see details
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# Test the specific Filson product
product_url = 'https://www.filson.com/products/lined-mackinaw-wool-jac-shirt-acid-green-black-heritage-plaid-x'
json_url = product_url + '.json'

print("=== DETAILED ANALYSIS OF PRODUCT AVAILABILITY ===")

# 1. Check JSON data more carefully
print("\n1. JSON VARIANT ANALYSIS:")
try:
    response = requests.get(json_url)
    if response.status_code == 200:
        data = response.json()
        product = data.get('product', {})
        variants = product.get('variants', [])
        
        print(f"Found {len(variants)} variants in JSON:")
        available_count = 0
        for i, variant in enumerate(variants):
            available = variant.get('available', False)
            inventory = variant.get('inventory_quantity')
            inventory_policy = variant.get('inventory_policy', 'deny')
            inventory_management = variant.get('inventory_management')
            option1 = variant.get('option1', '')
            option2 = variant.get('option2', '')  # Size
            
            print(f"  Variant {i+1}:")
            print(f"    Size (option2): '{option2}'")
            print(f"    Available: {available}")
            print(f"    Inventory Quantity: {inventory}")
            print(f"    Inventory Policy: {inventory_policy}")
            print(f"    Inventory Management: {inventory_management}")
            
            # Check different availability criteria
            if available:
                available_count += 1
                print(f"    *** MARKED AS AVAILABLE ***")
            
            # Sometimes inventory_policy='continue' means available even with 0 stock
            if inventory_policy == 'continue':
                print(f"    *** ALLOWS BACKORDER ***")
                
        print(f"\nTotal variants marked as available: {available_count}")
    else:
        print(f"Failed to fetch JSON: {response.status_code}")
except Exception as e:
    print(f"JSON Error: {e}")

# 2. Check HTML form data more carefully
print("\n2. HTML FORM ANALYSIS:")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(product_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the product form
        product_form = soup.find('form', {'action': '/cart/add'}) or soup.find('form', class_=lambda x: x and 'product' in x)
        if product_form:
            print("Found product form")
            
            # Look for size-related inputs
            size_inputs = product_form.find_all(['select', 'input'], attrs={'name': lambda x: x and 'size' in x.lower()})
            if not size_inputs:
                # Try broader search
                size_inputs = product_form.find_all(['select', 'input'])
                
            for input_elem in size_inputs:
                name = input_elem.get('name', '')
                print(f"\nFound input/select: name='{name}'")
                
                if input_elem.name == 'select':
                    options = input_elem.find_all('option')
                    print(f"  Has {len(options)} options:")
                    for opt in options:
                        text = opt.get_text(strip=True)
                        value = opt.get('value', '')
                        disabled = opt.get('disabled', False)
                        selected = opt.get('selected', False)
                        
                        print(f"    - text='{text}' value='{value}' disabled={disabled} selected={selected}")
                        
        # Also look for JavaScript/JSON data in script tags
        print("\n3. SCRIPT TAG ANALYSIS:")
        scripts = soup.find_all('script')
        for i, script in enumerate(scripts):
            if script.string and ('variants' in script.string or 'available' in script.string):
                content = script.string.strip()
                if len(content) > 100:  # Only show substantial scripts
                    print(f"\nScript {i+1} (first 300 chars):")
                    print(content[:300] + "...")
                    
                    # Try to parse as JSON if it looks like it
                    if content.startswith('{') or 'var ' in content or 'window.' in content:
                        # Look for variant data
                        if 'XS' in content and 'available' in content:
                            print("  *** Contains size and availability data ***")
                
    else:
        print(f"Failed to fetch HTML: {response.status_code}")
except Exception as e:
    print(f"HTML Error: {e}")

print("\n=== EXPECTED RESULT ===")
print("According to the screenshot, only XS, S, and 2XL should be available.")
print("All other sizes should be filtered out as unavailable.")