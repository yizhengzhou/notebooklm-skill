---
name: notebooklm
description: >
  Create or adopt a Gemini Notebook / NotebookLM notebook as a cross-domain
  Evergreen Advisor. Configure and verify a custom Persona, persist a Research
  Profile and Watchlist, run resumable Deep Research previews, selectively apply
  approved sources, safely retire replaced sources, refresh URL/Drive sources,
  and export provider-neutral state. Use when the user mentions NotebookLM,
  Gemini Notebook, evergreen research, a long-term AI advisor, source lifecycle,
  Persona, assumption watch, or decision watch.
metadata:
  version: "2.0.0"
---

# Evergreen Gemini Notebook Skill

Build and maintain one long-lived, source-grounded Advisor Notebook. The
`persona` field configures NotebookLM Custom Chat instructions; the current
schema does not separately model an End-user Persona. The instructions may use
any domain or user lens, but never inject a technical role unless the user asks
for one.

## Runtime contract

- Use `notebooklm-py >=0.8.1,<0.9` through `GeminiNotebookBackend`.
- Use `python -m notebooklm_skill.cli ...` as the supported entry point.
- Do not use `scripts/`, Patchright, browser selectors, browser daemons, or the
  old project-folder library for v2 operations.
- Do not scan project folders, install Git hooks, enforce Research/Project pairs,
  or auto-upload commits.
- Chat Persona and Studio artifact generation instructions are separate. Never
  claim that a Chat Persona automatically controls reports, slides, or audio.
- If external web content must be fetched outside NotebookLM's own research
  operation, use Crawl4AI.

## Authentication

Authentication belongs to `notebooklm-py`, not Advisor state:

```bash
notebooklm login
notebooklm auth check --test --json
```

Credentials must never be copied into profile, registry, run, preview, plan, or
export files.

## Create or adopt an Advisor

Prepare an input JSON file:

```json
{
  "advisor_id": "market-watch",
  "title": "Market Watch",
  "persona": {
    "instructions": "Act as an evidence-focused market research advisor. Separate facts, inference, conflict, and unknowns.",
    "response_length": "longer"
  },
  "research": {
    "enabled": true,
    "brief": "Track meaningful market and competitor changes.",
    "queries": ["What changed recently?", "What evidence challenges our assumptions?"],
    "mode": "deep",
    "language": "zh-Hant",
    "recency_days": 90,
    "max_new_sources_per_run": 10,
    "preferred_domains": ["example.com"],
    "update_mode": "review",
    "deletion_mode": "confirm"
  },
  "watchlist": [
    {
      "watch_id": "watch-market",
      "kind": "assumption",
      "statement": "The current market premise remains supported.",
      "questions": ["What new supporting or opposing evidence exists?"],
      "revisit_when": ["A high-quality conflicting source appears"],
      "status": "active"
    }
  ]
}
```

Create a new Notebook and apply/read back the Persona:

```bash
python -m notebooklm_skill.cli setup --config advisor.json
```

Adopt an existing Notebook instead:

```bash
python -m notebooklm_skill.cli setup \
  --config advisor.json \
  --adopt-notebook-id NOTEBOOK_ID
```

Add or reconcile a user-supplied canonical URL and protect it as a seed source:

```bash
python -m notebooklm_skill.cli source-add-url \
  --advisor-id market-watch \
  --url https://example.com/canonical-guide \
  --state pinned
```

The command canonicalizes tracking parameters, waits for `ready`, and writes the
Source Registry only after backend verification. Re-run the same command after a
timeout so it can reconcile an already-created source; never add a blind duplicate.

Adoption registers existing sources as `active`; it never silently pins or
retires them. Pin a core source explicitly:

```bash
python -m notebooklm_skill.cli source-state \
  --advisor-id market-watch --local-id src-ID --state pinned
```

Persona setup failure is a failed setup even when the Notebook was created. Keep
the returned Notebook ID and retry configuration; do not create a duplicate.

Ask a source-grounded question directly or from a UTF-8 file:

```bash
python -m notebooklm_skill.cli ask \
  --advisor-id market-watch \
  --question-file question.md
```

Current limitation: this command returns answer text but does not preserve native
reference objects or expose explicit fresh/follow-up conversation control. Do
not use it as a controlled experiment or citation-audit interface.

## Manual Evergreen cycle

### 1. Preview only

The query is composed from Research Profile, active Watch Items, recency, and
last successful refresh. Preview starts or resumes one Deep Research task and
must not mutate sources.

```bash
python -m notebooklm_skill.cli preview \
  --advisor-id market-watch \
  --run-id preview-20260822 \
  --work-directory ./runs/preview-20260822
```

On timeout, resume with the same run ID and directory. Do not start another
research task.

### 2. Build a reviewed Apply Plan

No retirements:

```bash
python -m notebooklm_skill.cli plan-apply \
  --advisor-id market-watch \
  --plan-id apply-20260822 \
  --preview ./runs/preview-20260822/preview.json \
  --selection ./runs/preview-20260822/selected-urls.json \
  --output-directory ./runs/apply-20260822
```

`selected-urls.json` is an explicitly reviewed JSON array of candidate URLs.
Selection may draw from the complete Preview candidate pool, including items
initially marked `over_budget`, but its size cannot exceed the Preview source
budget. This prevents ranking order from becoming blind import approval.

A retirement file maps a registered local source ID to an approved replacement:

```json
{
  "src-old": {
    "replacement_url": "https://example.com/new",
    "reason": "The approved primary source replaces this non-pinned source."
  }
}
```

Pass it with `--retirements retirements.json`. A pinned source cannot enter a
retirement plan.

### 3. Apply only an exact approved digest

```bash
python -m notebooklm_skill.cli apply \
  --advisor-id market-watch \
  --run-id refresh-20260822 \
  --plan ./runs/apply-20260822/apply-plan.json \
  --approved-digest SHA256 \
  --evidence-directory ./runs/apply-20260822/evidence
```

Required order is add → ready → delta summary → backup → protected-set recheck →
confirmed retirement. Any failure before backup/verification means zero deletes.
Successful execution updates the registry, creates tombstones, and writes one
immutable Refresh Run. Re-running the same run/digest reconciles instead of
creating duplicate history.

## Refresh existing URL or Drive sources

Plan first:

```bash
python -m notebooklm_skill.cli refresh-plan \
  --advisor-id market-watch \
  --plan-id native-refresh-20260822 \
  --output-directory ./runs/native-refresh-20260822
```

Apply an exact approved digest:

```bash
python -m notebooklm_skill.cli refresh-apply \
  --advisor-id market-watch \
  --run-id native-refresh-20260822 \
  --plan ./runs/native-refresh-20260822/refresh-plan.json \
  --approved-digest SHA256 \
  --work-directory ./runs/native-refresh-20260822/execution
```

Use NotebookLM native refresh/sync only. Never implement refresh as delete and
re-add. `missing`, `broken`, `syncing`, or unknown Drive states are warnings,
not deletion evidence. Recheck freshness immediately before execution; if a
stale plan has already auto-synced, record `already_fresh` and perform no RPC.

## Inspect and export

```bash
python -m notebooklm_skill.cli show --advisor-id market-watch
python -m notebooklm_skill.cli export \
  --advisor-id market-watch \
  --destination ./exports/market-watch
```

The export is backend-neutral and excludes credentials. Google Notebook, source,
chat, and artifact IDs are provider references and may not migrate one-to-one.

## Non-negotiable safety rules

1. Add before delete.
2. Pinned means protected.
3. Missing is not obsolete.
4. Never import all research results blindly.
5. Formal source deletion requires an exact reviewed plan and explicit digest.
6. Back up retirement metadata and available full text before deletion.
7. Resume/reconcile after timeout; do not duplicate work.
8. Record uncertain dates or freshness as unknown.
9. Keep credentials separate from portable state.
10. Disposable test resources are cleaned automatically after PASS; retain them
    only after converting them into a named, owned asset with a stated purpose.

## State location

Default Advisor state:

- macOS: `~/Library/Application Support/notebooklm-skill/advisors/`
- Linux: `~/.local/share/notebooklm-skill/advisors/`
- Windows: `%LOCALAPPDATA%/notebooklm-skill/advisors/`

Set `NOTEBOOKLM_SKILL_HOME` to override the root. Tests must always inject a
temporary state root.

## Legacy v1

The old `scripts/` directory is retained only for migration reference. It uses
Patchright and is not part of the v2 runtime contract. Do not modify or invoke it
unless the user explicitly requests legacy v1 maintenance.
