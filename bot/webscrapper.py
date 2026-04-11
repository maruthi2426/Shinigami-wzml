import re
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Use cloudscraper instead of Selenium for lightweight cloud compatibility
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("[WARNING] cloudscraper not installed, using requests fallback")


class VegamoviesScraper:
    def __init__(self):
        self.scraper = None
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

    def _fetch_page(self, url):
        """Fetch page using cloudscraper or requests (no Selenium needed)"""
        print("[INFO] Loading VegaMovies page...")
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

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'div', 'p', 'span', 'a']):
            text = element.get_text(" ", strip=True)
            quality_match = re.search(r'(480p|720p|1080p|4k|2160p|HQ 1080p)\s*(?:x264|x265|HEVC)?', text, re.I)
            if quality_match:
                current_quality = self._normalize_quality(quality_match.group(0))
                size_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', text, re.I)
                if size_match:
                    current_size = size_match.group(0).upper()
                continue

            if element.name == "a" and element.has_attr("href"):
                href = urljoin(base, element["href"])
                full_text = element.get_text(" ", strip=True)
                if any(x in href.lower() for x in ["nexdrive", "fast-dl.org"]):
                    size_match = re.search(r'(\d+\.?\d*)\s*(GB|MB)', full_text + " " + text, re.I)
                    size = size_match.group(0).upper() if size_match else current_size
                    episode = self._extract_episode(full_text, href)
                    if episode == "unknown":
                        episode = page_episode
                    links.append({
                        "url": href,
                        "size": size,
                        "quality": current_quality,
                        "episode": episode,
                        "show_name": show_name,
                        "season": season
                    })

        print(f"[INFO] Found {len(links)} short links")
        return links

    def _resolve_shortener(self, short_url):
        """Resolve shortener to direct link"""
        try:
            print(f"[INFO] Resolving shortener: {short_url[:60]}...")
            response = self.scraper.get(short_url, allow_redirects=True, timeout=15)
            
            # Extract direct Google Drive links from HTML
            links = set()
            
            # Check final URL
            if 'googleusercontent' in response.url.lower():
                links.add(response.url)
            
            # Extract from HTML
            matches = re.findall(r'https?://[^\s"\'<>]+', response.text)
            for m in matches:
                if 'googleusercontent' in m.lower() or 'google.com' in m.lower():
                    # Clean URL
                    m = m.split('"')[0].split("'")[0]
                    if m.startswith('http'):
                        links.add(m)
            
            return list(links) if links else [response.url]
        except Exception as e:
            print(f"[ERROR] Failed to resolve {short_url}: {e}")
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
        """Main scraping function using cloudscraper (no Selenium needed)"""
        start_time = time.time()

        if quality_filter:
            print(f"[INFO] Quality filter: {quality_filter}")

        try:
            html = self._fetch_page(url)
            if not html:
                print("[ERROR] Failed to fetch page")
                return []

            short_links = self.get_links(html, url, url)

            if not short_links:
                print("[ERROR] No shortener links found")
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
                print(f"[INFO] Resolving {len(short_links)} short link(s)...")
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


def scrape_website(url, quality_filter=None):
    """Main entry point for bot integration"""
    print("\n[INFO] ========== STARTING SCRAPER ==========")
    print(f"[INFO] Please wait... Scraping: {url}")
    if quality_filter:
        print(f"[INFO] Quality filter: {quality_filter}")
    print("[INFO] =======================================\n")
    
    scraper = VegamoviesScraper()
    try:
        results = scraper.scrape(url, quality_filter=quality_filter)
        
        if results:
            print(f"[INFO] ========== SCRAPER COMPLETED ==========")
            print(f"[INFO] Found {len(results)} direct download link(s)")
            print(f"[INFO] Preparing for leech/mirror...")
            print(f"[INFO] ==========================================\n")
            return results
        else:
            print(f"[ERROR] No direct download links found")
            return []
    
    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return []
