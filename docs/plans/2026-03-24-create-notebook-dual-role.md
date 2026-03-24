# Create Notebook + Dual-Role Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable skill to create new NotebookLM notebooks via browser automation, with a `--pair` mode that creates Research + Project notebooks for harness-style planning/execution separation.

**Architecture:** New `create_notebook.py` script handles browser automation (navigate to homepage, click create button, capture new URL). `notebook_manager.py` gains `role` and `paired_with` fields. SKILL.md gains query routing logic based on notebook role.

**Tech Stack:** Patchright (existing), same browser automation patterns as `add_source.py`

**DOM Discovery (2026-03-24):**
- Create button: `button[aria-label="建立新的筆記本"]` / class `create-new-button`
- Fallback text: `add新建` or `Create new`
- After click, URL changes to `notebooklm.google.com/notebook/{uuid}?authuser=N`

---

### Task 1: Create `create_notebook.py` — Core browser automation

**Files:**
- Create: `scripts/create_notebook.py`

- [ ] **Step 1: Write `_create_notebook_in_browser()` function**

```python
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


def _create_notebook_in_browser(headless: bool = True, authuser: int = 1) -> str:
    """Create a new empty notebook and return its URL.

    Flow: Navigate to homepage → Click create button → Wait for redirect → Return URL

    Returns:
        The full URL of the newly created notebook
    Raises:
        RuntimeError if creation fails
    """
    homepage = f"https://notebooklm.google.com?authuser={authuser}"

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()

            # Step 1: Navigate to homepage
            print("  🌐 Opening NotebookLM homepage...")
            page.goto(homepage, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT)
            page.wait_for_url(re.compile(r"notebooklm\.google\.com"), timeout=15000)
            StealthUtils.random_delay(3000, 5000)

            # Step 2: Click "建立新的筆記本" button
            print("  📓 Creating new notebook...")
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

            # Step 3: Wait for URL to change to new notebook
            print("  ⏳ Waiting for notebook to be created...")
            page.wait_for_url(
                re.compile(r"notebooklm\.google\.com/notebook/[a-f0-9-]+"),
                timeout=30000
            )
            StealthUtils.random_delay(2000, 3000)

            new_url = page.url
            print(f"  ✅ Notebook created: {new_url}")
            return new_url

        except Exception as e:
            raise RuntimeError(f"Failed to create notebook: {e}")
        finally:
            context.close()
```

- [ ] **Step 2: Run manual test to verify browser automation works**

```bash
cd /Volumes/NEWXYZ/macOS_data_mirror/Project/notebooklm-skill
.venv/bin/python3 -c "
import sys; sys.path.insert(0, 'scripts')
from create_notebook import _create_notebook_in_browser
url = _create_notebook_in_browser(headless=False)
print(f'Created: {url}')
"
```

Expected: Browser opens, clicks create, new notebook URL is printed.

- [ ] **Step 3: Commit**

```bash
git add scripts/create_notebook.py
git commit -m "feat: add create_notebook.py browser automation core"
```

---

### Task 2: Add `role` and `paired_with` to notebook_manager.py

**Files:**
- Modify: `scripts/notebook_manager.py` — `add_notebook()` method (line 63-121) and `main()` CLI (line 308-406)

- [ ] **Step 1: Add `role` and `paired_with` parameters to `add_notebook()`**

In `add_notebook()` signature, add:
```python
role: Optional[str] = None,       # "research" or "project"
paired_with: Optional[str] = None  # ID of paired notebook
```

In the notebook dict (line 96-108), add:
```python
'role': role,              # "research", "project", or None
'paired_with': paired_with,  # ID of paired notebook
```

- [ ] **Step 2: Add `--role` and `--paired-with` to CLI add command**

In `main()` add_parser section (line 315-321):
```python
add_parser.add_argument('--role', choices=['research', 'project'], help='Notebook role for dual-notebook architecture')
add_parser.add_argument('--paired-with', help='ID of paired notebook')
```

Pass to `add_notebook()` call (line 352-359):
```python
role=args.role,
paired_with=getattr(args, 'paired_with', None)
```

- [ ] **Step 3: Update list display to show role**

In the list command output (line 367-371), add role display:
```python
role_tag = f" [{notebook.get('role', '').upper()}]" if notebook.get('role') else ""
print(f"\n  📓 {notebook['name']}{active}{role_tag}")
```

- [ ] **Step 4: Verify existing commands still work**

```bash
python3 scripts/run.py notebook_manager.py list
python3 scripts/run.py notebook_manager.py stats
```

Expected: No errors, existing notebooks display correctly (role shows empty for old entries).

- [ ] **Step 5: Commit**

```bash
git add scripts/notebook_manager.py
git commit -m "feat: add role and paired_with fields to notebook library"
```

---

### Task 3: Add CLI interface and `--pair` mode to create_notebook.py

**Files:**
- Modify: `scripts/create_notebook.py`

- [ ] **Step 1: Add `create_notebook()` high-level function and CLI**

```python
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
        return {"status": "error", "message": "Not authenticated"}

    # Get authuser from auth info
    auth_info = auth_manager.get_auth_info()
    authuser = auth_info.get("authuser", 1)

    # Create via browser
    url = _create_notebook_in_browser(headless=headless, authuser=authuser)

    # Register in library
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
    print(f"🔬 Creating Research notebook for {project_name}...")
    research = create_notebook(
        name=f"[Research] {project_name}",
        role="research",
        description=f"{project_name} 市場研究、用戶痛點、競品分析",
        topics=["research", "pain-points", "competitors", "market"],
        headless=headless,
    )

    print(f"\n📋 Creating Project notebook for {project_name}...")
    project = create_notebook(
        name=f"[Project] {project_name}",
        role="project",
        description=f"{project_name} 產品規格、版本歷史、技術決策、進度",
        topics=["project", "specs", "decisions", "progress"],
        headless=headless,
    )

    # Link them
    from notebook_manager import NotebookLibrary
    library = NotebookLibrary()
    library.update_notebook(research['id'], paired_with=project['id'])
    library.update_notebook(project['id'], paired_with=research['id'])

    print(f"\n✅ Notebook pair created and linked!")
    print(f"  🔬 Research: {research['id']}")
    print(f"  📋 Project:  {project['id']}")

    return {"research": research, "project": project}
```

- [ ] **Step 2: Add argparse CLI**

```python
def main():
    import argparse
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

    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Test single notebook creation via CLI**

```bash
python3 scripts/run.py create_notebook.py --name "Test Single" --role research --show-browser
```

Expected: New notebook created, added to library with role=research.

- [ ] **Step 4: Test pair creation via CLI**

```bash
python3 scripts/run.py create_notebook.py --name "Test Pair" --pair --show-browser
```

Expected: Two notebooks created, linked via paired_with, both in library.

- [ ] **Step 5: Commit**

```bash
git add scripts/create_notebook.py
git commit -m "feat: add CLI and --pair mode for dual-notebook creation"
```

---

### Task 4: Update `notebook_manager.py` to support `update_notebook` with new fields via CLI

**Files:**
- Modify: `scripts/notebook_manager.py` — add `update` subcommand to CLI

- [ ] **Step 1: Add update subcommand to argparse**

After the `add` command section in `main()`:
```python
update_parser = subparsers.add_parser('update', help='Update notebook metadata')
update_parser.add_argument('--id', required=True, help='Notebook ID')
update_parser.add_argument('--role', choices=['research', 'project'], help='Set notebook role')
update_parser.add_argument('--paired-with', help='Set paired notebook ID')
update_parser.add_argument('--description', help='Update description')
update_parser.add_argument('--name', help='Update name')
```

And the handler:
```python
elif args.command == 'update':
    kwargs = {}
    if args.role: kwargs['role'] = args.role
    if getattr(args, 'paired_with', None): kwargs['paired_with'] = args.paired_with
    if args.description: kwargs['description'] = args.description
    if args.name: kwargs['name'] = args.name
    notebook = library.update_notebook(args.id, **kwargs)
    print(json.dumps(notebook, indent=2))
```

- [ ] **Step 2: Update `update_notebook()` to handle `role` and `paired_with`**

Add to the update method (after line 190):
```python
if 'role' in kwargs:
    notebook['role'] = kwargs['role']
if 'paired_with' in kwargs:
    notebook['paired_with'] = kwargs['paired_with']
```

Wait — the method uses explicit params. Add `role` and `paired_with` to the signature:
```python
def update_notebook(self, notebook_id, ..., role=None, paired_with=None):
```
And in the body:
```python
if role is not None:
    notebook['role'] = role
if paired_with is not None:
    notebook['paired_with'] = paired_with
```

- [ ] **Step 3: Commit**

```bash
git add scripts/notebook_manager.py
git commit -m "feat: add update subcommand and role/paired_with update support"
```

---

### Task 5: Update SKILL.md with create command and query routing

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Add create_notebook to Script Reference section**

After the `set_notebook_guide.py` section:
```markdown
### Create Notebook (`create_notebook.py`)
\`\`\`bash
# Create a single notebook
python scripts/run.py create_notebook.py --name "My Notebook" [--role research|project] [--show-browser]

# Create Research + Project pair (recommended for new projects)
python scripts/run.py create_notebook.py --name "ProjectName" --pair [--show-browser]
\`\`\`
**When to use:** When starting a new project that will use NotebookLM as its knowledge base. The `--pair` mode creates two linked notebooks following the planning/execution separation pattern.
```

- [ ] **Step 2: Add query routing guidance**

After the Follow-Up Mechanism section:
```markdown
## Notebook Role Routing

When a project has paired notebooks (role: research + project), route queries based on intent:

| Question type | Route to | Examples |
|--------------|----------|----------|
| Why / market / users / competitors | `role: research` | "What are the top pain points?", "How do competitors handle X?" |
| What / specs / decisions / versions | `role: project` | "What did we decide about the auth module?", "What's in v2.0?" |
| Unclear | Query both, synthesize | "Give me an overview of where the project stands" |

Agent should check `notebook_manager.py list` for role and paired_with fields to determine routing.
```

- [ ] **Step 3: Update the Scaling section**

Replace the current scaling guidance with the dual-notebook recommendation:
```markdown
### Scaling: Dual-Notebook Architecture

For new projects, create a Research + Project notebook pair:
\`\`\`bash
python scripts/run.py create_notebook.py --name "MyProject" --pair
\`\`\`

This creates:
- **[Research] MyProject** — market research, user pain points, competitor analysis (persona: market analyst)
- **[Project] MyProject** — product specs, version history, technical decisions (persona: product manager)

Benefits:
- Separates planning from execution knowledge (harness engineering pattern)
- Each notebook stays under the source limit
- Project notebook can generate presentations and overviews via NotebookLM's built-in tools
```

- [ ] **Step 4: Commit**

```bash
git add SKILL.md
git commit -m "docs: add create_notebook command and dual-notebook query routing to SKILL.md"
```

---

### Task 6: Update README with dual-notebook architecture

**Files:**
- Modify: `README.md`
- Modify: `README.zh-TW.md`

- [ ] **Step 1: Update the Scaling section in README.md**

Update the existing "Scaling: When One Notebook Isn't Enough" to lead with the dual-notebook pattern and add the create command.

- [ ] **Step 2: Update README.zh-TW.md** with equivalent changes

- [ ] **Step 3: Add to CHANGELOG.md** as v1.4.0 feature

- [ ] **Step 4: Commit**

```bash
git add README.md README.zh-TW.md CHANGELOG.md
git commit -m "docs: add dual-notebook architecture to READMEs and changelog"
```

---

### Task 7: End-to-end test with Sandbox notebook

- [ ] **Step 1: Create a test pair using Sandbox**

```bash
python3 scripts/run.py create_notebook.py --name "Sandbox Test" --pair --show-browser
```

- [ ] **Step 2: Verify library shows both notebooks with correct roles**

```bash
python3 scripts/run.py notebook_manager.py list
```

Expected: Two new notebooks with [RESEARCH] and [PROJECT] tags, linked via paired_with.

- [ ] **Step 3: Clean up test notebooks**

```bash
python3 scripts/run.py notebook_manager.py remove --id "research-sandbox-test"
python3 scripts/run.py notebook_manager.py remove --id "project-sandbox-test"
```

(Also manually delete from NotebookLM website)
