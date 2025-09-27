#!/usr/bin/env python3
"""
Test the new table format display
"""

import sys
import os
sys.path.append('src')

from ui import UserInterface
from database import Database

# Initialize the UI
ui = UserInterface()

# Create mock database
config = {'database': {'filename': 'sale_tracker.db'}}
database = Database(config['database'])
database.initialize()

# Test the best discounts display
print("Testing the new table format...")
print("="*80)

items = database.get_discounted_items(limit=10)

if items:
    print(f"Found {len(items)} discounted items!")
    ui.display_discounted_items(items)
else:
    print("No discounted items found. Let me show recent items instead...")
    recent_items = database.get_items(limit=10)
    if recent_items:
        ui.display_items(recent_items)
    else:
        print("No items found in database at all!")