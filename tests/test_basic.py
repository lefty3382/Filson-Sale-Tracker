"""
Basic tests for the Sale Tracker application.
"""

import unittest
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config_manager import ConfigManager
from scraper import SaleItem
from database import Database

class TestConfigManager(unittest.TestCase):
    """Test the ConfigManager class."""
    
    def test_config_manager_initialization(self):
        """Test that ConfigManager initializes correctly."""
        config_manager = ConfigManager()
        self.assertIsInstance(config_manager, ConfigManager)
    
    def test_load_config(self):
        """Test loading configuration."""
        config_manager = ConfigManager()
        try:
            config = config_manager.load_config()
            self.assertIsInstance(config, dict)
        except FileNotFoundError:
            # Expected if no config file exists
            pass

class TestSaleItem(unittest.TestCase):
    """Test the SaleItem dataclass."""
    
    def test_sale_item_creation(self):
        """Test creating a SaleItem instance."""
        item = SaleItem(
            title="Test Item",
            price=29.99,
            original_price=39.99,
            discount="25% off",
            url="https://example.com/item",
            image_url="https://example.com/image.jpg",
            website="example.com",
            scraped_at="2023-01-01T12:00:00"
        )
        
        self.assertEqual(item.title, "Test Item")
        self.assertEqual(item.price, 29.99)
        self.assertEqual(item.original_price, 39.99)
        self.assertEqual(item.discount, "25% off")
        self.assertEqual(item.url, "https://example.com/item")
        self.assertEqual(item.website, "example.com")

class TestDatabase(unittest.TestCase):
    """Test the Database class."""
    
    def setUp(self):
        """Set up test database."""
        self.db_config = {"type": "sqlite", "filename": ":memory:"}
        self.database = Database(self.db_config)
        self.database.initialize()
    
    def test_database_initialization(self):
        """Test database initialization."""
        self.assertIsNotNone(self.database.connection)
    
    def test_save_and_get_items(self):
        """Test saving and retrieving items."""
        item = SaleItem(
            title="Test Item",
            price=29.99,
            original_price=39.99,
            discount="25% off",
            url="https://example.com/item",
            image_url="https://example.com/image.jpg",
            website="example.com",
            scraped_at="2023-01-01T12:00:00"
        )
        
        # Save item
        saved_count = self.database.save_items([item])
        self.assertEqual(saved_count, 1)
        
        # Get items
        items = self.database.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], "Test Item")
    
    def tearDown(self):
        """Clean up after test."""
        self.database.close()

if __name__ == '__main__':
    unittest.main()