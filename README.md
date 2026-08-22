# Evergreen Gemini Notebook Skill

A thin, review-first orchestration layer for turning one Gemini Notebook /
NotebookLM notebook into a long-lived, cross-domain research advisor.

The skill delegates Notebook operations to
[`notebooklm-py`](https://github.com/teng-lin/notebooklm-py). It does not maintain
NotebookLM DOM selectors, browser daemons, cookie workarounds, project-folder
scanners, or Git hooks.

## What it does

- Create or adopt one Notebook.
- Apply and read back a custom Persona and response length.
- Persist a Research Profile and assumption/decision/trend/risk Watchlist.
- Run resumable Deep Research previews without mutating sources.
- Rank and selectively import reviewed candidates.
- Protect pinned sources and enforce add-before-delete.
- Back up replaced source content before confirmed retirement.
- Refresh URL/Drive sources with native sync, never delete + re-add.
- Record immutable refresh history and export provider-neutral state.

Personas are domain-neutral: psychology, philosophy, medicine, markets, product,
technology, or any combination. The current `persona` field means NotebookLM
Custom Chat instructions; a separate End-user Persona model is not implemented.
Studio artifact instructions remain separate from the Chat Persona.

## Status and guides

- [Current implementation status and handoff](docs/current-status.md)
- [Complete user guide](docs/user-guide.md)
- [Documentation index](docs/README.md)

The Phase 5D Gauntlet Loop Persona experiment is marked **invalid** and must not
be used as product-value evidence. Its engineering additions remain tested.

## Requirements

- Python 3.11 or 3.12
- `notebooklm-py 0.8.1`
- A Google account that can use NotebookLM

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/notebooklm login
.venv/bin/notebooklm auth check --test --json
```

## Quick start

Create `advisor.json`:

```json
{
  "advisor_id": "market-watch",
  "title": "Market Watch",
  "persona": {
    "instructions": "Act as an evidence-focused market advisor. Separate facts, inference, conflict, and unknowns.",
    "response_length": "longer"
  },
  "research": {
    "enabled": true,
    "brief": "Track meaningful market and competitor changes.",
    "queries": ["What changed recently?", "What challenges our assumptions?"],
    "mode": "deep",
    "language": "zh-Hant",
    "recency_days": 90,
    "max_new_sources_per_run": 10,
    "preferred_domains": [],
    "update_mode": "review",
    "deletion_mode": "confirm"
  },
  "watchlist": []
}
```

Create a Notebook:

```bash
.venv/bin/python -m notebooklm_skill.cli setup --config advisor.json
```

Or adopt an existing one:

```bash
.venv/bin/python -m notebooklm_skill.cli setup \
  --config advisor.json --adopt-notebook-id NOTEBOOK_ID
```

Add and protect a canonical URL seed:

```bash
.venv/bin/python -m notebooklm_skill.cli source-add-url \
  --advisor-id market-watch \
  --url https://example.com/canonical-guide \
  --state pinned
```

Run a non-mutating research preview:

```bash
.venv/bin/python -m notebooklm_skill.cli preview \
  --advisor-id market-watch \
  --run-id preview-20260822 \
  --work-directory ./runs/preview-20260822
```

Build a review plan:

```bash
.venv/bin/python -m notebooklm_skill.cli plan-apply \
  --advisor-id market-watch \
  --plan-id apply-20260822 \
  --preview ./runs/preview-20260822/preview.json \
  --selection ./runs/preview-20260822/selected-urls.json \
  --output-directory ./runs/apply-20260822
```

Apply only after reviewing and approving the exact digest:

```bash
.venv/bin/python -m notebooklm_skill.cli apply \
  --advisor-id market-watch \
  --run-id refresh-20260822 \
  --plan ./runs/apply-20260822/apply-plan.json \
  --approved-digest SHA256 \
  --evidence-directory ./runs/apply-20260822/evidence
```

See [`SKILL.md`](SKILL.md) for the full Agent workflow and
[`docs/`](docs/) for storage, preview, apply, refresh, testing, and local-runtime
contracts.

## Safety model

- **Add before delete**
- **Pinned means protected**
- **Missing is not obsolete**
- **No blind import-all**
- **No silent deletion**
- **Backup before confirmed retirement**
- **Resume/reconcile after timeout**
- **Credentials never enter portable state**

Disposable test resources are automatically cleaned after successful evidence
capture. They are retained only when explicitly converted into a named,
owned regression asset with a documented purpose.

## Storage and portability

Advisor state uses versioned JSON plus Markdown:

```text
advisors/<advisor_id>/
├── profile.json
├── persona.md
├── watchlist.json
├── sources.json
└── refresh-runs/
```

Default root:

- macOS: `~/Library/Application Support/notebooklm-skill/advisors/`
- Linux: `~/.local/share/notebooklm-skill/advisors/`
- Windows: `%LOCALAPPDATA%/notebooklm-skill/advisors/`

Override it with `NOTEBOOKLM_SKILL_HOME`. Exports exclude credentials and are
designed for a future non-Google backend.

## Development

```bash
python3.11 -m pytest -q
python3.12 -m pytest -q
ruff check notebooklm_skill tests
```

The suite is offline and uses an in-memory Fake Backend. Live tests are opt-in,
use disposable resources, and must clean them after PASS.

## Legacy v1

The old Patchright implementation remains in `scripts/` only as migration
reference. It is not part of the v2 runtime contract and is not installed by
`requirements.txt`. Install `requirements-legacy.txt` only when explicitly
maintaining v1.

## Scope

Scheduling (`launchd`, cron, Task Scheduler), an Open Notebook backend, automatic
project-folder upload, Git hooks, and Studio artifact generation are outside the
v2.0 MVP.
