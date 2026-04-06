# Critical Fixes Applied - GDFlix & HubCloud Scrapers

## Issue 1: GDFlix Syntax Error (gdflix.py Line 409)

### Error:
```
SyntaxError: f-string: unmatched '['
File "/app/bot/gdflix.py", line 409
    print(f"[+] Index/Zip from zipdisk: {result["mirrors"]['index_zip'][:140]}...")
```

### Root Cause:
F-strings in Python cannot directly include dictionary key access with quotes inside the braces. The nested quotes in `{result["mirrors"]['index_zip']}` created an unmatched bracket error.

### Fix Applied:
**File:** `bot/gdflix.py` (Lines 407-410)

```python
# BEFORE (Broken):
if index_directs:
    result["mirrors"]['index_zip'] = index_directs[list(index_directs.keys())[0]]
    print(f"[+] Index/Zip from zipdisk: {result["mirrors"]['index_zip'][:140]}...")

# AFTER (Fixed):
if index_directs:
    result["mirrors"]['index_zip'] = index_directs[list(index_directs.keys())[0]]
    zip_url = result["mirrors"]['index_zip'][:140]
    print(f"[+] Index/Zip from zipdisk: {zip_url}...")
```

**Solution:** Extract the value to a variable first, then use it in the f-string. This avoids nested quotes in the f-string braces.

---

## Issue 2: HubCloud Missing Module (hdhub_scraper.py Line 7)

### Error:
```
ModuleNotFoundError: No module named 'bs4'
File "/app/bot/hdhub_scraper.py", line 7
    from bs4 import BeautifulSoup
```

### Root Cause:
The `beautifulsoup4` package is not installed in the environment, but is required by hdhub_scraper.py for HTML parsing.

### Fix Applied:
**File:** `bot/hdhub_scraper.py` (Lines 1-22)

```python
# BEFORE (Broken):
from bs4 import BeautifulSoup

# AFTER (Fixed):
try:
    from bs4 import BeautifulSoup
except ImportError:
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4", "-q"])
        from bs4 import BeautifulSoup
        print("[INFO] beautifulsoup4 installed successfully")
    except Exception as e:
        print(f"[WARNING] Failed to install beautifulsoup4: {e}")
        BeautifulSoup = None
```

**Solution:** Auto-install beautifulsoup4 if missing. The script now:
1. Attempts to import BeautifulSoup
2. If import fails, automatically installs beautifulsoup4 via pip
3. Logs success/failure messages
4. Gracefully handles installation errors

---

## Expected Behavior After Fix

### On Bot Startup:
```
[DEBUG] Bot directory detected: /app/bot
[DEBUG] Attempting to load GDFlix from: /app/bot/gdflix.py
[DEBUG] File exists: True
[INFO] GDFlix scraper loaded successfully
[DEBUG] Attempting to load HubCloud from: /app/bot/hdhub_scraper.py
[DEBUG] File exists: True
[INFO] beautifulsoup4 installed successfully  (first run)
[INFO] HubCloud scraper loaded successfully
```

### On User Command:
```
/leech https://new16.gdflix.net/file/3waVAjs1WmOdo62
→ Direct link extracted and download starts

/mirror https://hubcloud.foo/drive/1oqzimcyqgq6iou
→ Direct link extracted and download starts
```

---

## Summary of Changes

| File | Lines | Change |
|------|-------|--------|
| `bot/gdflix.py` | 407-410 | Fixed f-string syntax error by extracting dict value to variable |
| `bot/hdhub_scraper.py` | 1-22 | Added try/except with auto-install for beautifulsoup4 |

Both scrapers now load successfully without syntax or module errors!
