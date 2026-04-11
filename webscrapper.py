"""
Advanced Web Scraper for Multiple Movie/Series Websites
Supports: VegaMovies, and more (extensible framework)
Features: Quality filtering, Series/Movie detection, Direct link extraction
Updated: Uses CloudScraper instead of Selenium for cloud compatibility
"""

import re
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Use cloudscraper for lightweight cloud compatibility (no Chrome needed)
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("[WARNING] cloudscraper not installed, using requests fallback")


class VegaMoviesScraper:
    """VegaMovies website scraper with advanced link extraction"""
    
    def __init__(self):
        self.name = "VegaMovies"
        print(f"[INFO] {self.name} Scraper Initialized (CloudScraper Mode - No Chrome Needed)")
        
        # Initialize scraper
        if CLOUDSCRAPER_AVAILABLE:
            try:
                self.scraper = cloudscraper.create_scraper()
                print("[INFO] CloudScraper initialized successfully")
            except Exception as e:
                print(f"[WARNING] CloudScraper init failed: {e}, using requests fallback")
                self.scraper = requests.Session()
        else:
            self.scraper = requests.Session()
        
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _extract_episode(self, text: str, url_slug: str = "") -> str:
        """Extract episode number from text or URL"""
        if url_slug:
            slug_match = re.search(r'ep[-_]0*(\d{1,3})', url_slug.lower())
            if slug_match:
                return f"EP{slug_match.group(1).zfill(2)}"
        
        if text:
            combined = text.lower()
            patterns = [
                r'ep[-_:\s]*0*(\d{1,3})',
                r'episode[-_:\s]*0*(\d{1,3})',
                r'eps[-_:\s]*0*(\d{1,3})',
                r'e(\d{2,3})\b',
                r's\d+e(\d{1,3})',
                r'(?:ep|episode|eps)\s*(\d{1,3})',
            ]
            for pattern in patterns:
                match = re.search(pattern, combined)
                if match:
                    num = match.group(1)
                    return f"EP{num.zfill(2)}"
        
        return "EP01"
    
    def _normalize_quality(self, q: str) -> str:
        """Normalize quality string"""
        if not q or q == "unknown":
            return "unknown"
        
        q = q.upper()
        q = q.replace("HEVC X265", "x265").replace("X265", "x265")
        q = q.replace("X264", "x264")
        q = re.sub(r'\s+', ' ', q).strip()
        
        return q
    
    def _fetch_page(self, url: str) -> str:
        """Fetch page using cloudscraper (no Selenium/Chrome needed)"""
        try:
            print(f"[INFO] Loading page: {url[:80]}...")
            start = time.time()
            response = self.scraper.get(url, timeout=30)
            response.raise_for_status()
            elapsed = time.time() - start
            print(f"[SUCCESS] Page loaded in {elapsed:.2f}s")
            return response.text
        except Exception as e:
            print(f"[ERROR] Failed to fetch page: {e}")
            return ""
    
    def _extract_links_from_html(self, html: str, base_url: str) -> dict:
        """Extract all download links from HTML"""
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title and metadata
        title_tag = soup.find("title")
        raw_title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        clean_title = re.sub(r'\s*\|\s*Vegamovies.*$', '', raw_title, flags=re.I).strip()
        clean_title = re.sub(r'^Download\s+', '', clean_title, flags=re.I).strip()
        clean_title = re.sub(r'\s*\(\d{4}\s*-\s*\d{4}\)?', '', clean_title).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title)
        
        show_name = re.sub(r'\s*Season\s*\d+.*|EP.*Added.*', '', clean_title, flags=re.I).strip()
        
        season_match = re.search(r'Season\s*0*(\d+)', clean_title, re.I)
        season = season_match.group(1).zfill(2) if season_match else "01"
        
        is_series = any(k in base_url.lower() for k in ["season", "ep-", "episode", "s0", "s1", "s2"])
        
        print(f"[INFO] Title: {show_name} | Season: S{season} | Type: {'SERIES' if is_series else 'MOVIE'}")
        
        links = {
            "title": show_name,
            "season": season,
            "is_series": is_series,
            "downloads": []
        }
        
        current_quality = "unknown"
        current_size = "unknown"
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'div', 'p', 'span', 'a']):
            text = element.get_text(" ", strip=True)
            
            # Check for quality indicators
            quality_match = re.search(r'(480p|720p|1080p|4k|2160p)\s*(?:x264|x265|HEVC)?', text, re.I)
            if quality_match:
                current_quality = self._normalize_quality(quality_match.group(0))
                size_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', text, re.I)
                if size_match:
                    current_size = size_match.group(0).upper()
                continue
            
            # Extract download links
            if element.name == "a" and element.has_attr("href"):
                href = urljoin(base_url, element["href"])
                link_text = element.get_text(" ", strip=True)
                
                if any(x in href.lower() for x in ["nexdrive", "fast-dl.org"]):
                    episode = self._extract_episode(link_text, href)
                    
                    links["downloads"].append({
                        "short_url": href,
                        "quality": current_quality,
                        "size": current_size,
                        "episode": episode,
                        "resolved": False,
                        "direct_links": []
                    })
        
        print(f"[INFO] Found {len(links['downloads'])} download links")
        return links
    
    def _resolve_shortener(self, short_url: str, is_series: bool) -> list:
        """Resolve shortener links to direct download URLs using HTTP requests"""
        direct_links = []
        
        try:
            print(f"[INFO] Resolving shortener: {short_url[:60]}...")
            response = self.scraper.get(short_url, allow_redirects=True, timeout=15)
            
            # Extract direct Google Drive links from HTML and final URL
            links = set()
            
            # Check final URL
            if 'googleusercontent' in response.url.lower():
                links.add(response.url)
            
            # Extract from HTML
            matches = re.findall(r'https?://[^\s"\'<>]+', response.text)
            for m in matches:
                if any(x in m.lower() for x in ["googleusercontent", "video-downloads.googleusercontent", "drive.google"]):
                    # Clean URL
                    m = m.split('"')[0].split("'")[0]
                    if m.startswith('http'):
                        links.add(m)
            
            # Also check for direct links in the response
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("http") and not any(x in href.lower() for x in ["nexdrive", "fast-dl", "vgmlinks", "tinyurl", "t.me"]):
                    if "googleusercontent" in href.lower() or "drive.google" in href.lower():
                        links.add(href)
            
            direct_links = list(links) if links else [response.url]
            print(f"[SUCCESS] Resolved {len(direct_links)} direct link(s)")
        
        except Exception as e:
            print(f"[ERROR] Failed to resolve shortener: {e}")
        
        return direct_links
    
    def scrape(self, url: str, quality_filter: str = None) -> list:
        """
        Main scraping function (CloudScraper version - no Chrome needed)
        
        Args:
            url: VegaMovies URL to scrape
            quality_filter: Optional quality filter (e.g., "720p", "1080p")
        
        Returns:
            List of direct download links with metadata
        """
        start_time = time.time()
        results = []
        
        try:
            # Fetch and parse page
            html = self._fetch_page(url)
            if not html:
                return []
            
            links_data = self._extract_links_from_html(html, url)
            
            # Apply quality filter if provided
            if quality_filter:
                norm_quality = self._normalize_quality(quality_filter)
                links_data["downloads"] = [
                    l for l in links_data["downloads"]
                    if self._normalize_quality(l.get("quality", "unknown")) == norm_quality
                ]
                if not links_data["downloads"]:
                    print(f"[WARNING] No links found for quality: {quality_filter}")
                    return []
                print(f"[INFO] Quality filter applied: {quality_filter}")
            
            # Resolve shortener links to direct downloads
            print(f"[INFO] Resolving {len(links_data['downloads'])} shortener link(s)...")
            
            for idx, link_info in enumerate(links_data["downloads"], 1):
                print(f"[INFO] Processing [{idx}/{len(links_data['downloads'])}] {link_info['quality']} {link_info['episode']}")
                
                direct_links = self._resolve_shortener(link_info["short_url"], links_data["is_series"])
                
                for direct_url in direct_links:
                    results.append({
                        "title": links_data["title"],
                        "season": links_data["season"],
                        "episode": link_info["episode"],
                        "quality": link_info["quality"],
                        "size": link_info["size"],
                        "url": direct_url
                    })
            
            # Remove duplicates
            unique_results = {}
            for r in results:
                key = (r["url"], r["episode"], r["quality"])
                if key not in unique_results:
                    unique_results[key] = r
            
            results = list(unique_results.values())
            total_time = time.time() - start_time
            
            print(f"[SUCCESS] Scraping completed in {total_time:.2f}s - Found {len(results)} direct links")
            
            return results
        
        except Exception as e:
            print(f"[ERROR] Scraping failed: {e}")
            import traceback
            traceback.print_exc()
            return []


def get_scraper_for_url(url: str):
    """Get appropriate scraper for URL"""
    url_lower = url.lower()
    
    if "vegamovies" in url_lower:
        return VegaMoviesScraper()
    
    # Add more scrapers here in future
    # if "example.com" in url_lower:
    #     return ExampleScraper()
    
    return None


def scrape_website(url: str, quality_filter: str = None) -> list:
    """
    Main entry point for web scraping
    
    Args:
        url: Website URL to scrape
        quality_filter: Optional quality filter
    
    Returns:
        List of direct download links
    """
    print(f"\n[INFO] ========== WEB SCRAPER INITIATED ==========")
    print(f"[INFO] URL: {url}")
    if quality_filter:
        print(f"[INFO] Quality Filter: {quality_filter}")
    print(f"[INFO] ============================================\n")
    
    scraper = get_scraper_for_url(url)
    
    if not scraper:
        print(f"[ERROR] No scraper available for URL: {url}")
        return []
    
    try:
        results = scraper.scrape(url, quality_filter)
        
        if results:
            print(f"\n[INFO] ========== SCRAPING RESULTS ==========")
            for i, result in enumerate(results, 1):
                print(f"[{i}] {result['title']} - {result['quality']} - {result['episode']}")
                print(f"    URL: {result['url'][:80]}...")
            print(f"[INFO] ========================================\n")
        
        return results
    
    except Exception as e:
        print(f"[ERROR] Scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Web Scraper")
    parser.add_argument("-u", "--url", required=True, help="Website URL to scrape")
    parser.add_argument("-q", "--quality", default=None, help="Quality filter (e.g., 720p, 1080p)")
    
    args = parser.parse_args()
    
    results = scrape_website(args.url, args.quality)
    
    if results:
        print("\n=== DIRECT DOWNLOAD LINKS ===")
        for r in results:
            print(f"{r['url']}")
