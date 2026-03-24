<div align="center">

**[English](README.md)** | **[繁體中文](README.zh-TW.md)**

# NotebookLM Claude Code Skill

**Turn NotebookLM into a per-project AI document manager for Claude Code**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Experimental-orange.svg)]()

> One notebook per project. One persona per domain. Your AI agent gets a dedicated, source-grounded research partner that thinks like the expert you need — VC analyst, software architect, product manager — not a generic chatbot.

> **Note:** This skill is under active development and experimentation by [Fork](https://fork.work). We use it daily in our own projects and are open-sourcing it to share what we've learned. Expect rough edges — contributions and feedback are welcome.

[Installation](#installation) • [Quick Start](#quick-start) • [Notebook Guide](#notebook-guide-persona-configuration) • [Commands](#commands)

</div>

---

## The Idea

Most NotebookLM integrations treat it as a Q&A tool — you ask, it answers.

This skill takes a different approach: **NotebookLM as a per-project document manager.**

Each project gets its own notebook with its own expert persona. Your market research project talks to a VC analyst. Your API docs project talks to a software architect. Your product notebook thinks like a PM. The agent doesn't just retrieve information — it reasons about your documents through the lens of the domain expert you configured.

```
Project A (market research)  → Notebook A → Persona: VC Analyst     → "Entry barrier is low, TAM shows..."
Project B (API migration)    → Notebook B → Persona: Architect       → "This breaks the contract at..."
Project C (user research)    → Notebook C → Persona: Product Manager → "RICE score suggests..."
```

**Key features:**
- **One notebook per project** — bind a notebook ID in your project config, set once
- **Expert personas** — configure how NotebookLM thinks and responds per domain
- **Headless automation** — query and configure notebooks without opening a browser
- **Library management** — tag, search, activate notebooks
- **One-time auth** — log in once, sessions persist

---

## Why NotebookLM?

| Approach | Hallucinations | Setup | Token Cost |
|----------|---------------|-------|------------|
| Feed docs to Claude | Yes — fills gaps with invention | Instant | Very high |
| Web search | High — unreliable sources | Instant | Medium |
| Local RAG | Medium — retrieval gaps | Hours | Medium |
| **NotebookLM Skill** | **Minimal — source-grounded** | **5 min** | **Minimal** |

NotebookLM doesn't retrieve chunks — it **understands** your documents. It correlates across 50+ sources, provides citations, and says "I don't know" instead of hallucinating.

---

## Installation

```bash
cd ~/.claude/skills
git clone https://github.com/yizhengzhou/notebooklm-skill notebooklm
```

Done. On first use, the skill auto-creates a `.venv`, installs dependencies, and sets up Chrome.

**Requirements:** Python 3.8+, local [Claude Code](https://github.com/anthropics/claude-code) (not web UI — sandbox blocks network access)

---

## Quick Start

### 1. Authenticate (one-time)

```
"Set up NotebookLM authentication"
```

A Chrome window opens. Log in with your Google account.

### 2. Create a notebook

Go to [notebooklm.google.com](https://notebooklm.google.com) → Create notebook → Upload your docs (PDFs, Google Docs, websites, YouTube videos).

### 3. Add to library

```
"Add this NotebookLM to my library: https://notebooklm.google.com/notebook/..."
```

### 4. Ask questions

```
"What does my research say about competitive moat analysis?"
```

Claude picks the right notebook, queries it, and uses the answer in context.

---

## Notebook Guide (Persona Configuration)

The most impactful feature. NotebookLM has a **Notebook Guide** setting that defines the AI's role and expertise. Find it at: `Chat → Customize → Notebook guide`. Without it, you get generic answers. With it, you get domain-expert analysis.

### The difference

| Without Guide | With Guide |
|--------------|------------|
| "Here are some market trends from your docs..." | "Based on the TAM/SAM analysis in your research, the addressable market shows a 23% gap in the utility app segment. Cross-referencing with the competitive density data, entry difficulty scores below 30, indicating a viable window for an MVP-first approach." |

### Usage

```bash
# Set persona via CLI
python scripts/run.py set_notebook_guide.py \
  --persona "You are a senior VC analyst..." \
  --response-length long \
  --notebook-id my-research

# Or just tell Claude
"Set the notebook guide to act as a VC analyst specializing in mobile app markets"
```

**Arguments:**
| Flag | Required | Description |
|------|----------|-------------|
| `--persona` | Yes | Role/expertise description (max 10,000 chars) |
| `--response-length` | No | `default`, `long`, or `short` |
| `--notebook-url` | No | Target notebook URL |
| `--notebook-id` | No | Notebook ID from library |
| `--show-browser` | No | Show browser for debugging |

### Persona Templates

**Market Research / VC Analyst:**
```
You are a senior venture capital analyst and think tank strategist.
Your knowledge base contains market research, trend reports, and competitive analysis.
You evaluate opportunities using investment frameworks: TAM/SAM/SOM sizing,
competitive moat analysis, and unit economics validation.
When answering, challenge assumptions — ask whether the data is asking the right
questions rather than accepting surface-level conclusions.
All recommendations should target MVP validation with measurable outcomes.
```

**Technical Architecture Reviewer:**
```
You are a principal software architect with 15 years of experience in distributed systems.
Your knowledge base contains API documentation, system design specs, and technical RFCs.
Evaluate technical decisions through the lens of: scalability, maintainability,
operational cost, and team capability constraints.
Flag anti-patterns and suggest alternatives with concrete trade-off analysis.
```

**Product Manager:**
```
You are a senior product manager focused on user-centric design and data-driven decisions.
Your knowledge base contains user research, analytics reports, and product specs.
Prioritize insights using RICE scoring (Reach, Impact, Confidence, Effort).
Always ground recommendations in user behavior data, not assumptions.
```

### Scaling: Dual-Notebook Architecture (Harness Engineering)

Inspired by the [harness engineering](https://openai.com/index/harness-engineering/) pattern of separating planning from execution, we recommend creating a **Research + Project notebook pair** for each project:

```bash
python scripts/run.py create_notebook.py --name "MyProject" --pair
```

This creates:
- **[Research] MyProject** — market research, user pain points, competitor analysis
- **[Project] MyProject** — product specs, version history, technical decisions

```
MyProject
├── [Research] Notebook     → Persona: Market Analyst
│   └── Why we're building this, who needs it, what competitors do
└── [Project] Notebook      → Persona: Product Manager
    └── What we're building, decisions made, version history
```

**Why separate?** When asking "what are the top pain points?", you want answers from research sources — not mixed with technical specs. When asking "what did we decide about auth?", you want project decisions — not competitor reviews. Role-based routing keeps answers focused.

**Bonus:** The Project notebook doubles as a living pitch deck — use NotebookLM's built-in Audio Overview to generate project introductions for investors, clients, or team onboarding.

#### Persona Tone Presets

The `--pair` command auto-configures personas for both notebooks. Choose a tone that fits your project stage:

```bash
# Balanced (default) — supportive analysis with evidence-based challenges
python scripts/run.py create_notebook.py --name "MyProject" --pair

# VC lens — evaluates like an investor (TAM/SAM, moats, unit economics)
python scripts/run.py create_notebook.py --name "MyProject" --pair --tone vc

# Harsh critic — finds fatal flaws, assumes optimism is wrong until proven
python scripts/run.py create_notebook.py --name "MyProject" --pair --tone critic
```

| Tone | Research Persona | Project Persona | Best for |
|------|-----------------|-----------------|----------|
| `default` | Market research analyst | Product manager | Active development |
| `vc` | VC analyst (investment lens) | VC partner (execution review) | Fundraising, pitch prep |
| `critic` | Brutal market critic | Ruthless technical reviewer | Pre-launch stress testing |

**Customize after creation:** These are starting points. Change the persona anytime with:

```bash
python scripts/run.py set_notebook_guide.py --persona "Your custom persona..." --notebook-id ID
```

### Best Practices

1. **Be specific about the role** — "senior VC analyst" > "helpful assistant"
2. **Reference the knowledge base** — Tell it what kind of documents are uploaded
3. **Define the analysis framework** — TAM/SAM, RICE, SWOT, etc.
4. **Set the challenge level** — Should it agree or push back on assumptions?
5. **Align with output format** — What kind of answers does your project need?
6. **Split large projects** — One notebook per feature/domain when source limits are hit

### Project Integration

Store the persona in your project config for automatic setup:

```python
# config.py or .env
NOTEBOOKLM_NOTEBOOK_ID = "your-notebook-id"
NOTEBOOKLM_PERSONA = """Your persona description..."""
NOTEBOOKLM_RESPONSE_LENGTH = "long"
```

When an agent sets up a new project, it auto-generates a persona based on the project's goals, stores it in config, and applies it via `set_notebook_guide.py`.

---

## Commands

| What you say | What happens |
|---|---|
| "Set up NotebookLM authentication" | Opens Chrome for Google login |
| "Add [link] to my NotebookLM library" | Saves notebook with metadata |
| "Show my NotebookLM notebooks" | Lists all saved notebooks |
| "Ask my docs about [topic]" | Queries the relevant notebook |
| "Use the [name] notebook" | Sets active notebook |
| "Set notebook guide to act as [role]" | Configures notebook persona |
| "Clear NotebookLM data" | Fresh start (keeps library) |

### Script Reference

```bash
# Query
python scripts/run.py ask_question.py --question "..." [--notebook-id ID] [--show-browser]

# Set persona
python scripts/run.py set_notebook_guide.py --persona "..." [--response-length long] [--notebook-id ID]

# Library management
python scripts/run.py notebook_manager.py list
python scripts/run.py notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py notebook_manager.py activate --id ID
python scripts/run.py notebook_manager.py remove --id ID

# Authentication
python scripts/run.py auth_manager.py setup    # Initial setup
python scripts/run.py auth_manager.py status   # Check auth
python scripts/run.py auth_manager.py reauth   # Re-authenticate
```

---

## Architecture

```
~/.claude/skills/notebooklm/
├── SKILL.md                      # Instructions for Claude Code
├── scripts/
│   ├── run.py                    # Entry point (auto-creates venv)
│   ├── ask_question.py           # Query NotebookLM
│   ├── set_notebook_guide.py     # Configure notebook persona
│   ├── notebook_manager.py       # Library management
│   ├── auth_manager.py           # Google authentication
│   ├── browser_utils.py          # Browser factory + stealth utils
│   ├── browser_session.py        # Session management
│   └── config.py                 # Selectors, paths, constants
├── data/                         # Local storage (git-ignored)
│   ├── library.json              # Notebook metadata
│   ├── auth_info.json            # Auth status
│   └── browser_state/            # Browser profile + cookies
└── .venv/                        # Isolated Python env (auto-created)
```

**How it works:**
1. Claude Code loads `SKILL.md` when you mention NotebookLM
2. Runs the appropriate Python script via `run.py`
3. Patchright opens a headless Chrome with persistent auth
4. Interacts with NotebookLM's DOM (type question, read answer, configure settings)
5. Returns the result to Claude Code

**Tech stack:**
- [Patchright](https://github.com/nickhath/patchright) — Playwright fork with anti-detection
- Real Chrome (not Chromium) — better Google service compatibility
- Human-like interaction patterns — realistic typing, random delays

---

## Recommended Workflow: NotebookLM as Project Document Hub

We built this skill around a specific philosophy: **NotebookLM should be the single source of truth for your project's accumulated knowledge.**

Instead of searching through scattered markdown files, git logs, and chat histories, upload key documents to NotebookLM as they are created. Over time, your notebook becomes a queryable knowledge base of your project's full development history.

### How it works in practice

```
You write a document (spec, research, meeting notes, architecture decision)
    ↓
Upload it to NotebookLM via add_source.py
    ↓
Tag it with a category prefix: [產品規劃], [用戶研究], [競品分析], etc.
    ↓
Later, ask your notebook instead of digging through files:
  "What decisions did we make about the auth module and why?"
  "Based on [用戶研究] sources, what are the top 3 pain points?"
```

### Tips for source management

- **Upload as you go** — each new document requires one `add_source.py` call. There is no auto-sync (yet).
- **Consolidate before uploading** — 30 small notes about the same topic should become 1 structured source with weight annotations, not 30 separate uploads.
- **Use category prefixes** — prefix source titles with `[Category]` (e.g., `[用戶痛點] Forum analysis`). When querying, reference the category to focus answers.
- **Stay under the source limit** — each notebook supports up to 50 sources. Quality over quantity.
- **No update-in-place** — to update a source, remove the old one and re-add it.

### Category prefix examples

| Prefix | Use for |
|--------|---------|
| `[用戶痛點]` | User pain points, forum discussions, feedback |
| `[競品分析]` | Competitor reviews, feature comparisons |
| `[學術研究]` | Academic papers, pedagogical research |
| `[市場數據]` | Market size, trends, demographics |
| `[產品規劃]` | Product specs, architecture docs, decisions |

```bash
# Upload with category
python scripts/run.py add_source.py \
  --category "產品規劃" \
  --title "Auth module architecture decision" \
  --file docs/auth-decision.md \
  --notebook-id my-project

# Query by category
python scripts/run.py ask_question.py \
  --question "Based only on [產品規劃] sources, what architecture decisions have we made?" \
  --notebook-id my-project
```

### Source freshness: the `[LIVE]` convention

NotebookLM captures a source's content at upload time. If the original document updates (e.g., an API reference, a prompt engineering guide, a framework's best practices), NotebookLM **does not** re-fetch it. Your notebook silently becomes stale.

This is especially dangerous for sources that directly shape agent behavior — for example, if you uploaded a model's recommended prompt format and that format later changed, the agent will keep producing suboptimal prompts. You're likely to blame "AI randomness" rather than realizing your reference material is outdated.

**Convention:** When adding sources that are likely to change over time, prefix them with `[LIVE]`:

```bash
python scripts/run.py add_source.py \
  --category "LIVE" \
  --title "NanoBanana prompt guide" \
  --file nanob-guide.md \
  --notebook-id my-project
```

This is a naming convention only — there is no automatic refresh yet. But it serves as a visual reminder when you browse your source list: anything tagged `[LIVE]` should be periodically checked and re-imported if the original has changed.

---

## Limitations

- **Local Claude Code only** — web UI sandbox blocks network access
- **No session persistence** — each question opens a fresh browser
- **NotebookLM rate limits** — free tier has daily query limits
- **Manual upload** — each document requires an `add_source.py` call (no auto-sync yet)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Skill not found | Verify `~/.claude/skills/notebooklm/SKILL.md` exists |
| Authentication fails | `"Reset NotebookLM authentication"` |
| Browser crashes | `"Clear NotebookLM browser data"` |
| Rate limited | Wait or switch Google account |
| Dependencies broken | Delete `.venv/`, next run auto-recreates it |

---

## Security

- All data stays local on your machine
- Google credentials stored in `data/browser_state/` (git-ignored)
- No external API calls — only browser automation to notebooklm.google.com
- Recommended: use a dedicated Google account for automation

---

## Roadmap

Features we're planning but haven't built yet:

- **Source Export (`export_sources.py`)** — Download all sources from a notebook back to your local project folder. Insurance against Google's [track record](https://killedbygoogle.com/) of shutting down free services. Your knowledge shouldn't be locked inside any single platform.

- **Live Source Refresh (`refresh_sources.py`)** — Some sources are "alive" (industry blogs, official docs, trend reports) — their content updates over time, but NotebookLM only captures what was there when you first added them. This feature would let you tag sources as `[LIVE]`, then periodically re-import them so your notebook's knowledge stays current. Turns NotebookLM from a static archive into a living knowledge base.

---

## Credits

- [NotebookLM MCP Server](https://github.com/PleasePrompto/notebooklm-mcp) by **PleasePrompto** — the original implementation that inspired this skill
- **[@blazingzebra](https://x.com/blazingzebra)** — the category prefix technique for organizing NotebookLM sources
- **[@Tool_Drop_1](https://youtube.com/@Tool_Drop_1)** — NotebookLM tips and workflows
- **[Steven Johnson](https://x.com/stevenbjohnson)** — NotebookLM Editorial Director, whose vision for the product shaped how we think about source-grounded AI

---

## License

MIT

</div>
