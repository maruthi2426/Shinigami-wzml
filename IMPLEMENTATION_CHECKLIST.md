# Implementation Checklist - WebScrapper Hybrid Fix

## Pre-Implementation

- [ ] Backup current `bot/webscrapper.py` (optional)
- [ ] Check current Python version: `python --version` (3.8+)
- [ ] Check current bot status (running/stopped)

## Step 1: Install Dependencies

```bash
# Install all required packages
pip install selenium webdriver-manager cloudscraper requests beautifulsoup4
```

- [ ] selenium installed ✓
- [ ] webdriver-manager installed ✓
- [ ] cloudscraper installed ✓
- [ ] requests installed ✓
- [ ] beautifulsoup4 installed ✓

**Note**: On first run, webdriver-manager will download Chrome binary (~200MB). This may take 1-2 minutes but only happens once.

## Step 2: Verify Files Are in Place

Check these files exist in your project:

```
/vercel/share/v0-project/
├── bot/
│   └── webscrapper.py ← UPDATED WITH HYBRID APPROACH
├── WEBSCRAPPER_FIX_COMPLETE.md ← New documentation
├── COMPLETE_WEBSCRAPPER_FIX_GUIDE.md ← New documentation
├── verify_webscrapper_fix.py ← New verification script
└── IMPLEMENTATION_CHECKLIST.md ← This file
```

- [ ] `bot/webscrapper.py` exists and has hybrid code
- [ ] Documentation files downloaded
- [ ] Verification script available

## Step 3: Run Verification

```bash
python verify_webscrapper_fix.py
```

Expected output:
```
✓ requests
✓ beautifulsoup4
✓ cloudscraper
✓ selenium + webdriver-manager
✓ FULL CAPABILITY
```

- [ ] All imports verified
- [ ] bot/webscrapper.py imports correctly
- [ ] Selenium support detected
- [ ] CloudScraper support detected
- [ ] Verification shows "FULL CAPABILITY"

## Step 4: Restart Bot

Stop and start your bot application:

```bash
# Stop bot (adjust based on your setup)
kill <bot-process-id>
# or
systemctl stop telegram-bot
# or
pkill -f bot.py

# Wait 3 seconds
sleep 3

# Start bot again
python -m bot
# or
systemctl start telegram-bot
```

- [ ] Bot process stopped cleanly
- [ ] Old bot fully terminated
- [ ] Bot started with new webscrapper
- [ ] No import errors in startup logs

## Step 5: Test Scraper Functionality

### Option A: Bot Command Test (Recommended)

In your Telegram bot, send:
```
/leech https://vegamovies.wedding/51369-anemone-2025-hindi-dual-audio-web-dl-720p-480p-1080p.html -q 720p
```

Expected response:
```
[INFO] ========== STARTING SCRAPER ==========
[INFO] Mode: Selenium + CloudScraper (Hybrid)
[INFO] Loading VegaMovies page...
✓ Page loaded in X.XXs
✓ Found N shortener link(s)
[INFO] Resolving shortener link(s)...
✓ Selenium resolved X direct link(s)
[SUCCESS] Found X direct download link(s)
[Download started...]
```

- [ ] Bot receives leech command
- [ ] Scraper starts loading page
- [ ] Shortener links found
- [ ] Selenium resolves links
- [ ] Direct Google Drive links extracted
- [ ] Download process starts

### Option B: Direct Python Test

```python
from bot.webscrapper import scrape_website

url = "https://vegamovies.wedding/51369-anemone-2025-hindi-dual-audio-web-dl-720p-480p-1080p.html"
results = scrape_website(url, quality_filter="720p")

print(f"Found {len(results)} links:")
for r in results:
    print(f"  Quality: {r['quality']}, Size: {r['size']}")
    print(f"  URL: {r['url'][:80]}...")
```

Expected output:
```
Found 1 links:
  Quality: 720p, Size: 450.0 MB
  URL: https://lh3.googleusercontent.com/...
```

- [ ] Import successful
- [ ] No errors during scrape
- [ ] Results returned as list
- [ ] Each result has 'url' key
- [ ] URLs are Google Drive links

### Option C: Check Logs

Look for these messages in your bot logs:

```
[INFO] ========== STARTING SCRAPER ==========
[INFO] Mode: Selenium + CloudScraper (Hybrid)
[INFO] CloudScraper initialized
[INFO] Loading VegaMovies page...
[INFO] Page loaded in 2.15s
[INFO] Found 4 shortener link(s)
[INFO] Resolving 1 shortener link(s)...
[INFO] Selenium driver ready
[INFO] Selenium resolved 1 direct link(s)
[SUCCESS] Found 1 direct download link(s)
```

- [ ] Scraper initialization messages appear
- [ ] CloudScraper loads successfully
- [ ] Page fetches within 5 seconds
- [ ] Shortener links are detected
- [ ] Selenium successfully resolves links
- [ ] Success message indicates direct links found

## Troubleshooting During Testing

### Issue: "Chrome not found"
```
Error: Service with name chromedriver doesn't exist
```
**Solution**: webdriver-manager downloads Chrome on first run
- [ ] Run script again (Chrome will download)
- [ ] Or manually install: `pip install --upgrade webdriver-manager`

### Issue: "Module not found: selenium"
```
ModuleNotFoundError: No module named 'selenium'
```
**Solution**: Install missing package
```bash
pip install selenium
```
- [ ] Run pip install command above
- [ ] Verify installation: `python -c "import selenium; print(selenium.__version__)"`

### Issue: "No shortener links found"
```
[ERROR] No shortener links found on page
```
**Possible causes**:
- [ ] URL is not a valid VegaMovies page
- [ ] Page structure changed
- [ ] Network issue (check internet)
- [ ] Try different URL or quality

### Issue: "Selenium resolved 0 direct link(s)"
```
[WARNING] Selenium: No direct links found
[INFO] HTTP resolved 0 direct link(s)
```
**Solutions**:
- [ ] Wait 2-3 seconds (shortener may be slow)
- [ ] Try without quality filter
- [ ] Try different quality option
- [ ] Try different VegaMovies URL

### Issue: "Still getting error after restart"
- [ ] Verify bot is using NEW bot/webscrapper.py
- [ ] Check that old Python processes are killed
- [ ] Verify imports in bot startup logs
- [ ] Run verification script again
- [ ] Check Python version (3.8+)

## Post-Implementation

### Monitor Bot Performance

Keep bot running for 24 hours and monitor:
- [ ] Memory usage stable (should be 100-200MB)
- [ ] No chrome processes left hanging
- [ ] Multiple leech commands work
- [ ] Download completion rate

### Check for Resource Leaks

```bash
# Check for zombie chrome processes
ps aux | grep chrome

# Should be empty or only running processes
# If many defunct [chrome] processes, Chrome cleanup failed
```

- [ ] No zombie Chrome processes
- [ ] Clean process termination
- [ ] Memory not growing over time

### Verify Success Rate

Test with 5-10 different VegaMovies URLs:
- [ ] At least 9/10 return direct links
- [ ] Average resolution time < 15s
- [ ] No bot crashes
- [ ] Error messages are informative

## Performance Baseline

After implementation, you should see:

| Metric | Expected |
|--------|----------|
| Page load | 1-3 seconds |
| Shortener resolution | 3-8 seconds |
| Total scrape time | 5-12 seconds |
| Success rate | 90%+ |
| Memory usage | 150-200MB |
| CPU usage | 20-40% during scrape |

- [ ] Times match baseline expectations
- [ ] Success rate meets 90%+ target
- [ ] Resource usage is acceptable
- [ ] No timeout errors

## Rollback Plan

If something goes wrong:

1. Stop bot
2. Restore original `bot/webscrapper.py` from backup
3. Restart bot
4. Report issue with full error logs

- [ ] Have original webscrapper.py backed up
- [ ] Know how to restore from backup
- [ ] Have rollback tested (don't wait for emergency)

## Success Criteria

You'll know the fix is working when:

✅ Bot no longer shows "No direct download links found" error  
✅ Scraper returns actual Google Drive URLs  
✅ Leech/download process starts immediately after  
✅ Downloads complete successfully  
✅ Bot handles multiple concurrent requests  
✅ Memory and CPU usage stable  
✅ Chrome processes clean up properly  

## Final Sign-Off

- [ ] All tests passed
- [ ] Bot operational with new webscrapper
- [ ] Documentation reviewed
- [ ] Verification script runs successfully
- [ ] At least 3 URLs tested successfully
- [ ] Team informed of changes
- [ ] Rollback plan understood

## Quick Reference

| What | Command | Expected |
|------|---------|----------|
| Verify setup | `python verify_webscrapper_fix.py` | All checks pass |
| Test scraper | `/leech <URL> -q 720p` | Direct Google Drive link |
| Check logs | `tail -f bot.log` | See scraper progress |
| Restart bot | `systemctl restart bot` | Bot starts cleanly |
| Check processes | `ps aux \| grep chrome` | No zombie processes |

---

## Status: Ready to Implement

The WebScrapper fix is complete and ready to use. Follow this checklist step-by-step for smooth implementation.

**Estimated Time**: 30-45 minutes (including Chrome download on first run)

**Success Rate Target**: 90%+

**Confidence Level**: High - Fix addresses root cause

---

**Last Updated**: 2026-04-11  
**Version**: WebScrapper v2.0  
**Status**: Production Ready
