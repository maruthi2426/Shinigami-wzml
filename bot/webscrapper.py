"""
Advanced Web Scraper for VegaMovies
Uses Selenium to load pages with JavaScript rendering
Extracts download links and resolves shortener URLs to direct Google Drive links
"""

import re
import time
import requests
from urllib.parse import urljoin, parse_qs, urlparse

# Handle BeautifulSoup imports
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[ERROR] BeautifulSoup4 not installed")
    BeautifulSoup = None

# Try to use lxml parser, fallback to html.parser
try:
    import lxml
    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"

# Try to import Selenium for JavaScript-heavy sites
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    print("[WARNING] Selenium not available")
    SELENIUM_AVAILABLE = False


class VegaMoviesScraper:
    """VegaMovies website scraper with Selenium-based link extraction"""
    
    def __init__(self):
        self.name = "VegaMovies"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _create_driver(self):
        """Create optimized Chrome driver for scraping"""
        if not SELENIUM_AVAILABLE:
            return None
        
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-setuid-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--blink-settings=imagesEnabled=false")
            options.add_argument("--disable-features=Translate,OptimizationHints,MediaRouter")
            options.add_argument("--log-level=3")
            options.page_load_strategy = "eager"
            
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option("useAutomationExtension", False)
            
            return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except Exception as e:
            print(f"[ERROR] Failed to create Chrome driver: {e}")
            return None
    
    def _resolve_shortener(self, short_url: str) -> str:
        """Resolve shortener link to direct Google Drive URL"""
        try:
            # Try HEAD first (faster)
            try:
                response = self.session.head(short_url, allow_redirects=True, timeout=10)
                if response.status_code == 200 or response.url != short_url:
                    return response.url
            except:
                pass
            
            # Fallback to GET
            response = self.session.get(short_url, allow_redirects=True, timeout=10, stream=True)
            return response.url if response.status_code == 200 else None
        except Exception as e:
            print(f"[ERROR] Failed to resolve shortener {short_url}: {e}")
            return None
    
    def _extract_quality_from_text(self, text: str) -> str:
        """Extract quality info from text"""
        quality_patterns = {
            '4K': ['4k', '2160p'],
            '1080p': ['1080p', '1080'],
            '720p': ['720p', '720'],
            '480p': ['480p', '480'],
        }
        
        text_lower = text.lower()
        for quality, patterns in quality_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return quality
        return "unknown"
    
    def scrape(self, url: str, quality_filter: str = None) -> list:
        """
        Main scraping function for VegaMovies
        
        Args:
            url: VegaMovies URL to scrape
            quality_filter: Optional quality filter (e.g., "720p", "1080p")
        
        Returns:
            List of direct download links with metadata
        """
        print(f"\n[INFO] Starting VegaMovies scrape for: {url}")
        if quality_filter:
            print(f"[INFO] Quality filter: {quality_filter}")
        
        driver = None
        results = []
        
        try:
            # Create and use Selenium driver
            driver = self._create_driver()
            if not driver:
                print("[ERROR] Failed to create Chrome driver")
                return []
            
            print("[INFO] Loading page with Selenium...")
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page source
            page_source = driver.page_source
            
            if not page_source:
                print("[ERROR] Failed to get page source")
                return []
            
            print("[INFO] Page loaded, parsing HTML...")
            
            # Parse HTML
            if BeautifulSoup is None:
                print("[ERROR] BeautifulSoup not available")
                return []
            
            soup = BeautifulSoup(page_source, PARSER)
            
            # Extract download links
            links = []
            
            # Look for download buttons and links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if not href or not text:
                    continue
                
                # Filter for shortener and download links
                shortener_keywords = [
                    'bit.ly', 'tinyurl', 'short.link', 'is.gd', 'ow.ly',
                    'nexdrive', 'droplink', 'mpx.sh', 'link.workers.dev'
                ]
                
                is_shortener = any(kw in href.lower() for kw in shortener_keywords)
                is_download = any(kw in text.lower() for kw in ['download', 'get', 'dl', 'gdrive'])
                
                if (is_shortener or is_download) and href.startswith('http'):
                    links.append({
                        'url': href,
                        'text': text
                    })
                    print(f"[DEBUG] Found link: {text[:50]}... -> {href[:80]}...")
            
            print(f"[INFO] Found {len(links)} download links")
            
            if not links:
                print("[WARNING] No download links found on page")
                return []
            
            # Resolve shortener links and filter by quality
            print("[INFO] Resolving shortener links...")
            for link in links:
                short_url = link['url']
                text = link['text']
                
                # Extract quality from text
                quality = self._extract_quality_from_text(text)
                
                # Check quality filter
                if quality_filter:
                    quality_filter_lower = quality_filter.lower()
                    if quality_filter_lower not in text.lower() and quality_filter_lower not in quality.lower():
                        continue
                
                # Resolve shortener
                direct_url = self._resolve_shortener(short_url)
                if direct_url and 'google' in direct_url.lower():
                    results.append({
                        'url': direct_url,
                        'quality': quality,
                        'name': text[:100],
                        'source': 'vegamovies'
                    })
                    print(f"[INFO] Resolved: {text[:50]} -> {direct_url[:80]}...")
            
            print(f"[INFO] Total results after filtering: {len(results)}")
            
        except Exception as e:
            print(f"[ERROR] Scraping error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return results


# Global scraper instance
_vegamovies_scraper = None

def scrape_website(url: str, quality_filter: str = None) -> list:
    """
    Scrape VegaMovies website and return direct download links
    
    Args:
        url: VegaMovies URL to scrape
        quality_filter: Optional quality filter
    
    Returns:
        List of direct download links with metadata
    """
    global _vegamovies_scraper
    
    if _vegamovies_scraper is None:
        _vegamovies_scraper = VegaMoviesScraper()
    
    # Detect website and route to appropriate scraper
    if 'vegamovies' in url.lower():
        return _vegamovies_scraper.scrape(url, quality_filter)
    else:
        print(f"[WARNING] Unknown website: {url}")
        return []


def get_scraper_for_url(url: str):
    """Get appropriate scraper for URL"""
    if 'vegamovies' in url.lower():
        return VegaMoviesScraper()
    return None
