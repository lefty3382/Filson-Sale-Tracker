"""
Web Scraper

Handles scraping sale items from target websites.
"""

import time
import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
import re

@dataclass
class SaleItem:
    """Represents a sale item."""
    title: str
    price: float
    original_price: Optional[float]
    discount: Optional[str]
    url: str
    image_url: Optional[str]
    website: str
    scraped_at: str
    sizes: Optional[str] = None

class WebScraper:
    """Web scraper for sale items."""
    
    def __init__(self, config):
        """Initialize the web scraper."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent', 'Sale-Tracker/1.0')
        })
    
    def scrape_website(self, website_config: Dict) -> List[SaleItem]:
        """Scrape sale items from a website."""
        self.logger.info(f"Scraping {website_config['name']}")
        
        items = []
        
        try:
            # Add delay between requests
            time.sleep(self.config.get('request_delay', 1000) / 1000)
            
            response = self._make_request(website_config['url'])
            
            if response and response.status_code == 200:
                all_items = self._parse_items(response.text, website_config)
                
                # Apply size filtering if enabled
                if self.config.get('user_preferences', {}).get('size_filtering_enabled', False):
                    items = self._filter_items_by_size(all_items)
                    self.logger.info(f"Found {len(all_items)} items, {len(items)} match size preferences from {website_config['name']}")
                else:
                    items = all_items
                    self.logger.info(f"Found {len(items)} items from {website_config['name']}")
            else:
                self.logger.warning(f"Failed to fetch data from {website_config['name']}")
        
        except Exception as e:
            self.logger.error(f"Error scraping {website_config['name']}: {e}")
        
        return items
    
    def scrape_all_websites(self, website_configs: List[Dict]) -> List[SaleItem]:
        """Scrape all configured websites."""
        all_items = []
        
        for website_config in website_configs:
            items = self.scrape_website(website_config)
            all_items.extend(items)
        
        return all_items
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with retries."""
        max_retries = self.config.get('max_retries', 3)
        timeout = self.config.get('timeout', 30000) / 1000
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=timeout)
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _parse_items(self, html_content: str, website_config: Dict) -> List[SaleItem]:
        """Parse sale items from HTML content using BeautifulSoup."""
        self.logger.debug(f"Parsing items from {website_config['name']}")
        
        items = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            selectors = website_config.get('selectors', {})
            
            # Find all item containers
            item_containers = soup.select(selectors.get('item_container', '.product-item'))
            self.logger.info(f"Found {len(item_containers)} product containers")
            
            for container in item_containers[:50]:  # Limit to first 50 items
                try:
                    item = self._extract_item_data(container, website_config, selectors, html_content)
                    if item and self.validate_item(item):
                        items.append(item)
                except Exception as e:
                    self.logger.warning(f"Error parsing item container: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing HTML from {website_config['name']}: {e}")
        
        return items
    
    def _extract_item_data(self, container, website_config: Dict, selectors: Dict, html_content: str = None) -> Optional[SaleItem]:
        """Extract item data from a product container."""
        try:
            # Extract title - try multiple selectors
            title = None
            title_selectors = selectors.get('title', '.product-title').split(', ')
            for selector in title_selectors:
                title_elem = container.select_one(selector.strip())
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title:
                        break
            
            # If still no title, try common fallbacks
            if not title:
                for fallback in ['h3', 'h2', '.card-title', '[data-testid="product-title"]', 'a']:
                    title_elem = container.select_one(fallback)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title and len(title) > 5:  # Avoid very short titles
                            break
            
            if not title:
                self.logger.debug(f"No title found in container: {container.get('class', 'no-class')}")
                return None
            
            # Extract color/variant information to make titles more specific
            title = self._enhance_title_with_variant(title, container)
            
            # Extract URL
            url_elem = container.select_one(selectors.get('url', 'a'))
            url = url_elem.get('href') if url_elem else None
            if url and not url.startswith('http'):
                url = website_config['base_url'] + url
            
            # Extract price - try multiple selectors
            price = None
            price_selectors = selectors.get('price', '.price').split(', ')
            for selector in price_selectors:
                price_elem = container.select_one(selector.strip())
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    if price is not None:
                        break
            
            # Fallback price selectors
            if price is None:
                for fallback in ['.money', '[data-price]', '.price-current', '.current-price']:
                    price_elem = container.select_one(fallback)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        price = self._extract_price(price_text)
                        if price is not None:
                            break
            
            # If no price found via selectors, try JavaScript extraction for this product
            original_price = None
            if price is None and html_content and title:
                js_price, js_original_price = self._extract_prices_from_js(html_content, title)
                if js_price:
                    price = js_price
                    original_price = js_original_price
            
            # Extract original price if not set from JS extraction
            if original_price is None:
                original_price_elem = container.select_one(selectors.get('original_price', '.original-price'))
                if original_price_elem:
                    original_price = self._extract_price(original_price_elem.get_text(strip=True))
            
            # If we have a URL, try fetching from individual product page for better price data
            if url and (price is None or original_price is None):
                self.logger.debug(f"Fetching individual product price for: {title[:30]}... (current: price=${price}, original=${original_price})")
                fetched_price, fetched_original = self._fetch_product_price(url)
                self.logger.debug(f"Fetched from product page: price=${fetched_price}, original=${fetched_original}")
                if fetched_price and fetched_original:
                    # If we got both prices from individual page, use them (they're more reliable)
                    price = fetched_price
                    original_price = fetched_original
                    self.logger.debug(f"Used complete fetched pricing: ${price} (was ${original_price})")
                elif fetched_price and price is None:
                    # Use fetched price if we don't have one
                    price = fetched_price
                    self.logger.debug(f"Set price to fetched: ${price}")
                elif fetched_original and original_price is None:
                    # Use fetched original price if we don't have one
                    original_price = fetched_original
                    self.logger.debug(f"Set original_price to fetched: ${original_price}")
            
            # Debug logging for price extraction
            if price is None:
                self.logger.debug(f"No price found for item: {title[:30]}... in container classes: {container.get('class', 'no-class')}")
            
            
            # Extract discount
            discount_elem = container.select_one(selectors.get('discount', '.discount'))
            discount = discount_elem.get_text(strip=True) if discount_elem else None
            
            # Extract image URL
            image_elem = container.select_one(selectors.get('image', 'img'))
            image_url = image_elem.get('src') or image_elem.get('data-src') if image_elem else None
            if image_url and not image_url.startswith('http'):
                image_url = website_config['base_url'] + image_url
            
            # Extract size information
            sizes = self._extract_size_info(title, url or '')
            size_string = ', '.join(sorted(sizes)) if sizes else None
            
            # If we have a URL but no size info from title/URL, try to get it from the product page
            if url and not size_string:
                page_sizes = self._fetch_product_sizes(url)
                if page_sizes:
                    size_string = ', '.join(sorted(page_sizes))
            
            # Debug final prices before creating SaleItem  
            self.logger.debug(f"Final prices for '{title}': price=${price}, original_price=${original_price}")
            
            return SaleItem(
                title=title,
                price=price,
                original_price=original_price,
                discount=discount,
                url=url,
                image_url=image_url,
                website=website_config['name'],
                scraped_at=datetime.now().isoformat(),
                sizes=size_string
            )
            
        except Exception as e:
            self.logger.warning(f"Error extracting item data: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text."""
        if not price_text:
            return None
        
        # Clean the price text
        cleaned_text = price_text.replace(',', '').replace('$', '').replace('USD', '').strip()
        
        # Try to find price patterns
        price_patterns = [
            r'\b(\d+\.\d{2})\b',  # Standard format: 123.45
            r'\b(\d+)\b',         # Integer format: 123
            r'(\d+\.\d{1})\b',    # One decimal: 123.4
        ]
        
        for pattern in price_patterns:
            price_match = re.search(pattern, cleaned_text)
            if price_match:
                try:
                    price_value = float(price_match.group(1))
                    # Sanity check - prices should be reasonable
                    if 0.01 <= price_value <= 10000:
                        return price_value
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_prices_from_js(self, html_content: str, title: str) -> tuple[Optional[float], Optional[float]]:
        """Extract price information from JavaScript data in HTML."""
        try:
            import json
            
            # For collection pages, look for product data in JavaScript
            # Pattern 1: Search for product data that matches our title
            title_clean = re.escape(title.replace('...', '').strip())
            
            # Look for variants array with matching title
            variant_pattern = rf'{{"price":{{"amount":([\d.]+),"currencyCode":"USD"}},"product":{{"title":"{title_clean}[^"]*"'
            variant_match = re.search(variant_pattern, html_content, re.IGNORECASE)
            if variant_match:
                price = float(variant_match.group(1))
                if price > 0:
                    self.logger.debug(f"Found price ${price} for {title} via variant pattern")
                    return price, None
            
            # Pattern 2: Look for price data in cents (Shopify format)
            # Find product data with title and price
            product_pattern = rf'"price":(\d+)[^}}]*"title":"[^"]*{re.escape(title[:20])}[^"]*"'
            product_match = re.search(product_pattern, html_content, re.IGNORECASE)
            if product_match:
                price_cents = int(product_match.group(1))
                price = price_cents / 100.0
                if price > 0:
                    self.logger.debug(f"Found price ${price} for {title} via product pattern")
                    return price, None
            
            # Pattern 3: Generic price extraction from JavaScript
            # Look for any price near the product title in the HTML
            price_patterns = [
                r'"price":\s*([\d.]+)',
                r'"amount":\s*([\d.]+)',
                r'price["\']?:\s*([\d.]+)'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    try:
                        price = float(matches[0])
                        if 10 <= price <= 2000:  # Reasonable price range
                            self.logger.debug(f"Found generic price ${price} for {title}")
                            return price, None
                    except ValueError:
                        continue
            
        except Exception as e:
            self.logger.debug(f"Error extracting prices from JS for {title}: {e}")
        
        return None, None
    
    def _fetch_product_price(self, product_url: str) -> tuple[Optional[float], Optional[float]]:
        """Fetch price information from individual product page."""
        try:
            if not product_url.startswith('http'):
                return None, None
                
            response = self._make_request(product_url)
            if response and response.status_code == 200:
                html = response.text
                
                # Look for Klaviyo price data (very reliable for Shopify) - multiple patterns
                klaviyo_patterns = [
                    r'"Price":\s*"\$([\d,]+\.\d{2})"[^}]*"CompareAtPrice":\s*"\$([\d,]+\.\d{2})"',
                    r'"CompareAtPrice":\s*"\$([\d,]+\.\d{2})"[^}]*"Price":\s*"\$([\d,]+\.\d{2})"',
                    r'"Value":\s*"([\d,]+\.\d{2})"[^}]*"CompareAtPrice":\s*"\$([\d,]+\.\d{2})"',
                    # New patterns for Filson's specific format
                    r'CompareAtPrice:\s*"\$([\d,]+\.\d{2})"',  # Just CompareAtPrice
                    r'Price:\s*"\$([\d,]+\.\d{2})".*?CompareAtPrice:\s*"\$([\d,]+\.\d{2})"',
                    r'CompareAtPrice:\s*"\$([\d,]+\.\d{2})".*?Price:\s*"\$([\d,]+\.\d{2})"'
                ]
                
                for i, pattern in enumerate(klaviyo_patterns):
                    klaviyo_match = re.search(pattern, html, re.DOTALL)
                    if klaviyo_match:
                        self.logger.debug(f"Matched Klaviyo pattern {i}: {pattern[:50]}...")
                        
                        if i == 3:  # CompareAtPrice only pattern
                            original_price = float(klaviyo_match.group(1).replace(',', ''))
                            # Need to find current price separately
                            price_pattern = r'"price":(\d+)'  # Shopify cents format
                            price_match = re.search(price_pattern, html)
                            if price_match:
                                price = float(price_match.group(1)) / 100.0
                            else:
                                # Try another pattern for current price
                                current_price_pattern = r'Price:\s*"\$([\d,]+\.\d{2})"'
                                current_price_match = re.search(current_price_pattern, html)
                                if current_price_match:
                                    price = float(current_price_match.group(1).replace(',', ''))
                                else:
                                    price = None
                        elif i == 5:  # CompareAtPrice.*Price pattern  
                            original_price = float(klaviyo_match.group(1).replace(',', ''))
                            price = float(klaviyo_match.group(2).replace(',', ''))
                        elif 'CompareAtPrice.*Price' in pattern or i == 1:  # Reverse order patterns
                            original_price = float(klaviyo_match.group(1).replace(',', ''))
                            if len(klaviyo_match.groups()) > 1:
                                price = float(klaviyo_match.group(2).replace(',', ''))
                            else:
                                price = None
                        else:  # Normal order (Price.*CompareAtPrice)
                            price = float(klaviyo_match.group(1).replace(',', ''))
                            if len(klaviyo_match.groups()) > 1:
                                original_price = float(klaviyo_match.group(2).replace(',', ''))
                            else:
                                original_price = None
                        
                        if price and original_price and original_price > price:  # Only return if there's actually a discount
                            discount_percent = ((original_price - price) / original_price) * 100
                            self.logger.info(f"DISCOUNT FOUND: {discount_percent:.1f}% off - ${price} (was ${original_price}) for {product_url}")
                            return price, original_price
                        elif price:
                            self.logger.debug(f"Found Klaviyo regular price: ${price} for {product_url}")
                            return price, original_price  # Return both even if no discount
                
                # Look for JSON-LD product data
                json_ld_pattern = r'<script type="application/ld\+json">\s*({.*?"@type":\s*"Product".*?})\s*</script>'
                json_match = re.search(json_ld_pattern, html, re.DOTALL)
                if json_match:
                    try:
                        import json
                        data = json.loads(json_match.group(1))
                        if 'offers' in data:
                            offers = data['offers']
                            if isinstance(offers, list) and offers:
                                offer = offers[0]
                                price = float(offer.get('price', 0))
                                if price > 0:
                                    self.logger.debug(f"Found JSON-LD price: ${price} for {product_url}")
                                    return price, None
                    except (json.JSONDecodeError, ValueError, KeyError):
                        pass
                
                # Look for simple price patterns in HTML
                price_patterns = [
                    r'<meta property="og:price:amount" content="([\d.]+)"',
                    r'"price":\s*(\d+)',  # Shopify cents format
                    r'class="price[^"]*"[^>]*>\s*\$([\d,]+\.\d{2})',
                ]
                
                for pattern in price_patterns:
                    match = re.search(pattern, html)
                    if match:
                        try:
                            price_str = match.group(1).replace(',', '')
                            if pattern == r'"price":\s*(\d+)':  # Shopify cents
                                price = float(price_str) / 100.0
                            else:
                                price = float(price_str)
                            
                            if price > 0:
                                self.logger.debug(f"Found price via pattern: ${price} for {product_url}")
                                return price, None
                        except (ValueError, IndexError):
                            continue
                            
        except Exception as e:
            self.logger.debug(f"Error fetching product price from {product_url}: {e}")
        
        return None, None
    
    def _fetch_product_sizes(self, product_url: str) -> List[str]:
        """Fetch only truly available/purchasable sizes from product page."""
        if not product_url.startswith('http'):
            return []
            
        self.logger.debug(f"Fetching sizes for: {product_url}")
        
        # First try to extract JavaScript variant data from HTML (most accurate)
        try:
            resp = self._make_request(product_url)
            if resp and resp.status_code == 200:
                from bs4 import BeautifulSoup
                import re
                import json
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                scripts = soup.find_all('script')
                
                available_sizes = []
                
                for script in scripts:
                    if script.string:
                        content = script.string.strip()
                        
                        # Look for individual variant JSON objects with availability data
                        # Pattern: {"id":...,"option2":"SIZE","available":true,...}
                        variant_pattern = r'\{"id":\d+,"title":"[^"]*","option1":"[^"]*","option2":"([^"]+)"[^}]*"available":(true|false)[^}]*\}'
                        matches = re.findall(variant_pattern, content)
                        
                        for size, available_str in matches:
                            if available_str == 'true' and self._is_actual_size(size):
                                available_sizes.append(size)
                                self.logger.debug(f"Found available size from JS: {size}")
                
                if available_sizes:
                    unique_sizes = sorted(list(set(available_sizes)))
                    self.logger.debug(f"Returning {len(unique_sizes)} truly available sizes from JS: {unique_sizes}")
                    return unique_sizes
                
                self.logger.debug("No available sizes found in JavaScript data")
                
        except Exception as e:
            self.logger.debug(f"JavaScript size extraction failed: {e}")
        
        # Fallback: Try Shopify JSON endpoint
        try:
            json_url = product_url.rstrip('/') + '.json'
            resp = self._make_request(json_url)
            if resp and resp.status_code == 200:
                data = resp.json()
                product = data.get('product', {})
                variants = product.get('variants', [])
                
                available_sizes = []
                for variant in variants:
                    # Check availability - some products set inventory_quantity to null but are still available
                    available = variant.get('available', False)
                    inventory_quantity = variant.get('inventory_quantity')
                    
                    # Skip if explicitly not available
                    if not available:
                        continue
                    
                    # Skip if inventory is explicitly 0, but allow null/None inventory
                    if inventory_quantity is not None and inventory_quantity <= 0:
                        continue
                    
                    # Check option1, option2, option3 for size information
                    option1 = variant.get('option1', '').strip()
                    option2 = variant.get('option2', '').strip()
                    option3 = variant.get('option3', '').strip()
                    
                    # Try to find the size in any of the options
                    size_found = None
                    for option in [option1, option2, option3]:
                        if option and self._is_actual_size(option):
                            size_found = option
                            break
                    
                    if size_found:
                        available_sizes.append(size_found)
                        self.logger.debug(f"Found available size from JSON: {size_found} (inventory: {inventory_quantity})")
                
                if available_sizes:
                    unique_sizes = sorted(list(set(available_sizes)))
                    self.logger.debug(f"Returning {len(unique_sizes)} truly available sizes from JSON: {unique_sizes}")
                    return unique_sizes
                else:
                    self.logger.debug("No truly available sizes found in JSON data")
                    
        except Exception as e:
            self.logger.debug(f"JSON size fetch failed: {e}")
        
        return []
    
    def _extract_filson_sizes(self, soup) -> List[str]:
        """Extract available sizes from Filson product pages - DISABLED."""
        # This method is disabled in favor of JSON-based extraction
        # to prevent color contamination and ensure only truly available sizes
        self.logger.debug("Filson size extraction disabled - using JSON method only")
        return []
    
    def _is_valid_size(self, size_text: str) -> bool:
        """Check if a text string represents a valid size."""
        if not size_text or len(size_text) > 20:  # Increased max length
            return False
            
        size_text = size_text.strip().upper()
        
        # Skip obviously invalid values
        invalid_values = ['DEFAULT', 'TITLE', 'NULL', 'UNDEFINED', 'SELECT', 'CHOOSE', 'SIZE']
        if size_text in invalid_values:
            return False
        
        # Check for common size patterns (more permissive)
        size_patterns = [
            r'^(XS|S|M|L|XL|XXL|XXXL|2XL|3XL|4XL)$',   # Standard letter sizes
            r'^(\d{1,2})$',                            # Numeric sizes (shoes, pants)
            r'^(\d{1,2}\.\d)$',                       # Decimal sizes (7.5, 8.5)
            r'^(\d{1,2}W|\d{1,2}L)$',                 # Waist/Length (32W, 34L)
            r'^(SMALL|MEDIUM|LARGE|EXTRA LARGE)$',     # Word sizes
            r'^(\d{1,2}X\d{1,2})$',                   # Dimensions (32X34)
            r'^(\d{1,2}"|")$',                       # Inches
            r'^(ONE SIZE|OS|ONESIZE)$',                # One size fits all
            r'^(\d{1,2}XL|\d{1,2}XXL)$',              # 2XL, 3XL, etc.
            r'^[SMLX]{1,4}$',                          # Simple S, M, L, XL combinations
            r'^SIZE\s+[SMLX]+$',                       # "SIZE M", "SIZE XL"
            r'^[0-9]{1,2}[/\-][0-9]{1,2}$',           # Fraction sizes like "7/8"
            r'^(REGULAR|REG)$',                        # Regular fit
            r'^[0-9]{1,2}[RLTW]$',                     # Size with qualifier (32R, 34T, etc.)
        ]
        
        for pattern in size_patterns:
            if re.match(pattern, size_text):
                return True
        
        # If it's short and alphanumeric, might be a size
        if len(size_text) <= 6 and re.match(r'^[A-Z0-9\-/\.\s]+$', size_text):
            return True
                
        return False
    
    def _is_actual_size(self, text: str) -> bool:
        """Check if text represents an actual clothing size (not color or other variant)."""
        if not text or len(text) > 15:
            return False
            
        text = text.strip().upper()
        
        # Exclude obvious color names
        color_names = [
            'BLACK', 'WHITE', 'BLUE', 'RED', 'GREEN', 'BROWN', 'GRAY', 'GREY', 'NAVY', 'TAN', 'BEIGE',
            'RAVEN', 'RUST', 'GOLD', 'SILVER', 'CREAM', 'OLIVE', 'KHAKI', 'CHARCOAL', 'HEATHER',
            'INDIGO', 'CRIMSON', 'BURGUNDY', 'MAROON', 'PURPLE', 'PINK', 'ORANGE', 'YELLOW',
            'DARK', 'LIGHT', 'BRIGHT', 'MULTI', 'PLAID', 'CAMO', 'WILDLIFE', 'SORREL', 'LARCH',
            'TROUT', 'RIVER', 'SMOKE', 'FALLS', 'ALMOND', 'MAPLE', 'BARK', 'DUST', 'CLAY',
            'FLAG', 'ARMY', 'FIELD', 'STONE', 'SAND', 'DECO', 'FLAME', 'FRONTIER'
        ]
        
        # Check if it's a color name
        if text in color_names:
            return False
        
        # Check if it contains color words
        for color in color_names:
            if color in text:
                return False
        
        # Check for actual size patterns
        size_patterns = [
            r'^(XS|S|M|L|XL|XXL|XXXL|2XL|3XL|4XL)$',         # Standard sizes
            r'^(\d{1,2})$',                                   # Numeric sizes
            r'^(\d{1,2}W|\d{1,2}L)$',                        # Waist/Length
            r'^(\d{1,2}X\d{1,2})$',                          # Dimensions like 32x34
            r'^[SMLX]{1,4}\s*LONG$',                         # Size + Long (e.g., "M LONG")
            r'^(SMALL|MEDIUM|LARGE|EXTRA LARGE)$',           # Word sizes
            r'^(ONE SIZE|OS)$',                              # One size
            r'^\d{1,2}(\.\d)?$',                             # Decimal sizes
        ]
        
        for pattern in size_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _calculate_discount_info(self, current_price: float, original_price: Optional[float]) -> dict:
        """Calculate discount percentage and savings amount."""
        if not original_price or original_price <= current_price:
            return {
                'has_discount': False,
                'discount_percent': 0,
                'savings_amount': 0,
                'is_on_sale': False
            }
        
        savings = original_price - current_price
        discount_percent = (savings / original_price) * 100
        
        return {
            'has_discount': True,
            'discount_percent': round(discount_percent, 1),
            'savings_amount': round(savings, 2),
            'is_on_sale': True
        }
    
    def validate_item(self, item: SaleItem) -> bool:
        """Validate a scraped item."""
        # Must have title and URL
        if not item.title or not item.url:
            return False
        
        # If price exists, it must be positive
        if item.price is not None and item.price < 0:
            return False
        
        # If original_price exists, it must be positive
        if item.original_price is not None and item.original_price < 0:
            return False
        
        # Title should be meaningful (not just whitespace or very short)
        if len(item.title.strip()) < 3:
            return False
        
        return True
    
    def _enhance_title_with_variant(self, title: str, container) -> str:
        """Extract color/variant info and add to title to differentiate similar products."""
        try:
            # Look for color/variant information in various places
            variant_info = []
            
            # Check for color in common selectors
            color_selectors = [
                '.product-form__option-value[data-option-position="1"]',  # Shopify color option
                '.color-swatch.selected',
                '.variant-color',
                '.product-color',
                '[data-color]',
                '.swatch.selected',
            ]
            
            for selector in color_selectors:
                color_elem = container.select_one(selector)
                if color_elem:
                    color_text = color_elem.get_text(strip=True)
                    if color_text and len(color_text) < 20:  # Reasonable color name length
                        variant_info.append(color_text)
                        break
                    # Also try data attributes
                    color_attr = color_elem.get('data-color') or color_elem.get('title')
                    if color_attr and len(color_attr) < 20:
                        variant_info.append(color_attr)
                        break
            
            # Look for size information
            size_selectors = [
                '.product-form__option-value[data-option-position="2"]',  # Shopify size option
                '.variant-size',
                '.product-size',
                '[data-size]'
            ]
            
            for selector in size_selectors:
                size_elem = container.select_one(selector)
                if size_elem:
                    size_text = size_elem.get_text(strip=True)
                    if size_text and len(size_text) < 10:  # Reasonable size length
                        variant_info.append(size_text)
                        break
            
            # Look in URL for additional variant info (like color codes)
            url_elem = container.select_one('a')
            if url_elem:
                href = url_elem.get('href', '')
                # Extract color from URL patterns like "/product-name-color" or "color=blue"
                color_matches = re.findall(r'[-_]([a-z]+(?:-[a-z]+)?)-?(?:\d+|$)', href.lower())
                if color_matches:
                    # Take the last match which is often the color
                    potential_color = color_matches[-1].replace('-', ' ').title()
                    if len(potential_color) < 15 and potential_color not in title.lower():
                        # Only add if it's not already in the title
                        variant_info.append(potential_color)
            
            # Add variant info to title if found
            if variant_info:
                # Clean up variant info
                clean_variants = []
                for variant in variant_info[:2]:  # Max 2 variants to keep title readable
                    variant = variant.strip().title()
                    if variant and variant not in clean_variants:
                        clean_variants.append(variant)
                
                if clean_variants:
                    variant_str = ' - ' + ' '.join(clean_variants)
                    return title + variant_str
            
            return title
            
        except Exception as e:
            self.logger.debug(f"Error enhancing title with variant: {e}")
            return title
    
    def _filter_items_by_size(self, items: List[SaleItem]) -> List[SaleItem]:
        """Filter items based on user size preferences."""
        filtered_items = []
        user_prefs = self.config.get('user_preferences', {})
        preferred_sizes = user_prefs.get('preferred_sizes', {})
        
        for item in items:
            if self._item_matches_size_preference(item, preferred_sizes):
                filtered_items.append(item)
            else:
                self.logger.debug(f"Filtered out {item.title} due to size preference")
        
        return filtered_items
    
    def _item_matches_size_preference(self, item: SaleItem, preferred_sizes: Dict) -> bool:
        """Check if an item matches the user's size preferences."""
        try:
            # Extract size information from title and URL
            size_info = self._extract_size_info(item.title, item.url)
            
            if not size_info:
                # If no size info found, include the item (could be one-size or size selection on product page)
                return True
            
            # Determine item category
            category = self._categorize_item(item.title)
            
            # Get preferred sizes for this category
            category_prefs = preferred_sizes.get(category, ['all'])
            
            # If "all" is in preferences for this category, include the item
            if 'all' in category_prefs:
                return True
            
            # Check if any extracted size matches preferences
            for size in size_info:
                if size.upper() in [pref.upper() for pref in category_prefs]:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking size preference for {item.title}: {e}")
            return True  # Include item if error occurs
    
    def _extract_size_info(self, title: str, url: str) -> List[str]:
        """Extract size information from title and URL."""
        sizes = []
        
        # Common size patterns
        size_patterns = [
            r'\b(XS|S|M|L|XL|XXL|XXXL)\b',  # Standard letter sizes
            r'\b(\d+)(?:"|\s*inch)?\b',  # Numeric sizes (pants, shoes)
            r'\b(Small|Medium|Large|Extra Large)\b',  # Word sizes
            r'\b(\d+\.\d+|\d+)\s*(?:W|L)\b',  # Waist/Length measurements
        ]
        
        text_to_search = f"{title} {url}"
        
        for pattern in size_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                size = match.strip()
                if size and len(size) <= 10:  # Reasonable size length
                    sizes.append(size)
        
        # Clean up and deduplicate
        unique_sizes = list(set(sizes))
        
        return unique_sizes
    
    def _categorize_item(self, title: str) -> str:
        """Categorize an item based on its title to determine size category."""
        title_lower = title.lower()
        
        # Bottoms/Pants category - include all sizes for pants
        pants_keywords = ['jeans', 'pants', 'trousers', 'chinos', 'shorts', 'trunks']
        if any(keyword in title_lower for keyword in pants_keywords):
            return 'bottoms'
        
        # Outerwear category
        outerwear_keywords = ['jacket', 'coat', 'vest', 'blazer', 'parka', 'anorak', 'cruiser']
        if any(keyword in title_lower for keyword in outerwear_keywords):
            return 'outerwear'
        
        # Footwear category
        footwear_keywords = ['shoe', 'boot', 'sneaker', 'sandal', 'loafer']
        if any(keyword in title_lower for keyword in footwear_keywords):
            return 'footwear'
        
        # Accessories category
        accessory_keywords = ['hat', 'cap', 'belt', 'bag', 'backpack', 'wallet', 'glove', 'scarf']
        if any(keyword in title_lower for keyword in accessory_keywords):
            return 'accessories'
        
        # Default to tops for shirts, tees, etc.
        return 'tops'
