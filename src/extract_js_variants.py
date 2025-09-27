import requests
import json
import re
from bs4 import BeautifulSoup

# Test the specific Filson product
product_url = 'https://www.filson.com/products/lined-mackinaw-wool-jac-shirt-acid-green-black-heritage-plaid-x'

print("=== EXTRACTING JAVASCRIPT VARIANT DATA ===")

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(product_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for script tags containing variant data
        scripts = soup.find_all('script')
        
        variant_data_found = []
        
        for i, script in enumerate(scripts):
            if script.string:
                content = script.string.strip()
                
                # Look for JSON objects that contain variant information
                # Pattern 1: {"id":46073796165784,"title":"...","available":true/false,...}
                variant_pattern = r'\{"id":\d+,"title":"[^"]*","option1":"[^"]*","option2":"([^"]+)"[^}]*"available":(true|false)[^}]*\}'
                matches = re.findall(variant_pattern, content)
                
                if matches:
                    print(f"\nScript {i+1} contains variant data:")
                    for size, available in matches:
                        available_bool = available == 'true'
                        print(f"  Size: {size} -> Available: {available_bool}")
                        
                        if available_bool:
                            variant_data_found.append(size)
                
                # Pattern 2: Look for arrays of variants
                if '"variants":' in content:
                    # Try to extract the variants array
                    try:
                        # Find JSON objects containing variants
                        json_pattern = r'\{[^{}]*"variants":\[[^\]]*\][^{}]*\}'
                        json_matches = re.findall(json_pattern, content)
                        
                        for json_str in json_matches[:3]:  # Limit to first 3 matches
                            try:
                                data = json.loads(json_str)
                                if 'variants' in data:
                                    variants = data['variants']
                                    print(f"\nFound variants array with {len(variants)} items:")
                                    for variant in variants:
                                        if isinstance(variant, dict):
                                            size = variant.get('option2', '')
                                            available = variant.get('available', False)
                                            print(f"  Size: {size} -> Available: {available}")
                                            if available and size:
                                                variant_data_found.append(size)
                            except json.JSONDecodeError:
                                continue
                    except Exception as e:
                        pass
                
                # Pattern 3: Look for individual variant objects
                if '"available":true' in content and '"option2"' in content:
                    # Extract individual variant JSON objects
                    individual_variant_pattern = r'\{[^{}]*"option2":"([^"]+)"[^{}]*"available":true[^{}]*\}'
                    individual_matches = re.findall(individual_variant_pattern, content)
                    
                    if individual_matches:
                        print(f"\nScript {i+1} individual available variants:")
                        for size in individual_matches:
                            print(f"  Available size: {size}")
                            variant_data_found.append(size)
        
        # Remove duplicates and sort
        available_sizes = sorted(list(set(variant_data_found)))
        
        print(f"\n=== FINAL RESULT ===")
        print(f"Available sizes found in JavaScript: {available_sizes}")
        print(f"Total available sizes: {len(available_sizes)}")
        
        # Compare with expected
        expected_sizes = ['XS', 'S', '2XL']
        print(f"\nExpected sizes (from screenshot): {expected_sizes}")
        
        if set(available_sizes) == set(expected_sizes):
            print("✅ PERFECT MATCH! Found sizes match expected sizes.")
        else:
            print("❌ MISMATCH:")
            print(f"  Found but not expected: {set(available_sizes) - set(expected_sizes)}")
            print(f"  Expected but not found: {set(expected_sizes) - set(available_sizes)}")
    
    else:
        print(f"Failed to fetch HTML: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")