#!/usr/bin/env python3
"""
Sale Tracker - Main Application Entry Point

An application that shows items on sale from a particular website.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from scraper import WebScraper
from database import Database
from ui import UserInterface

def setup_logging(config):
    """Set up logging configuration."""
    log_level = getattr(logging, config['logging']['level'].upper())
    log_file = config['logging']['file']
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting {config['app']['name']} v{config['app']['version']}")
        
        # Initialize components
        database = Database(config['database'])
        scraper = WebScraper(config['scraping'])
        ui = UserInterface()
        
        # Initialize database
        database.initialize()
        
        logger.info("Application initialized successfully")
        
        # Start the application
        ui.run(database, scraper, config)
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()