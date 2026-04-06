# GDFLIX & HUBCLOUD FIX - CHANGES SUMMARY

## FILES MODIFIED/ADDED

### 1. **ADDED FILES:**

#### `/bot/gdflix.py`
- Complete GDFlix scraper module
- Detects and extracts mirrors: Instant DL, Pixeldrain, Cloud R2, Index/Zip, Telegram, GoFile
- Handles both single file and pack URLs
- Follows redirects, strips proxies, extracts direct download links

#### `/bot/hdhub_scraper.py`
- Complete HubCloud bypasser module
- Extracts FSL Server and 10Gbps Server links
- Handles multiple download formats and quality options

---

### 2. **MODIFIED FILE:**

#### `/bot/helper/mirror_leech_utils/download_utils/direct_link_generator.py`

**Lines 22-32:** Added imports
```python
try:
    from gdflix import get_gdflix_data
except ImportError:
    get_gdflix_data = None

try:
    from hdhub_scraper import bypass_hubcloud
except ImportError:
    bypass_hubcloud = None
```

**Lines 40-115:** Added two new handler functions

1. **`gdflix(link)`** - GDFlix direct link generator
   - Priority: Instant DL > Pixeldrain > Cloud R2 > Index Zip
   - Handles both single files and packs
   - Returns first available mirror if priority ones fail

2. **`hubcloud_handler(link)`** - HubCloud direct link generator
   - Priority: FSL Server > 10Gbps Server > Pixeldrain
   - Uses session management for proper cookies/headers
   - Extracts best quality links first

**Lines 238-241:** Added domain detection in `direct_link_generator()` function
```python
elif any(x in domain for x in ["gdflix.net", "gdflix.cc", "gdflix.ml"]):
    return gdflix(link)
elif any(x in domain for x in ["hubcloud.foo", "hubcloud.one", "hubcloud.cc", "hubcloud.net"]):
    return hubcloud_handler(link)
```

**Line 483:** Updated old `hubcloud()` function docstring (kept as fallback)

---

## HOW IT WORKS

### When User Sends GDFlix Link:
1. Bot detects `gdflix.net`, `gdflix.cc`, or `gdflix.ml` in URL
2. Calls `gdflix()` handler → calls `get_gdflix_data()`
3. Scraper fetches landing page, extracts all mirrors
4. Returns priority mirror (Instant DL first)
5. Bot starts leech/mirror with that link

### When User Sends HubCloud Link:
1. Bot detects `hubcloud.foo`, `hubcloud.one`, etc. in URL
2. Calls `hubcloud_handler()` → calls `bypass_hubcloud()`
3. Scraper bypasses protection, extracts server links
4. Returns FSL or 10Gbps Server link
5. Bot starts download immediately

### Multiple Links Handling:
- Bot processes **first valid link** in message
- Other links are ignored
- Only one download starts at a time

---

## FEATURES

✅ **GDFlix:**
- Instant DL with CDN acceleration (10GBPS)
- Pixeldrain backup (20MB/s)
- Cloud R2 storage mirrors
- Index/Zip file extraction
- Pack episodes support

✅ **HubCloud:**
- FSL Server (fastest priority)
- 10Gbps Server (backup)
- Pixeldrain fallback
- Proper session cookies
- Error handling

✅ **General:**
- Both scrapers work without API keys
- Proxy support (optional)
- Timeout handling
- Exception logging
- Fallback mechanisms

---

## ERROR HANDLING

- If scraper module not found → "ERROR: GDFlix scraper not installed"
- If no mirrors found → "ERROR: No usable [service] mirror found"
- If URL is invalid → "ERROR: [service] - [detailed error]"
- If all attempts fail → Returns error message to user

---

## TESTING

To test manually:
```bash
# Test GDFlix
python -c "from gdflix import get_gdflix_data; print(get_gdflix_data('https://new16.gdflix.net/file/...', []))"

# Test HubCloud
python -c "from hdhub_scraper import bypass_hubcloud; import requests; s = requests.Session(); print(bypass_hubcloud('https://hubcloud.foo/file/...', s))"
```

---

## NOTES

- Scrapers use curl_cffi for browser emulation (Chrome 110)
- BeautifulSoup for HTML parsing
- No additional API keys required
- Safe to use - only extracting links, not downloading directly
- Can handle quota errors gracefully
