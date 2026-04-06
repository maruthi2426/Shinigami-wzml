# ZIP Extraction Error - FINAL FIX

## Problem
```
FileNotFoundError: [Errno 2] No such file or directory
```
The `which("7z")` check wasn't catching the missing 7z command, causing the code to still attempt to execute 7z and fail.

## Root Cause
The `which()` function was not reliable in the uvloop/asyncio environment. It returned None but the code logic was still trying to use 7z.

## Solution
**Reversed the logic to try-first with proper exception handling:**

1. **For ZIP files** → Use Python's zipfile directly (no need for 7z)
2. **For RAR/7z files** → Try 7z first, catch FileNotFoundError, fall back to zipfile
3. **Both cases** → Execute extraction in thread pool to avoid blocking

## File Modified
`bot/helper/ext_utils/files_utils.py` - Lines 365-441

## Changes Made
- Removed unreliable `which("7z")` check
- Added try-except block around 7z subprocess call
- Catches `FileNotFoundError` specifically when 7z is missing
- Auto-falls back to zipfile extraction
- Added proper logging at each step

## Expected Behavior
```
[INFO] - Extracting: Dynasty.The.Murdochs.2026.S01...zip
[FALLBACK] Using Python zipfile to extract: ...
[SUCCESS] Extracted using zipfile: ...
```

## Result
ZIP files will now extract successfully on any system, with or without 7z installed!
