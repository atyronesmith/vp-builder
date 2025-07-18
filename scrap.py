#!/usr/bin/env python3
"""
Web Scraper and Markdown Converter

Crawls a website starting from a given URL, converts pages to Markdown,
and saves them into a single file while respecting the site hierarchy.
"""

import sys
import subprocess
import pkg_resources
from importlib import import_module

def check_and_install_dependencies():
    """Check and install required dependencies if not present."""
    required_packages = {
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'html2text': 'html2text'
    }

    missing_packages = []

    for module_name, package_name in required_packages.items():
        try:
            import_module(module_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print(f"Installing missing dependencies: {', '.join(missing_packages)}...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'] + missing_packages
            )
            print("Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("\nError: Failed to install dependencies automatically.")
            print("Please install manually with:")
            print(f"  pip install {' '.join(missing_packages)}")
            sys.exit(1)

# Check and install dependencies before importing them
check_and_install_dependencies()

import requests
from bs4 import BeautifulSoup
import html2text
import re
from urllib.parse import urljoin, urlparse
import argparse
import logging
from typing import Set, List, Tuple, Optional, Union, Any


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def clean_filename(filename: str) -> str:
    """
    Remove invalid characters from a filename.

    Args:
        filename: The filename to clean

    Returns:
        Cleaned filename safe for filesystem use
    """
    # Remove or replace invalid characters
    cleaned = re.sub(r'[\/:*?"<>|]', '_', filename)
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    # Remove leading/trailing underscores
    return cleaned.strip('_')


def is_valid_url(url: str, base_domain: str) -> bool:
    """
    Check if URL is valid and belongs to the same domain.

    Args:
        url: URL to validate
        base_domain: Base domain to check against

    Returns:
        True if URL is valid and from same domain
    """
    try:
        parsed = urlparse(url)
        base_parsed = urlparse(base_domain)

        # Check if it's a valid HTTP(S) URL
        if parsed.scheme not in ['http', 'https']:
            return False

        # Check if it's from the same domain
        return parsed.netloc == base_parsed.netloc
    except Exception:
        return False


def extract_main_content(soup: BeautifulSoup) -> Optional[Any]:
    """
    Extract the main content from a page.

    Tries to find the main content area by looking for common patterns.

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        Tag object of main content or entire body
    """
    # Try to find main content areas (in order of preference)
    content_selectors = [
        'main',
        'article',
        '[role="main"]',
        '#main',
        '#content',
        '.main-content',
        '.content',
        'body'
    ]

    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            return content

    # Fallback to body
    return soup.find('body')


def convert_to_markdown(html_content: str, ignore_links: bool = False) -> str:
    """
    Convert HTML content to Markdown.

    Args:
        html_content: HTML string to convert
        ignore_links: Whether to ignore links in conversion

    Returns:
        Markdown formatted string
    """
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    h.single_line_break = True

    return h.handle(html_content)


def fetch_page(url: str, timeout: int = 10) -> Optional[requests.Response]:
    """
    Fetch a page with proper error handling.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Response object or None if error
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraper/1.0)'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None


def extract_links(soup: BeautifulSoup, current_url: str, base_url: str) -> List[str]:
    """
    Extract valid links from a page.

    Args:
        soup: BeautifulSoup object of the page
        current_url: Current page URL
        base_url: Base URL of the site

    Returns:
        List of absolute URLs
    """
    links = []

    for link in soup.find_all('a', href=True):
        href = link['href'].strip()

        # Skip empty links, anchors, and non-HTTP protocols
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue

        # Convert to absolute URL
        absolute_url = urljoin(current_url, href)

        # Validate and add
        if is_valid_url(absolute_url, base_url):
            # Remove fragment identifiers
            absolute_url = absolute_url.split('#')[0]
            if absolute_url not in links:
                links.append(absolute_url)

    return links


def crawl_and_convert(
    start_url: str,
    output_file: str,
    max_depth: int = 2,
    max_pages: int = 100,
    verbose: bool = False
) -> None:
    """
    Crawl a website and convert pages to Markdown.

    Args:
        start_url: Starting URL for crawling
        output_file: Output file path
        max_depth: Maximum crawl depth
        max_pages: Maximum number of pages to crawl
        verbose: Enable verbose logging
    """
    setup_logging(verbose)

    visited_urls: Set[str] = set()
    urls_to_visit: List[Tuple[str, int]] = [(start_url, 0)]
    markdown_sections: List[Tuple[str, str, int, str]] = []  # (url, content, depth, title)

    logging.info(f"Starting crawl from: {start_url}")
    logging.info(f"Maximum depth: {max_depth}")
    logging.info(f"Maximum pages: {max_pages}")

    while urls_to_visit and len(visited_urls) < max_pages:
        current_url, depth = urls_to_visit.pop(0)

        # Skip if already visited or exceeds depth
        if current_url in visited_urls or depth > max_depth:
            continue

        logging.debug(f"Crawling: {current_url} (depth: {depth})")

        # Fetch the page
        response = fetch_page(current_url)
        if not response:
            continue

        visited_urls.add(current_url)

        # Parse the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get page title
        page_title = soup.title.string if soup.title else urlparse(current_url).path
        page_title = page_title.strip() if page_title else current_url

        # Extract main content
        main_content = extract_main_content(soup)

        if main_content:
            # Convert to markdown
            markdown = convert_to_markdown(str(main_content))

            # Store the content with metadata
            markdown_sections.append((current_url, markdown, depth, page_title))

            logging.info(f"Converted: {page_title} ({current_url})")

            # Extract links for further crawling
            if depth < max_depth:
                new_links = extract_links(soup, current_url, start_url)
                for link in new_links:
                    if link not in visited_urls:
                        urls_to_visit.append((link, depth + 1))

                logging.debug(f"Found {len(new_links)} links to follow")

    # Write to output file
    logging.info(f"Writing {len(markdown_sections)} pages to {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"# Website Content\n\n")
        f.write(f"Crawled from: {start_url}\n\n")
        f.write(f"Total pages: {len(markdown_sections)}\n\n")
        f.write("---\n\n")

        # Write table of contents
        f.write("## Table of Contents\n\n")
        for url, _, depth, title in markdown_sections:
            indent = "  " * depth
            f.write(f"{indent}- [{title}](#{clean_filename(title).lower()})\n")
        f.write("\n---\n\n")

        # Write content
        for url, content, depth, title in markdown_sections:
            # Create proper heading level (1-6)
            heading_level = min(depth + 2, 6)
            heading = "#" * heading_level

            f.write(f"{heading} {title}\n\n")
            f.write(f"URL: {url}\n\n")
            f.write(content)
            f.write("\n\n---\n\n")

    logging.info(f"Successfully created {output_file}")
    logging.info(f"Total pages crawled: {len(visited_urls)}")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Crawl a website and convert to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com -o site_content.md -d 3 -m 50
  %(prog)s https://example.com --verbose
        """
    )

    parser.add_argument(
        'url',
        help='Starting URL to crawl'
    )
    parser.add_argument(
        '-o', '--output',
        default='website_content.md',
        help='Output file name (default: website_content.md)'
    )
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=2,
        help='Maximum crawl depth (default: 2)'
    )
    parser.add_argument(
        '-m', '--max-pages',
        type=int,
        default=100,
        help='Maximum number of pages to crawl (default: 100)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'https://' + args.url

    try:
        crawl_and_convert(
            start_url=args.url,
            output_file=args.output,
            max_depth=args.depth,
            max_pages=args.max_pages,
            verbose=args.verbose
        )
    except KeyboardInterrupt:
        logging.info("\nCrawling interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


if __name__ == '__main__':
    main()
