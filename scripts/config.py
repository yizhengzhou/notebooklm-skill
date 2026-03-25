"""
Configuration for NotebookLM Skill
Centralizes constants, selectors, and paths
"""

from pathlib import Path

# Paths
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"
AUTH_INFO_FILE = DATA_DIR / "auth_info.json"
LIBRARY_FILE = DATA_DIR / "library.json"

# NotebookLM Selectors
QUERY_INPUT_SELECTORS = [
    "textarea.query-box-input",  # Primary
    'textarea[aria-label="Feld für Anfragen"]',  # Fallback German
    'textarea[aria-label="Input for queries"]',  # Fallback English
]

RESPONSE_SELECTORS = [
    ".to-user-container .message-text-content",  # Primary
    "[data-message-author='bot']",
    "[data-message-author='assistant']",
]

# Browser Configuration
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',  # Patches navigator.webdriver
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--no-first-run',
    '--no-default-browser-check'
]

# Additional args when running headless (uses Chrome's new headless mode, more invisible)
HEADLESS_BROWSER_ARGS = BROWSER_ARGS + [
    '--headless=new',
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Notebook Guide Selectors (設定對話 dialog)
GUIDE_TYPE_RADIO_SELECTORS = {
    "default": '[role="radio"][aria-label*="預設"], [role="radio"][aria-label*="Default"]',
    "learning": '[role="radio"][aria-label*="學習指引"], [role="radio"][aria-label*="Learning"]',
    "custom": '[role="radio"][aria-label*="自訂"], [role="radio"][aria-label*="Custom"]',
}

GUIDE_TEXTAREA_SELECTORS = [
    "textarea.custom-input-textarea",
    'textarea[aria-label*="自訂提示"]',
    'textarea[aria-label*="Custom prompt"]',
]

GUIDE_RESPONSE_LENGTH_SELECTORS = {
    "default": 'mat-button-toggle-group:nth-of-type(2) [role="radio"][aria-label*="預設"], [role="radiogroup"]:nth-of-type(2) [role="radio"][aria-label*="Default"]',
    "long": '[role="radio"][aria-label*="詳細"], [role="radio"][aria-label*="Detailed"]',
    "short": '[role="radio"][aria-label*="精簡"], [role="radio"][aria-label*="Concise"]',
}

GUIDE_SUBMIT_SELECTORS = [
    "button.submit-button[type='submit']",
    'button[type="submit"]:has-text("儲存")',
    'button[type="submit"]:has-text("Save")',
]

# Access Denied Detection
# Text patterns that indicate the user is logged into the wrong Google account.
# Uses page text content matching (resilient to DOM changes) rather than CSS selectors.
# Pre-lowercased for efficient case-insensitive matching
ACCESS_DENIED_TEXT_PATTERNS = [
    "you need access",
    "需要存取權",
    "request access",
    "要求存取權",
    "you don't have access",
    "您沒有存取權",
    "ask for access",
]

# Timeouts
LOGIN_TIMEOUT_MINUTES = 10
QUERY_TIMEOUT_SECONDS = 120
PAGE_LOAD_TIMEOUT = 30000
