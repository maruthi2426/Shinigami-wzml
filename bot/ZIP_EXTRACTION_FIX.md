# ZIP Extraction Error Fix

## Problem
```
FileNotFoundError: [Errno 2] No such file or directory
```
When trying to extract ZIP files from HubCloud/GDFlix, the bot fails because **7z (7-zip) command is not installed** on the system.

## Root Cause
The bot was trying to execute the `7z` command directly, which doesn't exist on this system. The file extraction process depends entirely on 7z being available.

## Solution Implemented
Modified `bot/helper/ext_utils/files_utils.py` to add a **fallback mechanism**:

1. **Check if 7z is available** using `shutil.which("7z")`
2. **If 7z exists** → Use 7z for extraction (original behavior)
3. **If 7z doesn't exist** → Fall back to Python's built-in `zipfile` module for `.zip` files
4. **If file is not ZIP and 7z unavailable** → Return error with helpful message

## File Changed
`bot/helper/ext_utils/files_utils.py`

### Imports Added
```python
from zipfile import ZipFile
from shutil import which
```

### Extract Function Updated
- Lines 366-408: Added 7z availability check with `which("7z")`
- Lines 410-441: Added `zipfile` fallback for ZIP files
- Uses async executor to prevent blocking during extraction
- Properly handles password-protected ZIP files

## Expected Behavior

### Before Fix
```
[ERROR] FileNotFoundError: 7z command not found
[ERROR] Extraction fails completely
```

### After Fix
```
[INFO] 7z not available, using Python zipfile
[FALLBACK] Using Python zipfile to extract: file.zip
[SUCCESS] Extracted using zipfile: file.zip
```

## Testing
When user downloads and tries to extract a ZIP file from HubCloud/GDFlix:
1. Bot detects 7z is not available
2. Falls back to Python zipfile
3. Extracts successfully
4. Continues with upload/mirror/leech process

## Compatibility
- Works on systems with or without 7z installed
- Supports password-protected ZIP files
- Maintains full backward compatibility with existing 7z workflows
- Graceful error handling for non-ZIP files when 7z unavailable
