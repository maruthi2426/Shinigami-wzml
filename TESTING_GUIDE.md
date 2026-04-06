# TESTING GUIDE - GDFlix & HubCloud Integration

## QUICK TEST

Send these commands to your bot:

### GDFlix Test:
```
/leech https://new16.gdflix.net/file/YOUR_FILE_ID
```
Expected result: Bot detects gdflix.net domain → calls gdflix() → extracts mirrors → starts leech with Instant DL link

### HubCloud Test:
```
/mirror https://hubcloud.foo/file/YOUR_FILE_ID
```
Expected result: Bot detects hubcloud.foo domain → calls hubcloud_handler() → extracts FSL Server → starts mirror

---

## WHAT HAPPENS INTERNALLY

### For GDFlix:
1. URL arrives at bot
2. `direct_link_generator()` detects `gdflix.net` in domain
3. Calls `gdflix(link)` function
4. Function calls `get_gdflix_data(link, [])`
5. Scraper:
   - Fetches landing page
   - Extracts all download buttons
   - Follows redirects for Instant DL (busycdn → direct GD)
   - Returns JSON with all mirrors
6. Handler selects priority mirror (Instant DL first)
7. Returns direct download link to bot
8. Bot starts download/leech with that link

### For HubCloud:
1. URL arrives at bot
2. `direct_link_generator()` detects `hubcloud.foo` in domain
3. Calls `hubcloud_handler(link)` function
4. Function calls `bypass_hubcloud(link, session)`
5. Scraper:
   - Sends bypass request
   - Extracts FSL Server or 10Gbps Server link
   - Returns dict with server URLs
6. Handler selects best server (FSL first)
7. Returns direct download link to bot
8. Bot starts immediate download

---

## EXPECTED BEHAVIOR

### Success Case - GDFlix:
```
[User] /leech https://new16.gdflix.net/file/abc123

[Bot Log]
Running Pre Task Checks ...
Fetching landing page...
Landing status: 200
Parsed filename: Example.Movie.1080p
Parsed filesize: 3.5 GB
Scraping landing page for download buttons...
[+] instant button direct: https://busycdn.xyz/...
[+] Instant DL replaced with direct GD: https://googleusercontent.com/...
[INFO] Direct link found: https://googleusercontent.com/...
[INFO] Starting Aria2Download...
onDownloadStarted - Gid: xxxxx
Download started: example_movie_1080p
```

### Success Case - HubCloud:
```
[User] /mirror https://hubcloud.foo/file/xyz789

[Bot Log]
Running Pre Task Checks ...
[INFO] Processing HubCloud link...
Bypassing protection...
[+] FSL Server found: https://fsl-server.com/...
[INFO] Direct link found: https://fsl-server.com/...
[INFO] Starting leech...
Leech started successfully
```

---

## ERROR CASES

### If GDFlix scraper not found:
```
ERROR: No Direct link function found for https://new16.gdflix.net/file/...
```
→ Make sure `gdflix.py` is in `/bot/` directory

### If no mirrors extracted:
```
ERROR: GDFlix - No usable GDFlix mirror found
```
→ The file might be deleted or the domain is blocked
→ Try with a different file or check internet connection

### If HubCloud link is invalid:
```
ERROR: HubCloud - Invalid link format
```
→ Check that the link is complete and correct format

---

## DEBUGGING

If something goes wrong, check:

1. **Bot logs** - Look for `[ERROR]` messages
2. **Module imports** - Check if gdflix.py and hdhub_scraper.py are in `/bot/` 
3. **Domain detection** - Ensure the URL contains recognized domain
4. **Scraper errors** - The error message will contain details

---

## MONITORING

Watch for these indicators:

✅ Working correctly:
- `[+]` messages in logs = successful extraction
- Direct link returned = processing success
- Leech/Mirror starts = link is valid

❌ Not working:
- `No Direct link function found` = domain not detected
- `No mirrors found` = scraper couldn't extract
- `ERROR:` messages = something failed

---

## REQUIREMENTS

These must be installed in bot environment:
- `curl_cffi` - Browser emulation (GDFlix needs this)
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP requests (for HubCloud session)
- `lxml` - HTML parser backend

Install with:
```bash
pip install curl_cffi beautifulsoup4 requests lxml
```

---

## NOTES

- **First link only**: If user sends 2 GDFlix links, only the first is processed
- **Timeout**: Each scraper has 15-20 second timeout
- **Proxies**: Optional, bot works without proxies
- **Retries**: GDFlix retries 5 times, HubCloud uses direct approach
- **Quota errors**: Handled gracefully with fallback mirrors

---

## SUCCESS INDICATORS

You'll know it's working when:
1. GDFlix links start downloading with Instant DL (fastest)
2. HubCloud links start downloading with FSL Server (fastest)
3. No more "No Direct link function found" errors
4. Bot extracts mirrors instead of throwing errors
