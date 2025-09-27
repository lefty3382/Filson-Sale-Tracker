#!/usr/bin/env python3
"""Test display of items with size information."""

from database import Database
from ui import UserInterface

# Create database and UI instances
config = {'filename': 'sale_tracker.db'}
db = Database(config)
db.initialize()
ui = UserInterface()

# Get just the women's items that have size info
items = db.get_discounted_items()
women_items = [item for item in items if 'Women' in item['title'] and item.get('sizes')][:6]

print('Testing display with items that have size information:')
print()
if women_items:
    ui.display_discounted_items(women_items)
else:
    print('No womens items with size info found.')