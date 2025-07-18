# Web Scraper and Markdown Converter

A Python tool that crawls websites and converts pages to Markdown format, preserving site hierarchy and structure.

## 🚀 Features

- **Automatic Dependency Installation**: The script automatically installs required dependencies on first run
- Crawls websites starting from a given URL
- Converts HTML pages to clean Markdown
- Respects site hierarchy and structure
- Generates table of contents
- Configurable crawl depth and page limits
- Verbose logging option

## 📦 Installation

No manual installation required! The script automatically installs its dependencies when you run it:

```bash
# Just run the script - dependencies will be installed automatically
./scrap.py https://example.com

# Or use the properly named alias
./scrape.py https://example.com
```

### Manual Installation (Optional)

If you prefer to install dependencies manually:

```bash
pip install -r scraper_requirements.txt
```

## 🎯 Usage

```bash
# Basic usage
./scrap.py https://example.com

# Custom output file
./scrap.py https://example.com -o my_site.md

# Increase crawl depth and page limit
./scrap.py https://example.com -d 5 -m 200

# Enable verbose logging
./scrap.py https://example.com --verbose

# Show help
./scrap.py --help
```

### Command Line Options

- `url`: Starting URL to crawl (required)
- `-o, --output`: Output file name (default: website_content.md)
- `-d, --depth`: Maximum crawl depth (default: 2)
- `-m, --max-pages`: Maximum number of pages to crawl (default: 100)
- `-v, --verbose`: Enable verbose output

## 🔧 How It Works

1. **Dependency Check**: On startup, the script checks for required dependencies:
   - `requests` - For HTTP requests
   - `beautifulsoup4` - For HTML parsing
   - `html2text` - For HTML to Markdown conversion

2. **Automatic Installation**: If any dependencies are missing, the script will:
   - Detect missing packages
   - Automatically install them using pip
   - Continue with normal operation

3. **Web Crawling**: Starting from the provided URL:
   - Fetches pages using requests
   - Parses HTML with BeautifulSoup
   - Extracts main content areas
   - Follows links up to specified depth

4. **Markdown Conversion**: For each page:
   - Converts HTML to clean Markdown
   - Preserves formatting and structure
   - Generates hierarchical headings based on crawl depth

5. **Output Generation**: Creates a single Markdown file with:
   - Table of contents
   - All crawled pages in hierarchical order
   - Proper heading levels and formatting

## 📋 Requirements

- Python 3.6+
- Internet connection (for crawling and dependency installation)

## 🚨 Limitations

- Respects same-domain policy (won't crawl external sites)
- Skips non-HTML content (PDFs, images, etc.)
- May be blocked by sites with anti-scraping measures
- Dependency installation requires pip to be available

## 📝 Output Format

The generated Markdown file includes:

```markdown
# Website Content

Crawled from: https://example.com

Total pages: 42

---

## Table of Contents

- [Home](#home)
  - [About Us](#about-us)
  - [Products](#products)
    - [Product A](#product-a)
    - [Product B](#product-b)

---

## Home

URL: https://example.com

[Page content in Markdown]

---

### About Us

URL: https://example.com/about

[Page content in Markdown]

---
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

Apache License 2.0