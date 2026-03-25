#!/usr/bin/env python3
"""
Simple NotebookLM Question Interface
Based on MCP server implementation - simplified without sessions

Implements hybrid auth approach:
- Persistent browser profile (user_data_dir) for fingerprint consistency
- Manual cookie injection from state.json for session cookies (Playwright bug workaround)
See: https://github.com/microsoft/playwright/issues/36139
"""

import argparse
import sys
import time
import re
from pathlib import Path

from patchright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from notebook_manager import NotebookLibrary
from browser_utils import (
    BrowserFactory, StealthUtils,
    find_visible_input, poll_for_stable_response,
)


# Follow-up reminder (adapted from MCP server for stateless operation)
FOLLOW_UP_REMINDER = (
    "\n\nEXTREMELY IMPORTANT: Is that ALL you need to know? "
    "You can always ask another question! Think about it carefully: "
    "before you reply to the user, review their original request and this answer. "
    "If anything is still unclear or missing, ask me another comprehensive question "
    "that includes all necessary context (since each question opens a new browser session)."
)


def ask_notebooklm(question: str, notebook_url: str, headless: bool = True, quiet: bool = False) -> str:
    """
    Ask a question to NotebookLM (single-shot browser session).

    Returns:
        Raw answer text from NotebookLM (without FOLLOW_UP_REMINDER).
    """
    def log(msg):
        if not quiet:
            print(msg)

    auth = AuthManager()

    if not auth.is_authenticated():
        log("Warning: Not authenticated. Run: python auth_manager.py setup")
        return None

    log(f"Asking: {question}")
    log(f"Notebook: {notebook_url}")

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)

        page = context.new_page()
        log("  Opening notebook...")
        page.goto(notebook_url, wait_until="domcontentloaded")

        page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=10000)

        time.sleep(2)
        access_error = auth.diagnose_access_denied(page, notebook_url)
        if access_error:
            log(f"  Error: {access_error}")
            return None

        log("  Waiting for query input...")
        input_selector = find_visible_input(page)
        if not input_selector:
            log("  Error: Could not find query input")
            return None
        log(f"  Found input: {input_selector}")

        log("  Typing question...")
        if headless:
            StealthUtils.fast_fill(page, input_selector, question)
        else:
            StealthUtils.human_type(page, input_selector, question)

        log("  Submitting...")
        page.keyboard.press("Enter")

        if not headless:
            StealthUtils.random_delay(500, 1500)

        log("  Waiting for answer...")
        poll_interval = 0.5 if headless else 1
        stable_threshold = 2 if headless else 3

        answer = poll_for_stable_response(
            page,
            timeout=120,
            poll_interval=poll_interval,
            stable_threshold=stable_threshold,
        )

        if not answer:
            log("  Error: Timeout waiting for answer")
            return None

        log("  Got answer!")
        return answer

    except Exception as e:
        log(f"  Error: {e}")
        if not quiet:
            import traceback
            traceback.print_exc()
        return None

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
    parser = argparse.ArgumentParser(description='Ask NotebookLM a question')

    parser.add_argument('--question', required=True, help='Question to ask')
    parser.add_argument('--notebook-url', help='NotebookLM notebook URL')
    parser.add_argument('--notebook-id', help='Notebook ID from library')
    parser.add_argument('--show-browser', action='store_true', help='Show browser (enables stealth mode delays)')
    parser.add_argument('--quiet', action='store_true', help='Suppress all output except the final answer')

    args = parser.parse_args()
    quiet = args.quiet

    def log(msg):
        if not quiet:
            print(msg)

    # Resolve notebook URL
    notebook_url = args.notebook_url

    if not notebook_url and args.notebook_id:
        library = NotebookLibrary()
        notebook = library.get_notebook(args.notebook_id)
        if notebook:
            notebook_url = notebook['url']
        else:
            log(f"Error: Notebook '{args.notebook_id}' not found")
            return 1

    if not notebook_url:
        library = NotebookLibrary()
        active = library.get_active_notebook()
        if active:
            notebook_url = active['url']
            log(f"Using active notebook: {active['name']}")
        else:
            notebooks = library.list_notebooks()
            if notebooks:
                log("\nAvailable notebooks:")
                for nb in notebooks:
                    mark = " [ACTIVE]" if nb.get('id') == library.active_notebook_id else ""
                    log(f"  {nb['id']}: {nb['name']}{mark}")
                log("\nSpecify with --notebook-id or set active:")
                log("python scripts/run.py notebook_manager.py activate --id ID")
            else:
                log("No notebooks in library. Add one first:")
                log("python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS")
            return 1

    # Try daemon first (instant if running), fall back to single-shot browser
    answer = None
    if not args.show_browser:
        from browser_daemon import daemon_query  # lazy import — avoids side effects when unused
        answer = daemon_query(notebook_url, args.question)
        if answer:
            log("  (via daemon)")

    if not answer:
        answer = ask_notebooklm(
            question=args.question,
            notebook_url=notebook_url,
            headless=not args.show_browser,
            quiet=quiet
        )

    if answer:
        # Append follow-up reminder once, at the output boundary
        answer = answer + FOLLOW_UP_REMINDER
        if quiet:
            print(answer)
        else:
            print("\n" + "=" * 60)
            print(f"Question: {args.question}")
            print("=" * 60)
            print()
            print(answer)
            print()
            print("=" * 60)
        return 0
    else:
        log("\nFailed to get answer")
        return 1


if __name__ == "__main__":
    sys.exit(main())
