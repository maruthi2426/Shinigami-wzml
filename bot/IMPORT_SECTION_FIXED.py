# ═══════════════════════════════════════════════════════════════════════════
#  COMPLETE FIXED IMPORT SECTION FOR direct_link_generator.py
#  Lines 1-70 (IMPORTS + SCRAPER LOADING)
# ═══════════════════════════════════════════════════════════════════════════

from cloudscraper import create_scraper
from hashlib import sha256
from http.cookiejar import MozillaCookieJar
from json import loads
from lxml.etree import HTML
from os import path as ospath
from re import findall, match, search
from requests import Session, post, get, RequestException
from requests.adapters import HTTPAdapter
from time import sleep, time
from urllib.parse import parse_qs, urlparse, quote
from urllib3.util.retry import Retry
from uuid import uuid4
from base64 import b64decode, b64encode
import sys
from pathlib import Path
import importlib.util
import os

from ....core.config_manager import Config
from ...ext_utils.exceptions import DirectDownloadLinkException
from ...ext_utils.help_messages import PASSWORD_ERROR_MESSAGE
from ...ext_utils.links_utils import is_share_link
from ...ext_utils.status_utils import speed_string_to_bytes

# ═══════════════════════════════════════════════════════════════════════════
# SCRAPER LOADING - Using importlib for reliable file-based imports
# ═══════════════════════════════════════════════════════════════════════════

GDFLIX_AVAILABLE = False
HUBCLOUD_AVAILABLE = False
get_gdflix_data = None
bypass_hubcloud = None

# Get bot directory path
bot_dir = str(Path(__file__).parent.parent.parent.parent)

# Try to load gdflix scraper
gdflix_path = os.path.join(bot_dir, 'gdflix.py')
if os.path.exists(gdflix_path):
    try:
        spec = importlib.util.spec_from_file_location("gdflix", gdflix_path)
        gdflix_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gdflix_module)
        get_gdflix_data = gdflix_module.get_gdflix_data
        GDFLIX_AVAILABLE = True
        print(f"[INFO] GDFlix scraper loaded successfully from {gdflix_path}")
    except Exception as e:
        print(f"[ERROR] Failed to load GDFlix scraper: {str(e)}")
        GDFLIX_AVAILABLE = False
else:
    print(f"[WARNING] GDFlix scraper not found at {gdflix_path}")

# Try to load hdhub_scraper
hdhub_path = os.path.join(bot_dir, 'hdhub_scraper.py')
if os.path.exists(hdhub_path):
    try:
        spec = importlib.util.spec_from_file_location("hdhub_scraper", hdhub_path)
        hdhub_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hdhub_module)
        bypass_hubcloud = hdhub_module.bypass_hubcloud
        HUBCLOUD_AVAILABLE = True
        print(f"[INFO] HubCloud scraper loaded successfully from {hdhub_path}")
    except Exception as e:
        print(f"[ERROR] Failed to load HubCloud scraper: {str(e)}")
        HUBCLOUD_AVAILABLE = False
else:
    print(f"[WARNING] HubCloud scraper not found at {hdhub_path}")

# GoFile token cache to avoid rate limiting
gofile_token_cache = None

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
)

# ═══════════════════════════════════════════════════════════════════════════
# END OF IMPORT SECTION
# ═══════════════════════════════════════════════════════════════════════════
