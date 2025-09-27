# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Sale Tracker is a Python application that scrapes and displays discounted sale items from configured websites (currently Filson). The application performs real-time scraping, extracts product information including accurate size availability, and displays results in a formatted table interface without persistent data storage.

## Commands

### Running the Application
```bash
python src/main.py
```

### Usage Examples
```bash
# Basic usage - scrape and display current Filson deals
python src/main.py

# Example interaction:
# 1. Application scrapes Filson.com automatically
# 2. Displays table with products, prices, discounts, and available sizes
# 3. Use 'o10' to open item #10 in browser
# 4. Use '15' to view detailed info for item #15
# 5. Press Enter to exit
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python tests/test_basic.py

# Run tests with unittest module
python -m unittest discover tests/ -v
```

### Development Commands
```bash
# Check Python syntax
python -m py_compile src/*.py

# Run linting (if flake8 is installed)
python -m flake8 src/ tests/ --max-line-length=100

# Check imports
python -c "import sys; sys.path.insert(0, 'src'); import main; print('All imports successful')"
```

## Architecture

### Core Components

**ConfigManager (`src/config_manager.py`)**
- Handles hierarchical configuration loading: default.json → local.json → environment variables
- Environment variables follow pattern: `SALE_TRACKER_<SECTION>_<KEY>` (e.g., `SALE_TRACKER_DB_FILENAME`)
- Supports nested configuration merging

**Database (`src/database.py`)**
- SQLite-based storage with tables for `sale_items`, `price_history`, `websites`
- Database is initialized but not used for data persistence in current workflow
- Provides infrastructure for future features if data retention is needed
- Uses SQLite Row factory for dictionary-like access to results

**WebScraper (`src/scraper.py`)**
- Advanced Filson.com scraping with JavaScript variant parsing for accurate size extraction
- Implements sophisticated price detection from multiple sources (JSON API, HTML, JavaScript)
- Extracts truly available sizes by parsing embedded JavaScript variant data
- Filters out colors and unavailable sizes using intelligent pattern matching
- Uses `SaleItem` dataclass for structured data with sizes, pricing, and discount information

**UserInterface (`src/ui.py`)**
- Streamlined interface that displays scraped results immediately without database storage
- Formatted table display with expanded columns for product names and size information
- Interactive features: open products in browser, view detailed product information
- Deterministic sorting and deduplication for consistent results across runs

### Data Flow
1. **Configuration Loading**: ConfigManager loads settings from files and environment
2. **Database Initialization**: Database creates tables (unused in current workflow)
3. **Scraping Process**: WebScraper fetches Filson.com data and parses JavaScript for accurate product/size info
4. **Size Extraction**: Advanced parsing of JavaScript variant data to extract only truly available sizes
5. **Discount Filtering**: Items filtered to show only products with genuine discounts
6. **Direct Display**: Results displayed immediately in formatted table without storage
7. **User Interaction**: Browse results, open products in browser, view detailed information

### Key Configuration

**Database Config** (`config/default.json`)
- SQLite database available for infrastructure but not used in current workflow
- Database remains initialized for potential future features

**Scraping Config**
- Request delays: 1000ms default with exponential backoff
- Advanced retry logic: 3 attempts with proper error handling
- Configurable user agent and timeout settings
- Specialized Filson.com parsing with JavaScript variant extraction

**Website Configuration**
- Currently configured for Filson.com with advanced parsing rules
- Extracts product names, prices, discounts, and accurate size availability
- Uses multiple parsing strategies: JSON API, HTML selectors, JavaScript parsing
- Size filtering logic removes colors and shows only truly available sizes

## Development Notes

### Current Implementation Status
- **Fully functional**: Filson.com scraping with accurate size extraction
- **Advanced features**: JavaScript variant parsing, multi-source price detection
- **User interface**: Formatted table display with interactive browsing
- **Data handling**: Real-time processing without persistent storage

### Adding New Websites
1. Study the website's structure and identify discount/sale pages
2. Implement parsing logic in `WebScraper._parse_items()` following Filson.com patterns
3. Add size extraction logic specific to the site's format
4. Configure price detection for the site's pricing structure
5. Add website configuration to `config/default.json`
6. Test thoroughly with various product types and size variations

### Database Schema
- `sale_items`: Main item storage with price tracking
- `price_history`: Historical price data linked by URL
- `websites`: Metadata about configured target sites
- URLs are used as natural keys for linking items and price history

### Configuration Hierarchy
1. `config/default.json` - Base configuration
2. `config/local.json` - Local overrides (gitignored)
3. Environment variables - Runtime overrides

### Testing Strategy
- Tests use in-memory SQLite databases (`:memory:`)
- Unit tests cover core components independently
- Integration testing via main application flow
- Tests are located in `tests/` directory with `test_` prefix

### Logging
- Structured logging with configurable levels
- Logs to both file (`logs/app.log`) and console
- Log level configurable via `config.logging.level`
- Log file path configurable via `SALE_TRACKER_LOGGING_FILE`

### Dependencies
- **Standard Library**: `sqlite3`, `logging`, `json`, `pathlib`, `datetime`, `time`, `re`, `webbrowser`
- **External**: `requests` (HTTP client), `beautifulsoup4` (HTML parsing)
- **Development**: `unittest` (built-in testing)
- **Optional**: `pyperclip` (clipboard functionality for URL copying)

### File Structure
```
src/
├── main.py           # Application entry point and orchestration
├── config_manager.py # Configuration loading and management
├── database.py       # Data persistence and retrieval
├── scraper.py        # Web scraping functionality
└── ui.py            # Command-line user interface
config/
├── default.json      # Base configuration
└── local.json        # Local overrides (gitignored)
tests/
└── test_basic.py     # Basic unit tests
```

### Current Features

**Intelligent Size Extraction**
- Parses JavaScript variant data for accurate size availability
- Filters out color variants and unavailable sizes
- Supports various size formats: standard (XS-3XL), numeric, dimensions (32x34), etc.
- Shows only truly purchasable sizes based on inventory data

**Advanced Price Detection**
- Multiple parsing strategies: JSON API endpoints, HTML selectors, embedded JavaScript
- Accurate discount calculation and percentage display
- Handles various price formats and currency representations
- Filters results to show only items with genuine discounts

**User Interface**
- Formatted table with expanded columns for better readability (55-character size column)
- Consistent sorting by discount percentage for predictable results
- Interactive features: open products in browser (`o` + number), view details (number)
- Real-time display without data persistence for fresh results each run

**Filson.com Integration**
- Comprehensive scraping of Filson sale pages
- Handles various product types: clothing, accessories, bags, etc.
- Extracts product variants with color and size differentiation
- Processes discount percentages ranging from 30% to 70% off

### Error Handling
- Robust HTTP request handling with retry logic and exponential backoff
- Graceful degradation when size extraction fails (shows N/A)
- Configuration loading handles missing files with sensible defaults
- User-friendly error messages and logging for debugging
- Fallback parsing strategies when primary methods fail
