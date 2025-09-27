import requests
import json

# Test the specific Filson product that should show XS, S, 2XL
url = 'https://www.filson.com/products/lined-mackinaw-wool-jac-shirt-acid-green-black-heritage-plaid-x.json'

try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        product = data.get('product', {})
        variants = product.get('variants', [])
        
        print(f'Found {len(variants)} variants:')
        available_sizes = []
        
        for i, variant in enumerate(variants):
            available = variant.get('available', False)
            inventory = variant.get('inventory_quantity', 0)
            option1 = variant.get('option1', '')
            option2 = variant.get('option2', '')
            option3 = variant.get('option3', '')
            print(f'  {i+1}. option1="{option1}" option2="{option2}" option3="{option3}" available={available} inventory={inventory}')
            
            if available and inventory > 0:
                available_sizes.append(option1)
        
        print(f'\nAvailable sizes found: {available_sizes}')
        unique_sizes = sorted(list(set(available_sizes)))
        print(f'Unique available sizes: {unique_sizes}')
        
    else:
        print(f'Failed to fetch JSON: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')