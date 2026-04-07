#!/usr/bin/env python3
"""
Set NotebookLM Notebook Guide (Persona) Configuration

Automates the "設定對話" (Configure Conversation) dialog in NotebookLM
to set a custom persona/role and response length for the notebook.

Uses Patchright headless browser, same as ask_question.py.
"""

import argparse
import platform
import sys
import re
from pathlib import Path

from patchright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from notebook_manager import NotebookLibrary
from config import (
    GUIDE_TYPE_RADIO_SELECTORS,
    GUIDE_TEXTAREA_SELECTORS,
    GUIDE_RESPONSE_LENGTH_SELECTORS,
    GUIDE_SUBMIT_SELECTORS,
)
from browser_utils import BrowserFactory, StealthUtils

SELECT_ALL_KEY = "Meta+a" if platform.system() == "Darwin" else "Control+a"

# Button text variants for opening the settings dialog (multi-locale)
_SETTINGS_BUTTON_TEXTS = ["設定筆記本", "Customize", "Notebook guide"]


def _click_radio(page, selector_string, description):
    """Click a radio button from a comma-separated selector string.

    Uses a combined CSS selector for a single wait instead of sequential timeouts.
    """
    combined = selector_string  # already comma-separated = valid CSS multi-selector
    try:
        radio = page.wait_for_selector(combined, timeout=5000, state="visible")
        if radio:
            if radio.get_attribute("aria-checked") != "true":
                radio.click()
                StealthUtils.random_delay(300, 600)
            print(f"  ✓ {description}")
            return True
    except Exception:
        pass
    print(f"  ❌ Could not find: {description}")
    return False


def _resolve_notebook_url(args):
    """Resolve notebook URL from args (--notebook-url, --notebook-id, or active)."""
    if args.notebook_url:
        return args.notebook_url

    library = NotebookLibrary()

    if args.notebook_id:
        notebook = library.get_notebook(args.notebook_id)
        if notebook:
            return notebook["url"]
        print(f"❌ Notebook '{args.notebook_id}' not found")
        return None

    active = library.get_active_notebook()
    if active:
        print(f"📚 Using active notebook: {active['name']}")
        return active["url"]

    notebooks = library.list_notebooks()
    if notebooks:
        print("\n📚 Available notebooks:")
        for nb in notebooks:
            mark = " [ACTIVE]" if nb.get("id") == library.active_notebook_id else ""
            print(f"  {nb['id']}: {nb['name']}{mark}")
        print("\nSpecify with --notebook-id or --notebook-url")
    else:
        print("❌ No notebooks in library.")
    return None


def set_notebook_guide(
    notebook_url: str,
    persona: str,
    response_length: str = "default",
    headless: bool = True,
) -> bool:
    """
    Set the Notebook Guide (persona) for a NotebookLM notebook.

    Args:
        notebook_url: NotebookLM notebook URL
        persona: Custom persona/role description text (max 10000 chars)
        response_length: "default", "long", or "short"
        headless: Run browser in headless mode

    Returns:
        True if successful, False otherwise
    """
    auth = AuthManager()
    if not auth.is_authenticated():
        print("⚠️ Not authenticated. Run: python scripts/run.py auth_manager.py setup")
        return False

    if len(persona) > 10000:
        print(f"⚠️ Persona text too long ({len(persona)} chars, max 10000)")
        return False

    if response_length not in ("default", "long", "short"):
        print(f"⚠️ Invalid response_length: {response_length}. Use: default, long, short")
        return False

    print(f"⚙️ Setting Notebook Guide")
    print(f"  📚 Notebook: {notebook_url}")
    print(f"  📝 Persona: {persona[:80]}...")
    print(f"  📏 Response length: {response_length}")

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
        page = context.new_page()

        # Navigate to notebook
        print("  🌐 Opening notebook...")
        page.goto(notebook_url, wait_until="domcontentloaded")
        page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=15000)
        StealthUtils.random_delay(3000, 5000)

        # Step 1: Open settings dialog
        # The "設定筆記本" button (class: configure-settings-button) is in the
        # chat panel, not the top toolbar. Wait for it to render.
        print("  ⚙️ Opening settings dialog...")
        opened = False

        # Approach 1: CSS class (most reliable — unique class name)
        try:
            btn = page.wait_for_selector(
                "button.configure-settings-button", timeout=15000, state="visible"
            )
            if btn:
                btn.click()
                opened = True
                print("  ✓ Clicked settings button (class='configure-settings-button')")
        except Exception:
            pass

        # Approach 2: aria-label matching (handles icon-only buttons)
        if not opened:
            _SETTINGS_ARIA_LABELS = ["設定筆記本", "Customize notebook", "Notebook guide"]
            for label in _SETTINGS_ARIA_LABELS:
                try:
                    clicked = page.evaluate(
                        """(ariaLabel) => {
                            const btn = document.querySelector(`button[aria-label="${ariaLabel}"]`);
                            if (btn) { btn.click(); return true; }
                            return false;
                        }""",
                        label,
                    )
                    if clicked:
                        opened = True
                        print(f"  ✓ Clicked settings button (aria-label='{label}')")
                        break
                except Exception:
                    continue

        # Approach 3: textContent fallback (legacy)
        if not opened:
            for text in _SETTINGS_BUTTON_TEXTS:
                try:
                    clicked = page.evaluate(
                        """(btnText) => {
                            const btns = document.querySelectorAll('button');
                            for (const b of btns) {
                                if (b.textContent.includes(btnText)) { b.click(); return true; }
                            }
                            return false;
                        }""",
                        text,
                    )
                    if clicked:
                        opened = True
                        print(f"  ✓ Clicked settings button (text='{text}')")
                        break
                except Exception:
                    continue

        if not opened:
            print("  ❌ Could not find settings button")
            return False

        # Step 2: Wait for dialog (native wait, not sleep loop)
        print("  ⏳ Waiting for settings dialog...")
        try:
            page.wait_for_selector(".configure-settings-container", timeout=5000, state="visible")
        except Exception:
            print("  ❌ Settings dialog did not open")
            return False

        # Step 3: Select "自訂" (Custom) radio
        print("  🔘 Selecting custom guide type...")
        _click_radio(page, GUIDE_TYPE_RADIO_SELECTORS["custom"], "Custom guide type selected")

        # Step 4: Clear and type persona text
        print("  📝 Setting persona text...")
        textarea = None
        for selector in GUIDE_TEXTAREA_SELECTORS:
            try:
                textarea = page.wait_for_selector(selector, timeout=5000, state="visible")
                if textarea:
                    break
            except Exception:
                continue

        if not textarea:
            print("  ❌ Could not find persona textarea")
            return False

        # Clear existing text
        textarea.click()
        StealthUtils.random_delay(200, 400)
        page.keyboard.press(SELECT_ALL_KEY)
        StealthUtils.random_delay(100, 200)
        page.keyboard.press("Backspace")
        StealthUtils.random_delay(200, 400)

        # Type persona: use fill() for long text, human_type for short
        if len(persona) > 200:
            textarea.fill(persona)
            textarea.dispatch_event("input")
            textarea.dispatch_event("change")
        else:
            StealthUtils.human_type(page, GUIDE_TEXTAREA_SELECTORS[0], persona)
        print(f"  ✓ Set persona ({len(persona)} chars)")

        # Step 5: Set response length
        if response_length != "default":
            print(f"  📏 Setting response length: {response_length}...")
            length_selector = GUIDE_RESPONSE_LENGTH_SELECTORS.get(response_length, "")
            if length_selector:
                _click_radio(page, length_selector, f"Response length set to: {response_length}")

        # Step 6: Click Save
        print("  💾 Saving...")
        saved = False
        combined_submit = ", ".join(GUIDE_SUBMIT_SELECTORS)
        try:
            btn = page.wait_for_selector(combined_submit, timeout=5000, state="visible")
            if btn:
                btn.click()
                saved = True
                print("  ✓ Settings saved!")
        except Exception:
            pass

        if not saved:
            # Fallback: find submit button via JS
            result = page.evaluate("""
                (() => {
                    const btn = document.querySelector('button[type="submit"]');
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
            """)
            if result:
                saved = True
                print("  ✓ Settings saved (fallback)")
            else:
                print("  ❌ Could not find save button")
                return False

        StealthUtils.random_delay(1000, 2000)
        print("✅ Notebook Guide configured successfully!")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Set NotebookLM Notebook Guide (persona)")

    parser.add_argument("--persona", required=True, help="Custom persona/role description")
    parser.add_argument(
        "--response-length",
        choices=["default", "long", "short"],
        default="default",
        help="Response length preference",
    )
    parser.add_argument("--notebook-url", help="NotebookLM notebook URL")
    parser.add_argument("--notebook-id", help="Notebook ID from library")
    parser.add_argument("--show-browser", action="store_true", help="Show browser window")

    args = parser.parse_args()

    notebook_url = _resolve_notebook_url(args)
    if not notebook_url:
        return 1

    success = set_notebook_guide(
        notebook_url=notebook_url,
        persona=args.persona,
        response_length=args.response_length,
        headless=not args.show_browser,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
