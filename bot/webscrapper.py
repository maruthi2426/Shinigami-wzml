import re
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


class VegamoviesScraper:
    def __init__(self):
        pass

    def _create_driver(self, fast_mode=False):
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
        options.add_argument("--disable-features=Translate,OptimizationHints,MediaRouter,NetworkService,IsolateOrigins,site-per-process")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-breakpad")
        options.add_argument("--log-level=3")
        options.add_argument("--single-process")
        options.page_load_strategy = "eager"

        if fast_mode:
            options.add_argument("--disable-webgl")
            options.add_argument("--disable-3d-apis")
            options.add_argument("--disable-plugins")

        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        })
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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

    def _fetch_with_driver(self, url, driver, fast_mode=False):
        print("[INFO] Loading VegaMovies page (single driver)")
        start = time.time()
        driver.get(url)

        scrolls = 2 if fast_mode else 3
        for _ in range(scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.12 if fast_mode else 0.22)

        time.sleep(0.6 if fast_mode else 0.9)
        html = driver.page_source
        print(f"[INFO] Page loaded in {time.time() - start:.2f}s")
        return html

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

    def _resolve_single(self, item, driver, is_series=False, fast_mode=False):
        short_url = item["url"]
        main_episode = item.get("episode", "EP01")
        main_quality = item.get("quality", "unknown")
        show_name = item.get("show_name", "Unknown")
        season = item.get("season", "02")
        main_size = item.get("size", "unknown")

        start_resolve = time.time()
        sleep_time = 0.08 if fast_mode else 0.25
        verify_wait = 1.0 if fast_mode else 2.0
        verify_sleep = 0.35 if fast_mode else 0.9
        timeout_sleep = 0.7 if fast_mode else 1.4

        print(f"[INFO] Bypassing Nexdrive ({main_quality} | {main_episode} | {main_size})")
        driver.get(short_url)
        time.sleep(sleep_time)

        next_shorteners = []
        try:
            for el in driver.find_elements(By.TAG_NAME, "a"):
                href = el.get_attribute("href") or ""
                if href and "fast-dl.org" in href.lower():
                    a_text = el.get_attribute("innerText") or el.text or ""
                    sub_episode = self._extract_episode(a_text, href)
                    if sub_episode == "unknown":
                        sub_episode = main_episode
                    next_shorteners.append((href, sub_episode))
        except:
            pass

        if not next_shorteners:
            next_shorteners = [(short_url, main_episode)]

        if not is_series:
            next_shorteners = [next_shorteners[0]] if next_shorteners else []

        all_resolved = []
        for idx, (next_url, sub_episode) in enumerate(next_shorteners, 1):
            if len(next_shorteners) > 1 or is_series:
                print(f"[INFO] Resolving fast-dl {idx}/{len(next_shorteners)} [{sub_episode}]")

            driver.get(next_url)
            time.sleep(sleep_time)

            try:
                verify_btn = WebDriverWait(driver, verify_wait).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'verify')] | "
                        "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'verify')]"
                    ))
                )
                driver.execute_script("arguments[0].click();", verify_btn)
                time.sleep(verify_sleep)
            except TimeoutException:
                time.sleep(timeout_sleep)

            links = set()
            for el in driver.find_elements(By.TAG_NAME, "a"):
                try:
                    href = el.get_attribute("href")
                    if href and href.startswith("http") and not any(x in href.lower() for x in ["nexdrive", "fast-dl", "vgmlinks", "tinyurl", "t.me"]):
                        links.add(href)
                except:
                    continue

            html = driver.page_source
            matches = re.findall(r'https?://[^\s"\'<>]+', html)
            for m in matches:
                if any(x in m.lower() for x in ["googleusercontent", "video-downloads.googleusercontent"]):
                    links.add(m)

            for link in links:
                all_resolved.append({
                    "show_name": show_name,
                    "season": season,
                    "episode": sub_episode,
                    "quality": main_quality,
                    "size": main_size,
                    "url": link
                })

        print(f"[INFO] Resolved in {time.time() - start_resolve:.2f}s")
        return all_resolved

    def scrape(self, url, quality_filter=None):
        start_time = time.time()
        fast_mode = bool(quality_filter)

        if quality_filter:
            print(f"[INFO] QUALITY MODE: Targeting '{quality_filter}'")

        driver = self._create_driver(fast_mode=fast_mode)
        try:
            html = self._fetch_with_driver(url, driver, fast_mode)
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
                    resolved = self._resolve_single(item, driver, is_series, fast_mode=fast_mode)
                    results.extend(resolved)

            unique = {}
            for r in results:
                key = (r["url"], r.get("episode"), r["quality"], r["size"])
                if key not in unique:
                    unique[key] = r

            total_time = time.time() - start_time
            print(f"[INFO] Scraping completed in {total_time:.2f}s\n")
            return list(unique.values())

        finally:
            driver.quit()


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
