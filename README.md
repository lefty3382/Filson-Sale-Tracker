# Sale Tracker

A Python application that scrapes and displays discounted sale items from Filson.com with accurate size availability and pricing information.

## Overview

Sale Tracker performs real-time scraping of Filson.com's sale pages, extracts product information including truly available sizes, and displays results in a clean formatted table. The application focuses on providing accurate, up-to-date discount information without storing data persistently.

## Features

✅ **Real-time Filson.com scraping** - No cached data, always current
✅ **Accurate size extraction** - Shows only truly available sizes (filters out colors and out-of-stock)
✅ **Advanced discount detection** - Multi-source price parsing for reliable discount calculations
✅ **Interactive browser integration** - Open products directly in your browser
✅ **Formatted table display** - Clean, readable results with expanded size information
✅ **Consistent results** - Deterministic sorting and deduplication

## Getting Started

### Prerequisites
- Python 3.7+
- Internet connection for scraping

### Installation
1. Clone or download the repository
2. Install required dependencies:
   ```bash
   pip install requests beautifulsoup4
   ```
3. (Optional) Install clipboard support:
   ```bash
   pip install pyperclip
   ```

### Usage
```bash
# Run the application
python src/main.py
```

### Example Output
```
Sale Tracker - Scraping latest deals...
======================================

Starting fresh scrape...
Scraping 1 website(s)...
Scraped 50 items.

Found 43 discounted items!

┌──────┬──────────────────────────────┬──────────────┬───────────────┬──────────┬────────────┬─────────────────────────────┬────────────┐
│ #    │ Product Name                 │   Sale Price │    Original $ │    % Off │     Save $ │ Sizes                       │ Website    │
├──────┼──────────────────────────────┼──────────────┼───────────────┼──────────┼────────────┼─────────────────────────────┼────────────┤
│ 1    │ Field Flannel Shirt          │       $35.70 │       $119.00 │      70% │     $83.30 │ XL                          │ Filson     │
│ 10   │ Lined Mackinaw Wool Jac Shirt│      $225.00 │       $450.00 │      50% │    $225.00 │ 2XL, S, XS                  │ Filson     │
└──────┴──────────────────────────────┴──────────────┴───────────────┴──────────┴────────────┴─────────────────────────────┴────────────┘

Actions: Enter item number to view details, 'o' + number to open in browser (e.g., 'o1'), or press Enter to return.
```

### Interactive Commands
- **View details**: Enter item number (e.g., `10`)
- **Open in browser**: Enter `o` + item number (e.g., `o10`)
- **Exit**: Press Enter

## Technical Details

### How It Works
1. **Scrapes Filson.com** sale pages using advanced parsing techniques
2. **Extracts JavaScript data** from embedded Shopify variant information
3. **Filters sizes** by parsing only truly available inventory (not just display options)
4. **Calculates discounts** from multiple price sources for accuracy
5. **Displays results** in real-time without database storage

### Project Structure
```
sale-tracker/
├── src/
│   ├── main.py              # Application entry point
│   ├── scraper.py           # Advanced Filson.com scraping logic
│   ├── ui.py                # Formatted table display and interactions
│   ├── database.py          # Database infrastructure (unused in current workflow)
│   └── config_manager.py    # Configuration loading
├── config/
│   ├── default.json         # Default application settings
│   └── local.json           # Local overrides (gitignored)
├── tests/
│   └── test_basic.py        # Unit tests
├── README.md                # This file
└── WARP.md                  # Detailed technical documentation
```

### Size Extraction Logic
The application uses sophisticated parsing to extract only truly available sizes:
- Parses JavaScript variant data from Shopify
- Filters out color names and invalid options
- Checks inventory availability flags
- Supports multiple size formats (XS-3XL, numeric, dimensions)

## Configuration

The application is configured via JSON files in the `config/` directory:

- `config/default.json` - Base configuration with Filson.com settings
- `config/local.json` - Local overrides (gitignored)

Key settings:
```json
{
  "targets": {
    "websites": [
      {
        "name": "Filson",
        "url": "https://www.filson.com/sale",
        "base_url": "https://www.filson.com"
      }
    ]
  },
  "scraper": {
    "request_delay": 1000,
    "max_retries": 3,
    "timeout": 30000
  }
}
```

## Testing

```bash
# Run basic tests
python tests/test_basic.py

# Run with unittest module
python -m unittest discover tests/ -v

# Test imports and basic functionality
python -c "import sys; sys.path.insert(0, 'src'); import main; print('All imports successful')"
```

## Troubleshooting

### Common Issues

**No items found**
- Check internet connection
- Filson.com may be down or have changed their page structure
- Verify the sale page is accessible in your browser

**Size information shows "N/A"**
- This is normal for products that are completely out of stock
- The scraper only shows truly available sizes

**Browser won't open products**
- Ensure you have a default browser set
- Try copying the URL manually from the product details view

### Debug Mode
For detailed logging, check the console output - the application provides verbose logging for troubleshooting scraping issues.

## Notes

- **No data persistence**: Each run is completely fresh
- **Real-time data**: Results reflect current website state
- **Filson-specific**: Currently optimized for Filson.com's structure
- **Size accuracy**: Only shows inventory-available sizes, not just display options

## Documentation

For detailed technical documentation, see [WARP.md](WARP.md).
