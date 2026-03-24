#!/usr/bin/env python3
"""Create a new NotebookLM notebook via browser automation."""

import re
import sys
import time
from pathlib import Path
from patchright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from browser_utils import BrowserFactory, StealthUtils
from config import PAGE_LOAD_TIMEOUT


def _snapshot_notebook_ids(page) -> set:
    """Capture all notebook UUIDs currently visible on the homepage."""
    ids = page.evaluate("""() => {
        const links = document.querySelectorAll('a[href*="/notebook/"]');
        const ids = new Set();
        for (const a of links) {
            const m = a.href.match(/notebook\\/([0-9a-f]{8}-[0-9a-f]{4}-[^?/]+)/);
            if (m) ids.add(m[1]);
        }
        return [...ids];
    }""")
    return set(ids)


def _find_new_notebook_on_homepage(page, before_ids: set, authuser: int) -> str:
    """Return to homepage and find the notebook that didn't exist before."""
    homepage = f"https://notebooklm.google.com?authuser={authuser}"
    page.goto(homepage, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
    StealthUtils.random_delay(3000, 5000)

    after_ids = _snapshot_notebook_ids(page)
    new_ids = after_ids - before_ids

    if new_ids:
        new_id = new_ids.pop()
        return f"https://notebooklm.google.com/notebook/{new_id}?authuser={authuser}"
    return None


def _create_notebook_in_browser(headless: bool = True, authuser: int = 1) -> str:
    """Create a new empty notebook and return its URL.

    Flow: Snapshot existing IDs -> Click create -> Wait for UUID redirect
          If redirect fails, fallback to homepage diff to find the new notebook.

    Returns:
        The full URL of the newly created notebook
    Raises:
        RuntimeError if creation fails AND recovery also fails
    """
    homepage = f"https://notebooklm.google.com?authuser={authuser}"

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()

            # Step 1: Navigate to homepage and snapshot existing notebooks
            print("  Opening NotebookLM homepage...")
            page.goto(homepage, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            page.wait_for_url(re.compile(r"notebooklm\.google\.com"), timeout=15000)
            StealthUtils.random_delay(3000, 5000)

            before_ids = _snapshot_notebook_ids(page)

            # Step 2: Click "建立新的筆記本" button
            print("  Creating new notebook...")
            clicked = page.evaluate("""() => {
                const btn = document.querySelector('button[aria-label="建立新的筆記本"]')
                    || document.querySelector('button.create-new-button')
                    || document.querySelector('button[aria-label="Create new notebook"]');
                if (btn) { btn.click(); return true; }
                // Fallback: find by text
                const all = document.querySelectorAll('button');
                for (const b of all) {
                    if (b.textContent.includes('新建') || b.textContent.includes('Create new')) {
                        b.click(); return true;
                    }
                }
                return false;
            }""")

            if not clicked:
                raise RuntimeError("Could not find 'Create new notebook' button")

            # Step 3: Wait for URL to change to new notebook (UUID format)
            # NotebookLM shows /notebook/creating as a transition page before redirecting
            # to the actual UUID URL. We must wait for the full UUID, not the transition.
            print("  Waiting for notebook to be created...")
            try:
                page.wait_for_url(
                    re.compile(r"notebooklm\.google\.com/notebook/[0-9a-f]{8}-[0-9a-f]{4}-"),
                    timeout=60000
                )
                StealthUtils.random_delay(2000, 3000)
                new_url = page.url
            except Exception:
                # Fallback: redirect failed or timed out, but notebook may exist.
                # Go back to homepage and diff notebook IDs to find it.
                print("  URL redirect failed, recovering via homepage diff...")
                new_url = _find_new_notebook_on_homepage(page, before_ids, authuser)
                if not new_url:
                    raise RuntimeError(
                        "Notebook was likely created but URL could not be captured. "
                        "Check NotebookLM homepage manually."
                    )

            print(f"  Notebook created: {new_url}")
            return new_url

        except Exception as e:
            raise RuntimeError(f"Failed to create notebook: {e}")
        finally:
            context.close()


def create_notebook(
    name: str,
    role: str = None,
    description: str = None,
    topics: list = None,
    headless: bool = True,
) -> dict:
    """Create a new notebook and register it in the library.

    Returns:
        The library entry dict for the new notebook
    """
    auth_manager = AuthManager()
    if not auth_manager.is_authenticated():
        print("Not authenticated. Run: python scripts/run.py auth_manager.py setup")
        sys.exit(1)

    auth_info = auth_manager.get_auth_info()
    authuser = auth_info.get("authuser", 1)

    url = _create_notebook_in_browser(headless=headless, authuser=authuser)

    from notebook_manager import NotebookLibrary
    library = NotebookLibrary()

    notebook = library.add_notebook(
        url=url,
        name=name,
        description=description or f"Notebook for {name}",
        topics=topics or [],
        role=role,
    )

    return notebook


def create_pair(
    project_name: str,
    headless: bool = True,
) -> dict:
    """Create a Research + Project notebook pair.

    Returns:
        Dict with 'research' and 'project' notebook entries
    """
    print(f"Creating Research notebook for {project_name}...")
    research = create_notebook(
        name=f"[Research] {project_name}",
        role="research",
        description=f"{project_name} market research, user pain points, competitor analysis",
        topics=["research", "pain-points", "competitors", "market"],
        headless=headless,
    )

    print(f"\nCreating Project notebook for {project_name}...")
    project = create_notebook(
        name=f"[Project] {project_name}",
        role="project",
        description=f"{project_name} product specs, version history, technical decisions, progress",
        topics=["project", "specs", "decisions", "progress"],
        headless=headless,
    )

    # Link them
    from notebook_manager import NotebookLibrary
    library = NotebookLibrary()
    library.update_notebook(research['id'], paired_with=project['id'])
    library.update_notebook(project['id'], paired_with=research['id'])

    print(f"\nNotebook pair created and linked!")
    print(f"  Research: {research['id']}")
    print(f"  Project:  {project['id']}")

    return {"research": research, "project": project}


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Create NotebookLM notebooks")
    parser.add_argument("--name", required=True, help="Project or notebook name")
    parser.add_argument("--pair", action="store_true", help="Create Research + Project pair")
    parser.add_argument("--role", choices=["research", "project"], help="Notebook role (single mode)")
    parser.add_argument("--description", help="Notebook description")
    parser.add_argument("--topics", help="Comma-separated topics")
    parser.add_argument("--show-browser", action="store_true", help="Show browser window")

    args = parser.parse_args()

    if args.pair:
        result = create_pair(
            project_name=args.name,
            headless=not args.show_browser,
        )
    else:
        topics = [t.strip() for t in args.topics.split(",")] if args.topics else None
        result = create_notebook(
            name=args.name,
            role=args.role,
            description=args.description,
            topics=topics,
            headless=not args.show_browser,
        )

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
