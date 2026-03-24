---
name: notebooklm
description: >
  USE WHEN user mentions NotebookLM, shares notebooklm.google.com URLs,
  asks to query notebooks/documentation, says "ask my docs", "check my notebook",
  or wants to add sources to NotebookLM.
  Queries Google NotebookLM for source-grounded, citation-backed answers from Gemini.
  Browser automation via Patchright, notebook library management, persistent auth,
  text source upload with auto-naming, notebook guide/persona configuration.
---

# NotebookLM Research Assistant Skill

Interact with Google NotebookLM to query documentation with Gemini's source-grounded answers. Each question opens a fresh browser session, retrieves the answer exclusively from your uploaded documents, and closes.

## When to Use This Skill

Trigger when user:
- Mentions NotebookLM explicitly
- Shares NotebookLM URL (`https://notebooklm.google.com/notebook/...`)
- Asks to query their notebooks/documentation
- Wants to add documentation to NotebookLM library
- Uses phrases like "ask my NotebookLM", "check my docs", "query my notebook"

## ⚠️ CRITICAL: Add Command - Smart Discovery

When user wants to add a notebook without providing details:

**SMART ADD (Recommended)**: Query the notebook first to discover its content:
```bash
# Step 1: Query the notebook about its content
python scripts/run.py ask_question.py --question "What is the content of this notebook? What topics are covered? Provide a complete overview briefly and concisely" --notebook-url "[URL]"

# Step 2: Use the discovered information to add it
python scripts/run.py notebook_manager.py add --url "[URL]" --name "[Based on content]" --description "[Based on content]" --topics "[Based on content]"
```

**MANUAL ADD**: If user provides all details:
- `--url` - The NotebookLM URL
- `--name` - A descriptive name
- `--description` - What the notebook contains (REQUIRED!)
- `--topics` - Comma-separated topics (REQUIRED!)

NEVER guess or use generic descriptions! If details missing, use Smart Add to discover them.

## Critical: Always Use run.py Wrapper

**NEVER call scripts directly. ALWAYS use `python scripts/run.py [script]`:**

```bash
# ✅ CORRECT - Always use run.py:
python scripts/run.py auth_manager.py status
python scripts/run.py notebook_manager.py list
python scripts/run.py ask_question.py --question "..."

# ❌ WRONG - Never call directly:
python scripts/auth_manager.py status  # Fails without venv!
```

The `run.py` wrapper automatically:
1. Creates `.venv` if needed
2. Installs all dependencies
3. Activates environment
4. Executes script properly

## Core Workflow

### Step 1: Check Authentication Status
```bash
python scripts/run.py auth_manager.py status
```

If not authenticated, proceed to setup.

### Step 2: Authenticate (One-Time Setup)
```bash
# Browser MUST be visible for manual Google login
python scripts/run.py auth_manager.py setup
```

**Important:**
- Browser is VISIBLE for authentication
- Browser window opens automatically
- User must manually log in to Google
- Tell user: "A browser window will open for Google login"

### Step 3: Manage Notebook Library

```bash
# List all notebooks
python scripts/run.py notebook_manager.py list

# BEFORE ADDING: Ask user for metadata if unknown!
# "What does this notebook contain?"
# "What topics should I tag it with?"

# Add notebook to library (ALL parameters are REQUIRED!)
python scripts/run.py notebook_manager.py add \
  --url "https://notebooklm.google.com/notebook/..." \
  --name "Descriptive Name" \
  --description "What this notebook contains" \  # REQUIRED - ASK USER IF UNKNOWN!
  --topics "topic1,topic2,topic3"  # REQUIRED - ASK USER IF UNKNOWN!

# Search notebooks by topic
python scripts/run.py notebook_manager.py search --query "keyword"

# Set active notebook
python scripts/run.py notebook_manager.py activate --id notebook-id

# Remove notebook
python scripts/run.py notebook_manager.py remove --id notebook-id
```

### Quick Workflow
1. Check library: `python scripts/run.py notebook_manager.py list`
2. Ask question: `python scripts/run.py ask_question.py --question "..." --notebook-id ID`

### Step 4: Ask Questions

```bash
# Basic query (uses active notebook if set)
python scripts/run.py ask_question.py --question "Your question here"

# Query specific notebook
python scripts/run.py ask_question.py --question "..." --notebook-id notebook-id

# Query with notebook URL directly
python scripts/run.py ask_question.py --question "..." --notebook-url "https://..."

# Show browser for debugging
python scripts/run.py ask_question.py --question "..." --show-browser

# Filter by category prefix (if sources are categorized)
python scripts/run.py ask_question.py --question "Based only on [用戶痛點] sources, what are the top pain points?"
```

**Tip:** If the notebook has categorized sources (e.g., `[用戶痛點]`, `[競品分析]`), include the prefix in your question to focus the answer. See "Category Prefix System" below for details.

## Follow-Up Mechanism (CRITICAL)

Every NotebookLM answer ends with: **"EXTREMELY IMPORTANT: Is that ALL you need to know?"**

**Required Claude Behavior:**
1. **STOP** - Do not immediately respond to user
2. **ANALYZE** - Compare answer to user's original request
3. **IDENTIFY GAPS** - Determine if more information needed
4. **CONSIDER CATEGORY FILTERS** - If the notebook has categorized sources, ask targeted questions per category (e.g., `[競品分析]`, `[用戶痛點]`) to get focused answers from each source group
5. **ASK FOLLOW-UP** - If gaps exist, immediately ask:
   ```bash
   python scripts/run.py ask_question.py --question "Follow-up with context..."
   ```
6. **REPEAT** - Continue until information is complete
7. **SYNTHESIZE** - Combine all answers before responding to user

## Notebook Role Routing

When a project has paired notebooks (role: research + project), route queries based on intent:

| Question type | Route to | Examples |
|--------------|----------|----------|
| Why / market / users / competitors | `role: research` | "What are the top pain points?", "How do competitors handle X?" |
| What / specs / decisions / versions | `role: project` | "What did we decide about the auth module?", "What's in v2.0?" |
| Unclear | Query both, synthesize | "Give me an overview of where the project stands" |

Agent should check `notebook_manager.py list` for role and paired_with fields to determine routing.

## Script Reference

### Authentication Management (`auth_manager.py`)
```bash
python scripts/run.py auth_manager.py setup    # Initial setup (browser visible)
python scripts/run.py auth_manager.py status   # Check authentication
python scripts/run.py auth_manager.py reauth   # Re-authenticate (browser visible)
python scripts/run.py auth_manager.py clear    # Clear authentication
```

### Notebook Management (`notebook_manager.py`)
```bash
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py notebook_manager.py list
python scripts/run.py notebook_manager.py search --query QUERY
python scripts/run.py notebook_manager.py activate --id ID
python scripts/run.py notebook_manager.py remove --id ID
python scripts/run.py notebook_manager.py stats
```

### Question Interface (`ask_question.py`)
```bash
python scripts/run.py ask_question.py --question "..." [--notebook-id ID] [--notebook-url URL] [--show-browser]
```

### Notebook Guide / Persona (`set_notebook_guide.py`)
```bash
# Set custom persona for a notebook
python scripts/run.py set_notebook_guide.py --persona "You are a senior VC analyst..." [--response-length long] [--notebook-id ID] [--notebook-url URL] [--show-browser]

# Response length options: default, long, short
```
**When to use:** When setting up a new project notebook, or when the user wants to change how NotebookLM responds. The persona shapes answer quality — a well-crafted guide makes responses dramatically more useful.

**Agent workflow:** When creating a new project notebook, auto-generate a persona based on the project's goals and apply it automatically. Store the persona in the project's config for reproducibility.

### Create Notebook (`create_notebook.py`)
```bash
# Create a single notebook
python scripts/run.py create_notebook.py --name "My Notebook" [--role research|project] [--show-browser]

# Create Research + Project pair (recommended for new projects)
python scripts/run.py create_notebook.py --name "ProjectName" --pair [--show-browser]

# Pair with persona tone: default (balanced), vc (investment lens), critic (harsh)
python scripts/run.py create_notebook.py --name "ProjectName" --pair --tone vc [--show-browser]
```
**When to use:** When starting a new project that will use NotebookLM as its knowledge base. The `--pair` mode creates two linked notebooks with auto-configured personas following the planning/execution separation pattern (harness engineering). Use `--tone` to set how critically the personas evaluate your project.

### Add Text Source (`add_source.py`)
```bash
# Add from file
python scripts/run.py add_source.py --file path/to/document.md --notebook-id ID --title "Document Title" [--show-browser]

# Add from text
python scripts/run.py add_source.py --text "content here" --notebook-url URL --title "Title"

# Add from stdin (pipe)
cat document.md | python scripts/run.py add_source.py --notebook-id ID --title "Title"
```
**IMPORTANT:** Always provide `--title` — without it, the source appears as "貼上文字" in NotebookLM's source list, making it impossible to identify. Use a descriptive name (e.g., file name, topic, date).

### Data Cleanup (`cleanup_manager.py`)
```bash
python scripts/run.py cleanup_manager.py                    # Preview cleanup
python scripts/run.py cleanup_manager.py --confirm          # Execute cleanup
python scripts/run.py cleanup_manager.py --preserve-library # Keep notebooks
```

## Environment Management

The virtual environment is automatically managed:
- First run creates `.venv` automatically
- Dependencies install automatically
- Chromium browser installs automatically
- Everything isolated in skill directory

Manual setup (only if automatic fails):
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m patchright install chromium
```

## Data Storage

All data stored in `~/.claude/skills/notebooklm/data/`:
- `library.json` - Notebook metadata
- `auth_info.json` - Authentication status
- `browser_state/` - Browser cookies and session

**Security:** Protected by `.gitignore`, never commit to git.

## Configuration

Optional `.env` file in skill directory:
```env
HEADLESS=false           # Browser visibility
SHOW_BROWSER=false       # Default browser display
STEALTH_ENABLED=true     # Human-like behavior
TYPING_WPM_MIN=160       # Typing speed
TYPING_WPM_MAX=240
DEFAULT_NOTEBOOK_ID=     # Default notebook
```

## Decision Flow

```
User mentions NotebookLM
    ↓
Check auth → python scripts/run.py auth_manager.py status
    ↓
If not authenticated → python scripts/run.py auth_manager.py setup
    ↓
Check/Add notebook → python scripts/run.py notebook_manager.py list/add (with --description)
    ↓
Activate notebook → python scripts/run.py notebook_manager.py activate --id ID
    ↓
Ask question → python scripts/run.py ask_question.py --question "..."
    ↓
See "Is that ALL you need?" → Ask follow-ups until complete
    ↓
Synthesize and respond to user
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError | Use `run.py` wrapper |
| Authentication fails | Browser must be visible for setup! --show-browser |
| Rate limit (50/day) | Wait or switch Google account |
| Browser crashes | `python scripts/run.py cleanup_manager.py --preserve-library` |
| Notebook not found | Check with `notebook_manager.py list` |

## Gotchas (Common Failure Points)

These are real issues encountered during development. Read these BEFORE modifying any script.

### Browser & Authentication
- **Auth MUST use visible browser** — `headless=True` will fail for Google login. Always use `--show-browser` for `auth_manager.py setup`
- **Use `python3` not `python`** — On macOS and RPi, `python` may not exist. Always use `python3` or the `run.py` wrapper
- **Each query = new browser session** — There is NO session persistence between queries. Every `ask_question.py` call opens a fresh browser and closes it after. Include full context in every question
- **`accessrequest` in URL = wrong account** — If the page redirects to an access request page, the `authuser` parameter doesn't match the logged-in account

### Add Source (`add_source.py`)
- **Always provide `--title`** — Without it, the source appears as "貼上的文字" in the source list, making it impossible to identify
- **Don't use the "Add source" button** — The UI button detection is unreliable. Use `?addSource=true` URL parameter instead to open the dialog directly
- **Title input in paste dialog does NOT set the source name** — The `input.title-input` in the paste dialog is cosmetic. The source always defaults to "貼上的文字". We rename it AFTER insertion via the three-dot menu
- **Rename dialog input class is `title-input` not `rename-input`** — The overlay uses `input.title-input` inside `.cdk-overlay-pane`. Using wrong selector silently fails (returns true but doesn't rename)
- **Focus lands on submit button, not input** — After clicking "重新命名來源", the active element is the submit button. Must explicitly `.click()` the input before `.fill()`
- **Multiple sources with same name** — ~~If there are multiple "貼上的文字" sources, `querySelector` always picks the first one.~~ Fixed in v1.3.2: now uses `querySelectorAll` and picks the last (most recently added), with post-rename verification

### DOM & Selectors
- **NotebookLM uses Angular Material CDK** — Overlays, menus, and dialogs are in `.cdk-overlay-pane` containers, NOT inside the main page DOM tree
- **Menu items are `[role="menuitem"]` buttons** — The three-dot menu items (重新命名來源, 移除來源) are buttons with `role="menuitem"` inside overlay panes
- **Tab switching uses `[role="tab"]`** — Three tabs: 來源 (Sources), 對話 (Chat), 工作室 (Studio). Click the tab element directly
- **Textarea injection needs native setter** — Angular's change detection doesn't fire with simple `.value =`. Must use `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set` then dispatch `input` and `change` events
- **Selectors may change without notice** — NotebookLM is actively developed. If a script suddenly fails, check selectors first with `--show-browser`

### Rate Limits & Timing
- **Free tier: ~50 queries/day** — Exceeding this silently fails or returns empty responses
- **Random delays are required** — Without `StealthUtils.random_delay()` between actions, Google may detect automation and block the session
- **Wait 5-7 seconds after Insert** — The source needs processing time before it appears in the source list for renaming

## Source Curation Methodology (Experimentally Validated)

Based on A/B testing conducted 2026-03-20 and weighting experiments conducted 2026-03-22, the following practices improve NotebookLM answer quality. See [`references/weighting-experiment.md`](references/weighting-experiment.md) for the full experiment report with methodology and results.

### Category Prefix System

Use `--category` parameter when adding sources to auto-prefix titles:

```bash
# Auto-prefixes title as "[用戶痛點] Survey results..."
python scripts/run.py add_source.py --category "用戶痛點" --title "Survey results" --text "..."

# Auto-prefixes title as "[競品分析] LingoClip review..."
python scripts/run.py add_source.py --category "競品分析" --title "LingoClip review" --file review.md
```

When querying, reference categories in your question to focus the answer:
```bash
python scripts/run.py ask_question.py --question "Based only on [用戶痛點] sources, what features should we build?"
```

**Tested result:** Category-filtered queries produce more focused answers with direct user quotes. However, this is a "soft constraint" — NotebookLM may still reference other sources. It is not 100% reliable.

### Recommended Category Prefixes

| Prefix | Use For |
|--------|---------|
| `[用戶痛點]` | User pain points, forum discussions, community feedback — sources about **what users need**, not about specific products |
| `[競品分析]` | Competitor App Store reviews (both praise and complaints), feature comparisons, pricing — sources about **how competitors perform** |
| `[學術研究]` | Academic papers, pedagogical research |
| `[市場數據]` | Market size, trends, demographics |
| `[產品規劃]` | Your own product specs, architecture docs |
| `[LIVE]` | Official docs, API references, prompt guides, best practices — **sources that may become outdated**. When results seem off, re-import `[LIVE]` sources first before blaming AI randomness |

**How to choose between `[用戶痛點]` and `[競品分析]`:** Prefixes are for **query filtering**, not content description. Ask: "Is this source telling me what users need, or how a competitor performs?" App Store reviews of competitors → `[競品分析]`. Reddit users describing their own frustrations (without referencing a specific product) → `[用戶痛點]`.

### Source Curation Principles

1. **Sources should complement, not overlap.** Importing a Gemini Deep Research report into NotebookLM alongside NotebookLM's own Deep Research creates redundancy that suppresses unique insights from either source. (Experimentally confirmed: removing the overlapping source revealed different competitors and research that had been "crowded out".)

2. **Deduplicate and weight before adding.** When Agent collects 30 forum posts about the same topic, consolidate into one weighted source (e.g., "Pain Point X — mentioned by 12/30 users, weight: highest") rather than adding all 30 raw posts. NotebookLM's answers reflect the weight annotations in priority ordering.

3. **Keep source count manageable.** Fewer, high-quality curated sources produce better answers than many raw sources. Aim for 5-10 well-structured sources per research topic.

### Weighting Best Practices (Experimentally Validated 2026-03-22)

A 3-round controlled experiment confirmed that embedding weight annotations in source text influences Gemini's answer ranking. Key findings:

1. **Weight tags work:** `[權重:最高]`, `[權重:高]`, `[權重:中]`, `[權重:低]` are read and reflected by Gemini
2. **Pair with source counts:** `[權重:最高 — 8個來源提及]` is more persuasive than tags alone
3. **Spread weights apart:** If two items share `[最高]`, Gemini falls back to its own judgment. Limit `[最高]` to 1-2 items for clear ranking effect
4. **Include "why" explanations:** A `**為何權重最高：**` line after each section increases Gemini's confidence in following the ranking
5. **Gemini may merge related items:** Closely related pain points with similar weights may be combined into a single answer — design sources with this in mind

Full methodology, raw results, and limitations: [`references/weighting-experiment.md`](references/weighting-experiment.md)

### Recommended Source Format

For best results, structure curated sources with:
- Clear headers per topic/pain point
- Weight/frequency annotations (e.g., `[權重:最高 — N個來源提及]`)
- `**為何權重X：**` explanation per section
- Direct quotes with attribution
- Summary/conclusion per section

## Best Practices

1. **Always use run.py** - Handles environment automatically
2. **Check auth first** - Before any operations
3. **Follow-up questions** - Don't stop at first answer
4. **Browser visible for auth** - Required for manual login
5. **Include context** - Each question is independent
6. **Synthesize answers** - Combine multiple responses
7. **Use --category for source organization** - Enables focused querying
8. **Curate before adding** - Deduplicate, weight, and structure sources

## Limitations

- No session persistence (each question = new browser)
- Rate limits on free Google accounts (50 queries/day)
- Manual upload required (user must add docs to NotebookLM)
- Browser overhead (few seconds per question)

## Resources (Skill Structure)

**Important directories and files:**

- `scripts/` - All automation scripts (ask_question.py, notebook_manager.py, etc.)
- `data/` - Local storage for authentication and notebook library
- `references/` - Extended documentation:
  - `api_reference.md` - Detailed API documentation for all scripts
  - `troubleshooting.md` - Common issues and solutions
  - `usage_patterns.md` - Best practices and workflow examples
  - `weighting-experiment.md` - Source weighting A/B test methodology and results
- `.venv/` - Isolated Python environment (auto-created on first run)
- `.gitignore` - Protects sensitive data from being committed
