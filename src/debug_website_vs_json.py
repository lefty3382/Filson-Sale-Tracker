import requests
import json
from bs4 import BeautifulSoup

# Test the specific Filson product
product_url = 'https://www.filson.com/products/lined-mackinaw-wool-jac-shirt-acid-green-black-heritage-plaid-x'
json_url = product_url + '.json'

print("=== JSON DATA ===")
try:
    response = requests.get(json_url)
    if response.status_code == 200:
        data = response.json()
        product = data.get('product', {})
        variants = product.get('variants', [])
        
        print(f'Found {len(variants)} variants in JSON:')
        for i, variant in enumerate(variants):
            available = variant.get('available', False)
            inventory = variant.get('inventory_quantity')
            option1 = variant.get('option1', '')
            option2 = variant.get('option2', '')
            option3 = variant.get('option3', '')
            print(f'  {i+1}. option1="{option1}" option2="{option2}" option3="{option3}" available={available} inventory={inventory}')
    else:
        print(f'Failed to fetch JSON: {response.status_code}')
except Exception as e:
    print(f'JSON Error: {e}')

print("\n=== HTML DATA ===")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(product_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for size selectors in various common patterns
        size_selectors = [
            'select[name*="size"] option',
            'input[name*="size"]',
            '.size-option',
            '.variant-option',
            '[data-variant-title]',
            'select option[value*="Size"]',
            '.product-form__input option',
        ]
        
        for selector in size_selectors:
            elements = soup.select(selector)
            if elements:
                print(f'Found {len(elements)} elements with selector: {selector}')
                for elem in elements[:10]:  # Show first 10
                    text = elem.get_text(strip=True)
                    value = elem.get('value', '')
                    title = elem.get('title', '')
                    print(f'  - text="{text}" value="{value}" title="{title}"')
                print()
        
        # Look for JSON-LD or script data
        scripts = soup.find_all('script', type='application/json')
        for i, script in enumerate(scripts):
            if 'variants' in script.text or 'options' in script.text:
                print(f'Found JSON script {i+1}:')
                try:
                    data = json.loads(script.text)
                    print(f'  Keys: {list(data.keys()) if isinstance(data, dict) else "Not a dict"}')
                except:
                    print(f'  Could not parse as JSON')
                    print(f'  First 200 chars: {script.text[:200]}')
                print()
                
    else:
        print(f'Failed to fetch HTML: {response.status_code}')
except Exception as e:
    print(f'HTML Error: {e}')