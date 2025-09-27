"""
User Interface

Handles user interaction and display of sale items.
"""

import logging
import re
from typing import List, Dict
from scraper import WebScraper
from database import Database
import webbrowser

class UserInterface:
    """Command-line user interface for the sale tracker."""
    
    def __init__(self):
        """Initialize the user interface."""
        self.logger = logging.getLogger(__name__)
    
    def run(self, database: Database, scraper: WebScraper, config: Dict):
        """Run the simplified auto-scrape application."""
        self.database = database
        self.scraper = scraper
        self.config = config
        
        print("Sale Tracker - Scraping latest deals...")
        print("======================================\n")
        
        # Automatically scrape for new deals
        print("Starting fresh scrape...")
        scraped_items = self.scrape_items_direct()
        
        # Display results immediately without saving to database
        if scraped_items:
            print(f"\nFound {len(scraped_items)} items from scraping!")
            print("\n" + "="*80)
            self.display_scraped_items_directly(scraped_items)
        else:
            print("\nNo items found during scraping.")
    
    
    def scrape_items_direct(self):
        """Scrape items from configured websites and return them directly."""
        websites = self.config.get('targets', {}).get('websites', [])
        
        if not websites:
            print("No websites configured. Please configure websites first.")
            return []
        
        print(f"Scraping {len(websites)} website(s)...")
        
        all_items = self.scraper.scrape_all_websites(websites)
        
        if all_items:
            print(f"Scraped {len(all_items)} items.")
            return all_items
        else:
            print("No items found during scraping.")
            return []
    
    def display_scraped_items_directly(self, scraped_items):
        """Display scraped SaleItem objects directly without database conversion."""
        if not scraped_items:
            return
        
        # Convert SaleItem objects to dict format and filter for discounted items
        discounted_items = []
        for item in scraped_items:
            # Check if item has a discount
            has_discount = False
            discount_percent = 0
            savings_amount = 0
            
            if item.original_price and item.price and item.original_price > item.price:
                has_discount = True
                savings_amount = item.original_price - item.price
                discount_percent = (savings_amount / item.original_price) * 100
            elif item.discount:
                has_discount = True
            
            if has_discount:
                # Convert to dict format for display
                item_dict = {
                    'title': item.title,
                    'price': item.price,
                    'original_price': item.original_price,
                    'discount': item.discount,
                    'url': item.url,
                    'website': item.website,
                    'sizes': item.sizes,
                    'discount_percent': discount_percent,
                    'savings_amount': savings_amount,
                    'scraped_at': item.scraped_at
                }
                discounted_items.append(item_dict)
        
        if discounted_items:
            print(f"Found {len(discounted_items)} discounted items!")
            self.display_discounted_items(discounted_items)
        else:
            print("No discounted items found.")
    
    def display_discounted_items(self, items: List[Dict]):
        """Display discounted items in a formatted table."""
        if not items:
            return
        
        # Sort items by discount percentage (descending) and then by URL for consistent ordering
        sorted_items = sorted(items, key=lambda x: (-x.get('discount_percent', 0), x.get('url', '')))
        
        # Simple deduplication by URL - keep first occurrence (highest discount)
        seen_urls = set()
        enhanced_items = []
        
        for item in sorted_items:
            url = item.get('url', '')
            if not url or url not in seen_urls:
                enhanced_items.append(item)
                if url:
                    seen_urls.add(url)
            
        # Define column widths - expanded product name and sizes columns
        widths = [4, 60, 12, 13, 8, 10, 55, 10]  # #, Product, Sale $, Original $, % Off, Save $, Sizes, Website
        
        headers = ["#", "Product Name", "Sale Price", "Original $", "% Off", "Save $", "Sizes", "Website"]
        
        # Print table header
        self._print_table_separator(widths, "top")
        print(self._format_table_row(headers, widths))
        self._print_table_separator(widths, "middle")
        
        # Print items
        for i, item in enumerate(enhanced_items, 1):
            discount_percent = item.get('discount_percent', 0)
            savings_amount = item.get('savings_amount', 0)
            current_price = float(item['price']) if item['price'] else 0
            original_price = float(item['original_price']) if item['original_price'] else 0
            
            # Just use the item number without emojis
            item_number = str(i)
            
            # Product name without hyperlink attempts - just clean text
            product_name = self._truncate_text(item['title'], 58)
            
            # Format sizes
            sizes = item.get('sizes', '') or 'N/A'
            sizes_display = self._truncate_text(sizes, 53)
            
            # Format row data
            row = [
                item_number,
                product_name,
                f"${current_price:.2f}",
                f"${original_price:.2f}",
                f"{discount_percent:.0f}%",
                f"${savings_amount:.2f}",
                sizes_display,
                self._truncate_text(item['website'], 8)
            ]
            
            print(self._format_table_row(row, widths))
        
        self._print_table_separator(widths, "bottom")
        
        # Show summary
        total_savings = sum(item.get('savings_amount', 0) for item in enhanced_items)
        avg_discount = sum(item.get('discount_percent', 0) for item in enhanced_items) / len(enhanced_items) if enhanced_items else 0
        
        print(f"\\nSummary: {len(enhanced_items)} sale items - Average discount: {avg_discount:.1f}% - Total potential savings: ${total_savings:.2f}")
        
        # Interactive options
        self._show_item_actions(enhanced_items)
    
    def display_items(self, items: List[Dict]):
        """Display a list of items in a formatted table."""
        if not items:
            return
            
        # Define column widths - expanded product name column 
        widths = [4, 50, 12, 12, 8, 13, 16, 16]  # #, Product, Price, Original/Status, Discount, Website, Scraped, Actions
        
        headers = ["#", "Product Name", "Current Price", "Original Price", "Discount", "Website", "Scraped", "Actions"]
        
        # Print table header
        self._print_table_separator(widths, "top")
        print(self._format_table_row(headers, widths))
        self._print_table_separator(widths, "middle")
        
        # Print items
        for i, item in enumerate(items, 1):
            current_price = float(item['price']) if item['price'] else 0
            original_price = float(item['original_price']) if item['original_price'] else 0
            
            # Calculate discount info
            discount_info = "N/A"
            if original_price > current_price and current_price > 0:
                discount_percent = ((original_price - current_price) / original_price) * 100
                discount_info = f"{discount_percent:.0f}% off"
            elif item.get('discount'):
                discount_info = self._truncate_text(item['discount'], 6)
            
            # Fire indicator for discounted items
            indicator = "🔥" if discount_info != "N/A" else ""
            
            # Format row data
            row = [
                f"{indicator}{i}",
                self._truncate_text(item['title'], 48),  # Expanded to fit longer names
                f"${current_price:.2f}" if current_price > 0 else "N/A",
                f"${original_price:.2f}" if original_price > 0 else "N/A",
                discount_info,
                self._truncate_text(item['website'], 11),
                self._format_datetime(item['scraped_at'])[:16],  # Truncate datetime
                "🔗 View | 🛒 Shop"
            ]
            
            print(self._format_table_row(row, widths))
        
        self._print_table_separator(widths, "bottom")
        
        # Interactive options
        self._show_item_actions(items)
    
    def _format_datetime(self, datetime_str: str) -> str:
        """Format datetime string for display."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return datetime_str
    
    def _truncate_text(self, text: str, max_length: int = 40) -> str:
        """Truncate text to fit in table columns."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _format_table_row(self, columns: List[str], widths: List[int]) -> str:
        """Format a table row with proper alignment."""
        row = "│"
        for i, (col, width) in enumerate(zip(columns, widths)):
            # Ensure column content doesn't exceed width
            if len(col) > width:
                col = col[:width-1] + "…"
            
            # Right-align numbers, left-align text  
            if i in [2, 3, 4, 5]:  # Price and percentage columns (Sale Price, Original $, % Off, Save $)
                row += f" {col:>{width}} │"
            else:
                row += f" {col:<{width}} │"
        return row
    
    def _print_table_separator(self, widths: List[int], style: str = "middle"):
        """Print table separator line."""
        if style == "top":
            line = "┌" + "┬".join(["─" * (w + 2) for w in widths]) + "┐"
        elif style == "bottom":
            line = "└" + "┴".join(["─" * (w + 2) for w in widths]) + "┘"
        else:  # middle
            line = "├" + "┼".join(["─" * (w + 2) for w in widths]) + "┤"
        print(line)
    
    def _show_item_actions(self, items: List[Dict]):
        """Show interactive actions for the displayed items."""
        print("\nActions: Enter item number to view details, 'o' + number to open in browser (e.g., 'o1'), or press Enter to return.")
        
        while True:
            try:
                user_input = input("Action: ").strip().lower()
                
                if not user_input:  # Empty input - return to menu
                    break
                
                if user_input.startswith('o'):  # Open in browser
                    try:
                        item_num = int(user_input[1:])
                        if 1 <= item_num <= len(items):
                            item = items[item_num - 1]
                            print(f"Opening {item['title']} in browser...")
                            webbrowser.open(item['url'])
                        else:
                            print(f"Invalid item number. Please enter 1-{len(items)}.")
                    except ValueError:
                        print("Invalid format. Use 'o' followed by item number (e.g., 'o1').")
                
                elif user_input.isdigit():  # Show item details
                    item_num = int(user_input)
                    if 1 <= item_num <= len(items):
                        self._show_item_details(items[item_num - 1])
                    else:
                        print(f"Invalid item number. Please enter 1-{len(items)}.")
                
                else:
                    print("Invalid input. Enter item number, 'o' + number to open in browser, or press Enter to return.")
                    
            except KeyboardInterrupt:
                break
    
    def _group_similar_products(self, items: List[Dict]) -> List[Dict]:
        """Group similar products to reduce duplicates while showing variety."""
        grouped = {}
        seen_base_products = {}
        
        for item in items:
            # Create a key based on title, price, and original price to group exact matches
            exact_key = f"{item['title']}_{item['website']}_{item.get('price', 0)}_{item.get('original_price', 0)}"
            
            # Also track base product names to limit how many of the same product we show
            base_name = self._get_base_product_name(item['title'])
            base_key = f"{base_name}_{item.get('price', 0)}_{item.get('original_price', 0)}"
            
            if exact_key not in grouped:
                grouped[exact_key] = item.copy()
                grouped[exact_key]['count'] = 1
                grouped[exact_key]['urls'] = [item.get('url', '')]
                
                # Track how many variations of this base product we've seen
                if base_key not in seen_base_products:
                    seen_base_products[base_key] = 0
                seen_base_products[base_key] += 1
            else:
                grouped[exact_key]['count'] += 1
                if item.get('url') not in grouped[exact_key]['urls']:
                    grouped[exact_key]['urls'].append(item.get('url', ''))
        
        # Filter to show max 3 variations of each base product to increase variety
        result = []
        base_product_counts = {}
        
        for item in grouped.values():
            base_name = self._get_base_product_name(item['title'])
            base_key = f"{base_name}_{item.get('price', 0)}_{item.get('original_price', 0)}"
            
            if base_key not in base_product_counts:
                base_product_counts[base_key] = 0
            
            # Limit to 3 variations per base product to show more variety
            if base_product_counts[base_key] < 3:
                if item['count'] > 1:
                    item['title'] = f"{item['title']} (x{item['count']})"
                result.append(item)
                base_product_counts[base_key] += 1
        
        return result
    
    def _get_base_product_name(self, title: str) -> str:
        """Extract the base product name without color/variant info."""
        # Remove common variant patterns
        base_title = title
        
        # Remove " - ColorName" patterns
        base_title = re.sub(r' - [A-Za-z\s]+$', '', base_title)
        # Remove " (ColorName)" patterns  
        base_title = re.sub(r' \([A-Za-z\s]+\)$', '', base_title)
        # Remove color words at the end
        color_words = ['Black', 'White', 'Blue', 'Red', 'Green', 'Brown', 'Gray', 'Grey', 'Navy', 'Tan', 'Beige']
        for color in color_words:
            base_title = re.sub(f' {color}$', '', base_title, flags=re.IGNORECASE)
        
        return base_title.strip()
    
    def _extract_variant_from_title(self, title: str) -> str:
        """Extract variant information from title."""
        # Look for " - VariantName" pattern
        match = re.search(r' - (.+)$', title)
        if match:
            return match.group(1)
        
        # Look for color words at the end
        color_words = ['Black', 'White', 'Blue', 'Red', 'Green', 'Brown', 'Gray', 'Grey', 'Navy', 'Tan', 'Beige']
        for color in color_words:
            if title.lower().endswith(f' {color.lower()}'):
                return color
        
        return ''
    
    def _terminal_supports_hyperlinks(self) -> bool:
        """Check if the terminal supports clickable hyperlinks."""
        import os
        
        # Check common terminal indicators
        terminal_program = os.environ.get('TERM_PROGRAM', '').lower()
        term = os.environ.get('TERM', '').lower()
        
        # Terminals that support hyperlinks
        supported_terminals = [
            'iterm.app',      # iTerm2
            'vscode',         # VS Code terminal  
            'hyper',          # Hyper terminal
            'wezterm',        # WezTerm
            'alacritty',      # Alacritty (recent versions)
        ]
        
        # Windows Terminal supports it
        if 'wt.exe' in os.environ.get('WT_SESSION', ''):
            return True
            
        # Check for known supporting terminals
        if any(term_name in terminal_program for term_name in supported_terminals):
            return True
            
        # Modern xterm-256color often supports it
        if 'xterm-256color' in term:
            return True
            
        # Default to False for safety (will use action-based approach)
        return ''
    
    def _deduplicate_by_url_and_combine_variants(self, items: List[Dict]) -> List[Dict]:
        """Only remove TRUE duplicates (exact same URL), keep all unique product pages."""
        seen_urls = {}
        unique_items = []
        
        for item in items:
            url = item.get('url', '')
            if not url:
                # Keep items without URLs
                unique_items.append(item)
                continue
                
            if url not in seen_urls:
                # First time seeing this URL - keep the item
                seen_urls[url] = True
                unique_items.append(item)
            # Skip true duplicates (same exact URL)
        
        return unique_items
    
    def _enhance_individual_product_names(self, items: List[Dict]) -> List[Dict]:
        """Enhance individual product names with color and size info without grouping."""
        enhanced_items = []
        
        for item in items:
            enhanced_item = item.copy()
            title = item['title']
            
            # Extract additional info from URL if available
            size = self._extract_size_from_url_or_title(title, item.get('url', ''))
            
            # If we found size info that's not already in the title, add it
            if size and size.upper() not in title.upper():
                enhanced_item['title'] = f"{title} ({size})"
            
            enhanced_items.append(enhanced_item)
        
        return enhanced_items
    
    def _extract_color_from_title(self, title: str) -> str:
        """Extract color information from product title."""
        # Look for " - Color" pattern
        color_match = re.search(r' - ([A-Za-z\s]+)$', title)
        if color_match:
            color = color_match.group(1).strip()
            # Filter out non-color words
            non_color_words = ['Wildlife', 'Plaid', 'Multi', 'Camo', 'Heather', 'Deco']
            if not any(word in color for word in non_color_words):
                return color
        
        # Look for common color words
        color_words = ['Black', 'White', 'Blue', 'Red', 'Green', 'Brown', 'Gray', 'Grey', 'Navy', 'Tan', 'Beige', 'Gold', 'Silver']
        title_words = title.split()
        for word in reversed(title_words):  # Check from end of title
            for color in color_words:
                if color.lower() in word.lower():
                    return color
        
        return ''
    
    def _extract_size_from_url_or_title(self, title: str, url: str) -> str:
        """Extract size information from title or URL."""
        # Look for size in URL parameters or path
        if url:
            size_patterns = [
                r'[?&]size=([^&]+)',
                r'/size-([^/]+)',
                r'-([XSMLXL]+)(?:-|$)',
                r'-(\d+)(?:-|$)'
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    size = match.group(1).replace('%20', ' ').replace('-', ' ').upper()
                    if len(size) <= 10:  # Reasonable size length
                        return size
        
        # Look for size in title
        size_patterns = [
            r'\b(XS|S|M|L|XL|XXL|XXXL)\b',
            r'\b(\d{1,2})"\b',  # For waist sizes like 32"
            r'\b(\d{1,2}W)\b',   # For waist sizes like 32W
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return ''
    
    def _show_item_details(self, item: Dict):
        """Show detailed information about a single item."""
        print("\\n" + "="*60)
        print(f"📰 PRODUCT DETAILS")
        print("="*60)
        print(f"🏷️  Name: {item['title']}")
        print(f"🌐 Website: {item['website']}")
        
        # Price information
        if item['price']:
            current_price = float(item['price'])
            print(f"💰 Current Price: ${current_price:.2f}")
            
            if item['original_price'] and item['original_price'] != item['price']:
                original_price = float(item['original_price'])
                savings = original_price - current_price
                discount_percent = (savings / original_price) * 100
                print(f"💸 Original Price: ${original_price:.2f}")
                print(f"🔥 Discount: {discount_percent:.1f}% off")
                print(f"💵 You Save: ${savings:.2f}")
        
        if item.get('discount'):
            print(f"🏷️  Store Badge: {item['discount']}")
        
        if item.get('sizes'):
            print(f"📏 Available Sizes: {item['sizes']}")
        
        print(f"🔗 Product URL: {item['url']}")
        print(f"📅 Last Scraped: {self._format_datetime(item['scraped_at'])}")
        
        print("="*60)
        
        # Actions
        while True:
            action = input("\\n🛠️  Actions: (o)pen in browser, (c)opy URL, or (b)ack: ").strip().lower()
            
            if action == 'o':
                print(f"Opening {item['title']} in browser...")
                webbrowser.open(item['url'])
                break
            elif action == 'c':
                try:
                    import pyperclip
                    pyperclip.copy(item['url'])
                    print("✓ URL copied to clipboard!")
                except ImportError:
                    print(f"URL: {item['url']} (copy manually - pyperclip not available)")
                break
            elif action == 'b' or action == '':
                break
            else:
                print("Invalid choice. Enter 'o' to open, 'c' to copy URL, or 'b' to go back.")
    
    def show_error(self, message: str):
        """Display an error message."""
        print(f"\\nError: {message}")
    
    def show_success(self, message: str):
        """Display a success message."""
        print(f"\\nSuccess: {message}")