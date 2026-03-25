"""
Browser Utilities for NotebookLM Skill
Handles browser launching, stealth features, and common interactions
"""

import json
import time
import random
from typing import Optional, List

from patchright.sync_api import Playwright, BrowserContext, Page
from config import (
    BROWSER_PROFILE_DIR, STATE_FILE, BROWSER_ARGS, HEADLESS_BROWSER_ARGS,
    USER_AGENT, RESPONSE_SELECTORS, QUERY_INPUT_SELECTORS,
)


class BrowserFactory:
    """Factory for creating configured browser contexts"""

    @staticmethod
    def launch_persistent_context(
        playwright: Playwright,
        headless: bool = True,
        user_data_dir: str = str(BROWSER_PROFILE_DIR)
    ) -> BrowserContext:
        """
        Launch a persistent browser context with anti-detection features
        and cookie workaround.
        """
        # Launch persistent context using patchright's bundled Chromium (no dock icon)
        # When headless, use Chrome's new headless mode for improved invisibility
        browser_args = HEADLESS_BROWSER_ARGS if headless else BROWSER_ARGS
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            user_agent=USER_AGENT,
            args=browser_args
        )

        # Cookie Workaround for Playwright bug #36139
        # Session cookies (expires=-1) don't persist in user_data_dir automatically
        BrowserFactory._inject_cookies(context)

        return context

    @staticmethod
    def _inject_cookies(context: BrowserContext):
        """Inject cookies from state.json if available"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    if 'cookies' in state and len(state['cookies']) > 0:
                        context.add_cookies(state['cookies'])
                        # print(f"  🔧 Injected {len(state['cookies'])} cookies from state.json")
            except Exception as e:
                print(f"  ⚠️  Could not load state.json: {e}")


class StealthUtils:
    """Human-like interaction utilities"""

    @staticmethod
    def random_delay(min_ms: int = 100, max_ms: int = 500):
        """Add random delay"""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    @staticmethod
    def human_type(page: Page, selector: str, text: str, wpm_min: int = 320, wpm_max: int = 480):
        """Type with human-like speed"""
        element = page.query_selector(selector)
        if not element:
            # Try waiting if not immediately found
            try:
                element = page.wait_for_selector(selector, timeout=2000)
            except Exception:
                pass

        if not element:
            print(f"⚠️ Element not found for typing: {selector}")
            return

        # Click to focus
        element.click()
        
        # Type
        for char in text:
            element.type(char, delay=random.uniform(25, 75))
            if random.random() < 0.05:
                time.sleep(random.uniform(0.15, 0.4))

    @staticmethod
    def fast_fill(page: Page, selector: str, text: str):
        """Fast text input via JS — for headless mode where stealth isn't needed"""
        page.evaluate("""({selector, text}) => {
            const el = document.querySelector(selector);
            if (!el) return false;
            el.focus();
            const nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeSetter.call(el, text);
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            return true;
        }""", {"selector": selector, "text": text})

    @staticmethod
    def realistic_click(page: Page, selector: str):
        """Click with realistic movement"""
        element = page.query_selector(selector)
        if not element:
            return

        # Optional: Move mouse to element (simplified)
        box = element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            page.mouse.move(x, y, steps=5)

        StealthUtils.random_delay(100, 300)
        element.click()
        StealthUtils.random_delay(100, 300)


# ── Shared utilities (used by ask_question, browser_daemon, browser_session) ──

def find_visible_input(page: Page, selectors: list = None, timeout: int = 10000) -> Optional[str]:
    """Try each query-input selector, return the first visible match's selector string or None."""
    for selector in (selectors or QUERY_INPUT_SELECTORS):
        try:
            el = page.wait_for_selector(selector, timeout=timeout, state="visible")
            if el:
                return selector
        except Exception:
            continue
    return None


def snapshot_latest_response(page: Page, selectors: list = None) -> Optional[str]:
    """Return the current last bot-message text, or None."""
    for sel in (selectors or RESPONSE_SELECTORS):
        try:
            elements = page.query_selector_all(sel)
            if elements:
                text = elements[-1].inner_text().strip()
                return text or None
        except Exception:
            pass
    return None


def poll_for_stable_response(
    page: Page,
    previous_answer: Optional[str] = None,
    timeout: int = 120,
    poll_interval: float = 0.5,
    stable_threshold: int = 2,
    selectors: list = None,
) -> Optional[str]:
    """Poll until a new, stable answer appears. Returns answer text or None on timeout."""
    _selectors = selectors or RESPONSE_SELECTORS
    deadline = time.time() + timeout
    last_candidate: Optional[str] = None
    stable_count = 0

    while time.time() < deadline:
        try:
            thinking = page.query_selector('div.thinking-message')
            if thinking and thinking.is_visible():
                time.sleep(poll_interval)
                continue
        except Exception:
            pass

        for sel in _selectors:
            try:
                elements = page.query_selector_all(sel)
                if not elements:
                    continue
                latest = elements[-1].inner_text().strip()
                if latest and latest != previous_answer:
                    if latest == last_candidate:
                        stable_count += 1
                        if stable_count >= stable_threshold:
                            return latest
                    else:
                        last_candidate = latest
                        stable_count = 1
                break
            except Exception:
                continue

        time.sleep(poll_interval)

    return None
