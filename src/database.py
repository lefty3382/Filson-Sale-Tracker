"""
Database

Handles data storage and retrieval for sale items.
"""

import sqlite3
import logging
from typing import List, Optional
from datetime import datetime
from scraper import SaleItem

class Database:
    """Database manager for sale items."""
    
    def __init__(self, config):
        """Initialize the database."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_path = config.get('filename', 'sale_tracker.db')
        self.connection = None
    
    def initialize(self):
        """Initialize the database and create tables."""
        self.logger.info(f"Initializing database: {self.db_path}")
        
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        self._create_tables()
        self.logger.info("Database initialized successfully")
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.connection.cursor()
        
        # Create sale_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL,
                original_price REAL,
                discount TEXT,
                url TEXT NOT NULL,
                image_url TEXT,
                website TEXT NOT NULL,
                sizes TEXT,
                scraped_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(url, scraped_at)
            )
        ''')
        
        # Create price_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_url TEXT NOT NULL,
                price REAL NOT NULL,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (item_url) REFERENCES sale_items (url)
            )
        ''')
        
        # Create websites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS websites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                base_url TEXT NOT NULL,
                last_scraped TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Add sizes column if it doesn't exist (migration)
        try:
            cursor.execute('ALTER TABLE sale_items ADD COLUMN sizes TEXT')
        except sqlite3.OperationalError:
            # Column already exists
            pass
            
        self.connection.commit()
    
    def save_items(self, items: List[SaleItem]) -> int:
        """Save sale items to database."""
        if not items:
            return 0
        
        cursor = self.connection.cursor()
        saved_count = 0
        
        for item in items:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO sale_items 
                    (title, price, original_price, discount, url, image_url, 
                     website, sizes, scraped_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.title,
                    item.price,
                    item.original_price,
                    item.discount,
                    item.url,
                    item.image_url,
                    item.website,
                    item.sizes,
                    item.scraped_at,
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                    # Also save price history
                    self._save_price_history(item.url, item.price)
            
            except sqlite3.Error as e:
                self.logger.error(f"Error saving item {item.title}: {e}")
        
        self.connection.commit()
        self.logger.info(f"Saved {saved_count} new items to database")
        return saved_count
    
    def _save_price_history(self, url: str, price: float):
        """Save price history for an item."""
        if price is None:
            return
        
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO price_history (item_url, price, recorded_at)
            VALUES (?, ?, ?)
        ''', (url, price, datetime.now().isoformat()))
    
    def get_items(self, website: Optional[str] = None, limit: int = 100) -> List[dict]:
        """Get sale items from database."""
        cursor = self.connection.cursor()
        
        if website:
            cursor.execute('''
                SELECT * FROM sale_items 
                WHERE website = ? 
                ORDER BY scraped_at DESC 
                LIMIT ?
            ''', (website, limit))
        else:
            cursor.execute('''
                SELECT * FROM sale_items 
                ORDER BY scraped_at DESC 
                LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_price_history(self, url: str) -> List[dict]:
        """Get price history for an item."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT price, recorded_at FROM price_history 
            WHERE item_url = ? 
            ORDER BY recorded_at ASC
        ''', (url,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_items(self, query: str, limit: int = 50) -> List[dict]:
        """Search items by title."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM sale_items 
            WHERE title LIKE ? 
            ORDER BY scraped_at DESC 
            LIMIT ?
        ''', (f'%{query}%', limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> dict:
        """Get database statistics."""
        cursor = self.connection.cursor()
        
        # Total items
        cursor.execute('SELECT COUNT(*) as count FROM sale_items')
        total_items = cursor.fetchone()['count']
        
        # Items by website
        cursor.execute('''
            SELECT website, COUNT(*) as count 
            FROM sale_items 
            GROUP BY website
        ''')
        items_by_website = {row['website']: row['count'] for row in cursor.fetchall()}
        
        # Latest scrape time
        cursor.execute('SELECT MAX(scraped_at) as latest FROM sale_items')
        latest_scrape = cursor.fetchone()['latest']
        
        return {
            'total_items': total_items,
            'items_by_website': items_by_website,
            'latest_scrape': latest_scrape
        }
    
    def get_price_statistics(self) -> dict:
        """Get price-related statistics."""
        cursor = self.connection.cursor()
        
        # Items with prices
        cursor.execute('SELECT COUNT(*) as count FROM sale_items WHERE price IS NOT NULL')
        items_with_prices = cursor.fetchone()['count']
        
        if items_with_prices == 0:
            return {
                'items_with_prices': 0,
                'items_with_discounts': 0
            }
        
        # Price statistics
        cursor.execute('''
            SELECT 
                AVG(price) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM sale_items 
            WHERE price IS NOT NULL
        ''')
        price_stats = cursor.fetchone()
        
        # Items with discounts
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM sale_items 
            WHERE (original_price IS NOT NULL AND original_price != price) 
               OR discount IS NOT NULL
        ''')
        items_with_discounts = cursor.fetchone()['count']
        
        return {
            'items_with_prices': items_with_prices,
            'avg_price': price_stats['avg_price'] or 0,
            'min_price': price_stats['min_price'] or 0,
            'max_price': price_stats['max_price'] or 0,
            'items_with_discounts': items_with_discounts
        }
    
    def get_discounted_items(self, limit: int = 100) -> List[dict]:
        """Get items that have discounts, sorted by discount percentage."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT *, 
                   CASE 
                       WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
                       THEN ROUND(((original_price - price) / original_price) * 100, 1)
                       ELSE 0
                   END as discount_percent,
                   CASE 
                       WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
                       THEN ROUND(original_price - price, 2)
                       ELSE 0
                   END as savings_amount
            FROM sale_items 
            WHERE (original_price > price AND price IS NOT NULL AND original_price IS NOT NULL)
               OR (discount IS NOT NULL AND discount != '')
            ORDER BY discount_percent DESC, savings_amount DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_discounted_items_since(self, since_time, limit: int = 100) -> List[dict]:
        """Get items with discounts scraped since a specific time."""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT *, 
                   CASE 
                       WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
                       THEN ROUND(((original_price - price) / original_price) * 100, 1)
                       ELSE 0
                   END as discount_percent,
                   CASE 
                       WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
                       THEN ROUND(original_price - price, 2)
                       ELSE 0
                   END as savings_amount
            FROM sale_items 
            WHERE scraped_at >= ? 
              AND ((original_price > price AND price IS NOT NULL AND original_price IS NOT NULL)
                   OR (discount IS NOT NULL AND discount != ''))
            ORDER BY discount_percent DESC, savings_amount DESC
            LIMIT ?
        ''', (since_time.isoformat(), limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sale_statistics(self) -> dict:
        """Get statistics focused on sales and discounts."""
        cursor = self.connection.cursor()
        
        # Items with discounts
        cursor.execute('''
            SELECT COUNT(*) as count,
                   AVG(((original_price - price) / original_price) * 100) as avg_discount,
                   MAX(((original_price - price) / original_price) * 100) as max_discount,
                   SUM(original_price - price) as total_savings
            FROM sale_items 
            WHERE original_price > price 
              AND price IS NOT NULL 
              AND original_price IS NOT NULL
        ''')
        discount_stats = cursor.fetchone()
        
        # Total items
        cursor.execute('SELECT COUNT(*) as count FROM sale_items')
        total_items = cursor.fetchone()['count']
        
        return {
            'total_items': total_items,
            'discounted_items': discount_stats['count'] or 0,
            'avg_discount_percent': round(discount_stats['avg_discount'] or 0, 1),
            'max_discount_percent': round(discount_stats['max_discount'] or 0, 1),
            'total_savings': round(discount_stats['total_savings'] or 0, 2),
            'discount_rate': round((discount_stats['count'] or 0) / total_items * 100, 1) if total_items > 0 else 0
        }
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")