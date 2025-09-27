import requests
import json
from bs4 import BeautifulSoup

# Test the specific Filson product for actual cart availability
product_url = 'https://www.filson.com/products/lined-mackinaw-wool-jac-shirt-acid-green-black-heritage-plaid-x'
json_url = product_url + '.json'

print("=== CHECKING CART AVAILABILITY ===")
try:
    # Get the HTML to see what sizes are actually selectable
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(product_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the add to cart form and size options
        cart_form = soup.find('form', {'action': '/cart/add'})
        if cart_form:
            print("Found add-to-cart form")
            
            # Look for size selector
            size_select = cart_form.find('select', attrs={'name': lambda x: x and 'size' in x.lower()}) or cart_form.find('select')
            if size_select:
                print("Found size selector:")
                options = size_select.find_all('option')
                available_options = []
                
                for option in options:
                    text = option.get_text(strip=True)
                    value = option.get('value', '')
                    disabled = option.get('disabled', False)
                    
                    print(f"  - text='{text}' value='{value}' disabled={disabled}")
                    
                    # Skip the default "Select a size" option
                    if text and text.lower() not in ['select a size', 'select size', ''] and not disabled:
                        available_options.append(text)
                
                print(f"\nActually selectable sizes: {available_options}")
                print(f"Number of selectable sizes: {len(available_options)}")
            else:
                print("No size selector found in form")
        else:
            print("No add-to-cart form found")
    else:
        print(f"Failed to fetch HTML: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n=== COMPARING WITH JSON DATA ===")
try:
    response = requests.get(json_url)
    if response.status_code == 200:
        data = response.json()
        product = data.get('product', {})
        variants = product.get('variants', [])
        
        print(f"JSON shows {len(variants)} total variants:")
        available_json = []
        for variant in variants:
            available = variant.get('available', False)
            inventory = variant.get('inventory_quantity')
            option2 = variant.get('option2', '')  # Size is in option2 for this product
            
            if available:  # Even if inventory is None or 0, check if marked as available
                available_json.append(option2)
                print(f"  - {option2}: available={available}, inventory={inventory}")
        
        print(f"\nJSON available sizes: {available_json}")
        print(f"Number from JSON: {len(available_json)}")
    else:
        print(f"Failed to fetch JSON: {response.status_code}")
        
except Exception as e:
    print(f"JSON Error: {e}")