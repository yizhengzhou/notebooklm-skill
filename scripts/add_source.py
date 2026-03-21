#!/usr/bin/env python3
"""
Add a text source to a NotebookLM notebook.

Uses browser automation to paste text content as a new source document.
Flow: Open notebook?addSource=true → Click "Copied text" → Fill title → Inject text → Click "Insert"
"""

import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from patchright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from notebook_manager import NotebookLibrary
from browser_utils import BrowserFactory, StealthUtils
from config import PAGE_LOAD_TIMEOUT

# Selectors discovered from NotebookLM UI (2026-03-18)
PASTE_TEXTAREA_SELECTOR = "textarea.copied-text-input-textarea"
# Source rename: each source has button[aria-label="<name>"] + sibling button[aria-label="更多"]
# The "更多" menu contains "重新命名來源" (edit + rename) and "移除來源" (delete + remove)
DEFAULT_PASTE_SOURCE_NAME = "貼上的文字"


def _build_add_source_url(notebook_url: str) -> str:
    """Append addSource=true to the notebook URL."""
    parsed = urlparse(notebook_url)
    params = parse_qs(parsed.query)
    params["addSource"] = ["true"]
    new_query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _inject_text(page, selector: str, text: str):
    """Inject text into a textarea using native setter to trigger Angular change detection."""
    page.evaluate(
        """([sel, val]) => {
            const el = document.querySelector(sel);
            if (el) {
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype, 'value'
                ).set;
                setter.call(el, val);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""",
        [selector, text],
    )


def _rename_source(page, new_name: str) -> bool:
    """Rename the most recently added source (defaults to '貼上的文字') via three-dot menu.

    Flow: 來源 tab → find source → more_vert → 重新命名來源 → type name → confirm
    """
    import platform
    select_all = "Meta+a" if platform.system() == "Darwin" else "Control+a"

    # Switch to 來源 tab
    page.evaluate("""() => {
        const tabs = document.querySelectorAll('[role="tab"]');
        for (const t of tabs) {
            if (t.textContent.trim().includes('來源') || t.textContent.trim().includes('Sources')) {
                t.click(); return;
            }
        }
    }""")
    StealthUtils.random_delay(1500, 2500)

    # Find the source's more_vert button (look for "貼上的文字" or "Pasted text")
    menu_opened = page.evaluate("""(defaultName) => {
        const sourceBtn = document.querySelector('button[aria-label="' + defaultName + '"]')
            || document.querySelector('button[aria-label="Pasted text"]');
        if (!sourceBtn) return false;
        const parent = sourceBtn.parentElement;
        const moreBtn = parent.querySelector('button[aria-label="更多"]')
            || parent.querySelector('button[aria-label="More"]');
        if (moreBtn) { moreBtn.click(); return true; }
        return false;
    }""", DEFAULT_PASTE_SOURCE_NAME)

    if not menu_opened:
        return False

    StealthUtils.random_delay(500, 1000)

    # Click "重新命名來源" (rename) in the menu
    rename_clicked = page.evaluate("""() => {
        const overlays = document.querySelectorAll('.cdk-overlay-pane');
        for (const overlay of overlays) {
            if (overlay.offsetWidth > 0) {
                const items = overlay.querySelectorAll('button');
                for (const item of items) {
                    const t = item.textContent.trim();
                    if (t.includes('重新命名') || t.includes('Rename')) {
                        item.click();
                        return true;
                    }
                }
            }
        }
        return false;
    }""")

    if not rename_clicked:
        page.keyboard.press("Escape")
        return False

    StealthUtils.random_delay(500, 1000)

    # Find the rename input field inside the dialog overlay
    # The dialog uses edit-source-dialog with input.title-input
    rename_input = page.query_selector(".cdk-overlay-pane input.title-input")
    if not rename_input:
        # Fallback: any visible input in an overlay
        rename_input = page.query_selector(".cdk-overlay-pane input[type='text']")

    if not rename_input:
        page.keyboard.press("Escape")
        return False

    # Click input to focus, then clear and type new name
    rename_input.click()
    StealthUtils.random_delay(200, 400)
    page.keyboard.press(select_all)
    StealthUtils.random_delay(100, 200)
    rename_input.fill(new_name)
    StealthUtils.random_delay(300, 500)

    # Click the submit button in the dialog
    submitted = page.evaluate("""() => {
        const overlays = document.querySelectorAll('.cdk-overlay-pane');
        for (const overlay of overlays) {
            const btn = overlay.querySelector('button.submit-button, button[type="submit"]');
            if (btn && btn.offsetWidth > 0) {
                btn.click();
                return true;
            }
        }
        return false;
    }""")

    if not submitted:
        page.keyboard.press("Enter")

    StealthUtils.random_delay(1000, 2000)
    return True


def add_text_source(
    text: str,
    notebook_url: str,
    title: str = None,
    headless: bool = True,
) -> dict:
    """
    Add text content as a new source to a NotebookLM notebook.

    Args:
        text: The text content to add as a source
        notebook_url: NotebookLM notebook URL
        title: Source title (displayed in source list instead of "貼上文字")
        headless: Run browser in headless mode

    Returns:
        dict with status and message
    """
    auth_manager = AuthManager()
    if not auth_manager.is_authenticated():
        return {"status": "error", "message": "Not authenticated. Run: python scripts/run.py auth_manager.py setup"}

    if title:
        print(f"📄 Adding source: {title}")
    print(f"📚 Notebook: {notebook_url}")
    print(f"📝 Content length: {len(text)} chars")

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=headless)

        try:
            page = context.pages[0] if context.pages else context.new_page()

            # Step 1: Navigate to notebook with addSource dialog open
            add_source_url = _build_add_source_url(notebook_url)
            print("  🌐 Opening notebook (add source dialog)...")
            page.goto(add_source_url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=15000)
            StealthUtils.random_delay(3000, 5000)

            # Check for access request page (wrong account)
            if "accessrequest" in page.url:
                return {"status": "error", "message": "Access denied. Check Google account (authuser parameter)."}

            # Step 2: Click "Copied text" option in the add source dialog
            print("  📋 Selecting 'Copied text'...")
            clicked = page.evaluate("""() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    const t = b.textContent;
                    if (t.includes('複製的文字') || t.includes('Copied text')) {
                        b.click();
                        return true;
                    }
                }
                return false;
            }""")

            if not clicked:
                return {"status": "error", "message": "Could not find 'Copied text' button in add source dialog"}

            StealthUtils.random_delay(2000, 3000)

            # Step 3: Inject text into textarea
            print("  ✍️ Injecting text content...")
            textarea = page.query_selector(PASTE_TEXTAREA_SELECTOR)
            if not textarea:
                textarea = page.query_selector("textarea[placeholder*='貼上']")
            if not textarea:
                textarea = page.query_selector("textarea[placeholder*='Paste']")

            if not textarea:
                return {"status": "error", "message": "Could not find paste textarea"}

            _inject_text(page, PASTE_TEXTAREA_SELECTOR, text)
            StealthUtils.random_delay(500, 1000)

            # Verify text was injected
            current_value = textarea.input_value()
            if len(current_value) < 10:
                return {"status": "error", "message": f"Text injection failed. Only {len(current_value)} chars in textarea."}

            print(f"  ✓ Injected {len(current_value)} chars")

            # Step 4: Click "Insert" button
            print("  📤 Clicking 'Insert'...")
            inserted = page.evaluate("""() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    const t = b.textContent.trim();
                    if (t.includes('插入') || t.includes('Insert')) {
                        b.click();
                        return true;
                    }
                }
                return false;
            }""")

            if not inserted:
                return {"status": "error", "message": "Could not find 'Insert' button"}

            StealthUtils.random_delay(5000, 7000)

            # Step 5: Rename the source (it defaults to "貼上的文字")
            if title:
                print(f"  🏷️ Renaming source to: {title}")
                renamed = _rename_source(page, title)
                if renamed:
                    print(f"  ✓ Source renamed to: {title}")
                else:
                    print("  ⚠️ Rename failed, source will show as '貼上的文字'")

            result = {"status": "success", "message": f"Source added successfully ({len(text)} chars)"}
            if title:
                result["title"] = title
            print(f"  ✅ {result['message']}")
            return result

        except Exception as e:
            return {"status": "error", "message": f"Browser error: {str(e)}"}

        finally:
            context.close()


def main():
    parser = argparse.ArgumentParser(description="Add text source to NotebookLM")
    parser.add_argument("--text", help="Text content to add (reads from stdin if not provided)")
    parser.add_argument("--file", help="Path to text file to add")
    parser.add_argument("--title", help="Source title (shown in source list)")
    parser.add_argument("--category", help="Category prefix added to title (e.g., '用戶痛點' becomes '[用戶痛點] title')")
    parser.add_argument("--notebook-id", help="Notebook ID from library")
    parser.add_argument("--notebook-url", help="Direct NotebookLM URL")
    parser.add_argument("--show-browser", action="store_true", help="Show browser window")

    args = parser.parse_args()

    # Determine notebook URL
    notebook_url = args.notebook_url
    if not notebook_url and args.notebook_id:
        library = NotebookLibrary()
        notebook = library.get_notebook(args.notebook_id)
        if notebook:
            notebook_url = notebook["url"]
            library.increment_use_count(args.notebook_id)
        else:
            print(f"❌ Notebook '{args.notebook_id}' not found in library")
            sys.exit(1)

    if not notebook_url:
        # Try active notebook
        library = NotebookLibrary()
        active = library.get_active_notebook()
        if active:
            notebook_url = active["url"]
            library.increment_use_count(active["id"])
        else:
            print("❌ No notebook specified. Use --notebook-id, --notebook-url, or set an active notebook.")
            sys.exit(1)

    # Determine text content
    text = args.text
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        text = file_path.read_text(encoding="utf-8")
        title = args.title or file_path.name
    elif not text:
        # Read from stdin
        if sys.stdin.isatty():
            print("❌ No text provided. Use --text, --file, or pipe content via stdin.")
            sys.exit(1)
        text = sys.stdin.read()
        title = args.title or "Pasted text"
    else:
        title = args.title or "Pasted text"

    # Apply category prefix to title
    if args.category:
        category = args.category.strip("[]")
        if not title.startswith(f"[{category}]"):
            title = f"[{category}] {title}"

    if not text or len(text.strip()) < 10:
        print("❌ Text content is too short (minimum 10 chars)")
        sys.exit(1)

    result = add_text_source(
        text=text,
        notebook_url=notebook_url,
        title=title,
        headless=not args.show_browser,
    )

    if result["status"] == "success":
        print(f"\n✅ Source added to NotebookLM!")
    else:
        print(f"\n❌ Failed: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
