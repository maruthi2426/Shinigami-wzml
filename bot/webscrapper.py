import re
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Try to use Selenium for robust shortener resolution, fallback to CloudScraper
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
    print("[INFO] Selenium detected - will use for shortener resolution")
except ImportError:
    print("[INFO] Selenium not available - using CloudScraper + requests fallback")

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("[WARNING] cloudscraper not installed")


class VegamoviesScraper:
    def __init__(self):
        self.scraper = None
        self.driver = None
        self.selenium_available = SELENIUM_AVAILABLE
        
        if CLOUDSCRAPER_AVAILABLE:
            try:
                self.scraper = cloudscraper.create_scraper()
                print("[INFO] CloudScraper initialized for page fetching")
            except Exception as e:
                print(f"[WARNING] CloudScraper init failed: {e}, using requests fallback")
                self.scraper = requests.Session()
        else:
            self.scraper = requests.Session()
        
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _extract_episode(self, text="", url_slug=""):
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
                r'ep\s*-\s*0*(\d{1,3})',
            ]
            for pattern in patterns:
                match = re.search(pattern, combined)
                if match:
                    num = match.group(1)
                    return f"EP{num.zfill(2)}"
        return "unknown"

    def _normalize_quality(self, q):
        if not q or q == "unknown":
            return "unknown"
        q = q.upper().replace("HEVC X265", "HEVC x265").replace("X265", "HEVC x265")
        q = q.replace("X264", "x264")
        q = re.sub(r'\s+', ' ', q).strip()
        return q

    def _fetch_page(self, url, driver=None):
        """Fetch page using Selenium driver with scrolling to load all content"""
        if driver is None:
            # Fallback to CloudScraper if no driver available
            print("[INFO] Loading VegaMovies page (CloudScraper fallback)...")
            start = time.time()
            try:
                response = self.scraper.get(url, timeout=30)
                response.raise_for_status()
                elapsed = time.time() - start
                print(f"[INFO] Page loaded in {elapsed:.2f}s")
                return response.text
            except Exception as e:
                print(f"[ERROR] Failed to fetch page: {e}")
                return None
        
        # Use Selenium with scrolling for better link loading
        print("[INFO] Loading VegaMovies page with Selenium (scrolling)...")
        start = time.time()
        try:
            driver.get(url)
            
            # Scroll to load all lazy-loaded content
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.15)
            
            time.sleep(0.5)
            html = driver.page_source
            elapsed = time.time() - start
            print(f"[INFO] Page loaded in {elapsed:.2f}s with full content")
            return html
        except Exception as e:
            print(f"[ERROR] Failed to fetch page with Selenium: {e}")
            return None

    def get_links(self, html, base, url):
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("title")
        raw_title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
        clean_title = re.sub(r'\s*\|\s*Vegamovies.*$', '', raw_title, flags=re.I).strip()
        clean_title = re.sub(r'^Download\s+', '', clean_title, flags=re.I).strip()
        clean_title = re.sub(r'\s*\(\d{4}\s*-\s*\d{4}\)?', '', clean_title).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title)
        
        show_name = re.sub(r'\s*Season\s*\d+.*|EP.*Added.*', '', clean_title, flags=re.I).strip()
        season_match = re.search(r'Season\s*0*(\d+)', clean_title, re.I)
        season = season_match.group(1).zfill(2) if season_match else "02"

        page_episode = self._extract_episode("", url)
        if page_episode == "unknown":
            page_episode = self._extract_episode(clean_title, "")

        print(f"[INFO] Show: {show_name} | Season: S{season} | Episode: {page_episode}")

        links = []
        current_quality = "unknown"
        current_size = "unknown"

        # Enhanced element scanning for better quality/size detection
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'div', 'p', 'span', 'a', 'button']):
            text = element.get_text(" ", strip=True)
            
            # More comprehensive quality matching
            quality_match = re.search(r'(480p|720p|1080p|4k|2160p|HQ\s+1080p|X264|X265|HEVC)\s*(?:x264|x265|HEVC|H\.?264|H\.?265)?', text, re.I)
            if quality_match:
                current_quality = self._normalize_quality(quality_match.group(0))
                # Also try to find size info in the same element
                size_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', text, re.I)
                if size_match:
                    current_size = size_match.group(0).upper()
                continue

            # Better link extraction - check both href and parents
            if element.name == "a" and element.has_attr("href"):
                href = urljoin(base, element["href"])
                full_text = element.get_text(" ", strip=True)
                
                # Check for shortener links
                if any(x in href.lower() for x in ["nexdrive", "fast-dl.org", "fastdl"]):
                    # Try to find size in link text and parent
                    size_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', full_text + " " + text, re.I)
                    size = size_match.group(0).upper() if size_match else current_size
                    
                    # Extract episode from link text or URL
                    episode = self._extract_episode(full_text, href)
                    if episode == "unknown":
                        episode = page_episode
                    
                    # Only add if we have valid URL
                    if href and href.startswith('http'):
                        links.append({
                            "url": href,
                            "size": size,
                            "quality": current_quality,
                            "episode": episode,
                            "show_name": show_name,
                            "season": season
                        })
                        print(f"[DEBUG] Found link: {episode} | {current_quality} | {size}")

        print(f"[INFO] Found {len(links)} shortener link(s) total")
        return links

    def _create_selenium_driver(self):
        """Create a Selenium Chrome driver for shortener resolution"""
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
            options.add_argument("--page-load-strategy=eager")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except Exception as e:
            print(f"[WARNING] Failed to create Selenium driver: {e}")
            return None
    
    def _resolve_with_selenium(self, short_url):
        """Resolve shortener using Selenium (handles JavaScript redirects)"""
        if not SELENIUM_AVAILABLE or self.driver is None:
            return []
        
        try:
            print(f"[INFO] Using Selenium to resolve: {short_url[:60]}...")
            self.driver.get(short_url)
            time.sleep(0.15)
            
            # Look for and click verify button if present
            try:
                verify_btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'verify')] | "
                        "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'verify')]"
                    ))
                )
                self.driver.execute_script("arguments[0].click();", verify_btn)
                time.sleep(0.8)
            except TimeoutException:
                time.sleep(1.0)
            
            # Extract links from page
            links = set()
            
            # Get direct links from href attributes
            for el in self.driver.find_elements(By.TAG_NAME, "a"):
                try:
                    href = el.get_attribute("href")
                    if href and href.startswith("http"):
                        if not any(x in href.lower() for x in ["nexdrive", "fast-dl", "vgmlinks", "tinyurl", "t.me"]):
                            links.add(href)
                except:
                    continue
            
            # Get links from page source
            html = self.driver.page_source
            matches = re.findall(r'https?://[^\s"\'<>]+', html)
            for m in matches:
                if any(x in m.lower() for x in ["googleusercontent", "video-downloads.googleusercontent", "drive.google"]):
                    links.add(m)
            
            if links:
                print(f"[INFO] Selenium resolved {len(links)} direct link(s)")
                return list(links)
            else:
                print(f"[WARNING] Selenium: No direct links found")
                return []
        
        except Exception as e:
            print(f"[WARNING] Selenium resolution failed: {e}")
            return []

    def _resolve_shortener(self, short_url):
        """Resolve shortener using Selenium first, fallback to HTTP requests"""
        # Try Selenium first if available
        if self.driver is not None:
            links = self._resolve_with_selenium(short_url)
            if links:
                return links
        
        # Fallback to HTTP-based resolution
        try:
            print(f"[INFO] Resolving shortener (HTTP): {short_url[:60]}...")
            response = self.scraper.get(short_url, allow_redirects=True, timeout=15, verify=False)
            response.encoding = 'utf-8'
            
            # Extract direct Google Drive links from HTML
            links = set()
            
            # Check final URL for direct drive links
            if any(x in response.url.lower() for x in ['googleusercontent', 'drive.google', 'lh3.googleusercontent']):
                links.add(response.url)
            
            # Parse with BeautifulSoup for better link extraction
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract from all link attributes
            for tag in soup.find_all(['a', 'button']):
                href = tag.get('href', '')
                if href and href.startswith('http'):
                    if any(x in href.lower() for x in ['googleusercontent', 'drive.google', 'lh3.googleusercontent']):
                        links.add(href)
            
            # Extract from HTML content with regex
            matches = re.findall(r'https?://[^\s"\'<>{}|\\^`\[\]]{20,}', response.text)
            for m in matches:
                if any(x in m.lower() for x in ['googleusercontent', 'video-downloads.googleusercontent', 'drive.google']):
                    m = m.split('"')[0].split("'")[0].split('\\')[0]
                    if m.startswith('http') and len(m) > 30:
                        links.add(m)
            
            if links:
                print(f"[INFO] HTTP resolved {len(links)} direct link(s)")
                return list(links)
            else:
                print(f"[WARNING] No direct links found via HTTP")
                return []
                
        except Exception as e:
            print(f"[ERROR] HTTP resolution failed: {e}")
            traceback.print_exc()
            return []

    def _resolve_single(self, item, is_series=False):
        """Resolve single download item without Selenium"""
        short_url = item["url"]
        main_episode = item.get("episode", "EP01")
        main_quality = item.get("quality", "unknown")
        show_name = item.get("show_name", "Unknown")
        season = item.get("season", "02")
        main_size = item.get("size", "unknown")

        start_resolve = time.time()
        print(f"[INFO] Resolving link ({main_quality} | {main_episode} | {main_size})")
        
        resolved_links = self._resolve_shortener(short_url)
        
        all_resolved = []
        for link in resolved_links:
            all_resolved.append({
                "show_name": show_name,
                "season": season,
                "episode": main_episode,
                "quality": main_quality,
                "size": main_size,
                "url": link
            })

        print(f"[INFO] Resolved in {time.time() - start_resolve:.2f}s")
        return all_resolved

    def scrape(self, url, quality_filter=None):
        """Main scraping function with hybrid Selenium + CloudScraper approach"""
        start_time = time.time()

        if quality_filter:
            print(f"[INFO] Quality filter: {quality_filter}")

        # Try to initialize Selenium driver for shortener resolution
        if SELENIUM_AVAILABLE:
            print(f"[INFO] Initializing Selenium for shortener resolution...")
            self.driver = self._create_selenium_driver()
            if self.driver:
                print(f"[INFO] Selenium driver ready")
            else:
                print(f"[WARNING] Selenium driver failed - will use HTTP fallback")

        try:
            html = self._fetch_page(url, driver=self.driver)
            if not html:
                print("[ERROR] Failed to fetch page")
                return []

            short_links = self.get_links(html, url, url)

            if not short_links:
                print("[ERROR] No shortener links found on page")
                return []

            if quality_filter:
                norm_quality = self._normalize_quality(quality_filter)
                filtered_links = [
                    lnk for lnk in short_links
                    if self._normalize_quality(lnk.get('quality', 'unknown')) == norm_quality
                ]
                if not filtered_links:
                    print(f"[WARNING] No links matching quality '{quality_filter}'")
                    return []
                short_links = filtered_links[:1]
                print(f"[INFO] Quality filter applied - 1 link selected")

            url_lower = url.lower()
            is_series = any(k in url_lower for k in ["season", "ep-", "episode", "s0", "s1", "s2"])
            print(f"[INFO] Page type: {'SERIES' if is_series else 'MOVIE'}")

            results = []
            if short_links:
                print(f"[INFO] Resolving {len(short_links)} shortener link(s)...")
                for item in short_links:
                    resolved = self._resolve_single(item, is_series)
                    results.extend(resolved)

            unique = {}
            for r in results:
                key = (r["url"], r.get("episode"), r["quality"], r["size"])
                if key not in unique:
                    unique[key] = r

            total_time = time.time() - start_time
            print(f"[INFO] Scraping completed in {total_time:.2f}s\n")
            return list(unique.values())

        except Exception as e:
            print(f"[ERROR] Scraping exception: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        finally:
            # Cleanup Selenium driver
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None


def scrape_website(url, quality_filter=None):
    """Main entry point for bot integration - Hybrid Selenium + CloudScraper"""
    print("\n[INFO] ========== STARTING SCRAPER ==========")
    print(f"[INFO] URL: {url}")
    if SELENIUM_AVAILABLE:
        print(f"[INFO] Mode: Selenium + CloudScraper (Hybrid)")
    else:
        print(f"[INFO] Mode: CloudScraper + HTTP Fallback")
    if quality_filter:
        print(f"[INFO] Quality filter: {quality_filter}")
    print("[INFO] =======================================\n")
    
    scraper = VegamoviesScraper()
    try:
        print(f"[INFO] Step 1: Fetching page content...")
        results = scraper.scrape(url, quality_filter=quality_filter)
        
        if results:
            print(f"\n[INFO] ========== SCRAPER COMPLETED ==========")
            print(f"[SUCCESS] Found {len(results)} direct download link(s)")
            print(f"[INFO] Preparing for download...")
            print(f"[INFO] ==========================================\n")
            
            # Log found links
            for i, result in enumerate(results, 1):
                print(f"[{i}] {result.get('quality', 'unknown')} | {result.get('size', 'unknown')} | {result['url'][:80]}...")
            
            return results
        else:
            print(f"\n[ERROR] No direct download links found from scraper")
            print(f"[INFO] Possible causes:")
            print(f"[INFO]  - Shortener links could not be resolved")
            print(f"[INFO]  - No Google Drive links found on the page")
            print(f"[INFO]  - Quality filter may be too restrictive")
            print(f"[INFO] ==========================================\n")
            return []
    
    except Exception as e:
        print(f"\n[ERROR] Scraping failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print(f"[INFO] ==========================================\n")
        return []
