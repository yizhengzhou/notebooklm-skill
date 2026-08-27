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

### Writing `persona.instructions`

The role sentence has two independent choices, not one — pick both, don't
default to the first idea that comes to mind:

**What domain is this Advisor for?** A few starting points to adapt, not an
exhaustive list:
- *Spec/API tracking*: "...helping an engineering team understand how
  [spec/API] has changed since [baseline version] and what that means for
  an existing integration."
- *Technology evaluation*: "...helping a small team decide whether [a new
  technique/tool] is mature enough to adopt, and under what constraints."
- *Market/competitor research*: "...tracking competitor moves, pricing, and
  industry trends relevant to [product]."
- *Literature/idea genealogy*: "...tracing how [a concept/text] has been
  received, revised, or contested by later work."
- *Project documentation*: "...pointing to the specific decision, spec, or
  past incident behind a question about this project, citing project
  documents directly."
- *Tool/API documentation*: "...always referencing the uploaded official
  documentation and explaining both the recommended usage and the
  underlying reasoning."

**What stance does it take toward the user?** This is a separate choice from
the domain above, and changes the phrasing, not just the topic:
- *Directive/expert* (the default assumed below if unstated): answers
  authoritatively, like a consultant handing over a recommendation.
- *Coach*: asks clarifying questions first, pushes the user toward their own
  conclusion rather than just stating one — e.g. append "Before answering,
  ask me what I've already tried or considered. Help me reach the answer
  rather than just giving it to me."
- *Partner*: thinks alongside the user as a peer rather than from authority
  — e.g. append "Treat this as a working discussion, not a verdict — flag
  where you're uncertain or where reasonable people could disagree."

Nothing about which stance suits which user has been tested — this is an
unvalidated design axis, offered as a choice to make deliberately, not a
claim that any one of these performs better.

**Put in Persona only what must hold for every future question on this
Notebook.** Persona is standing state, not a place to restate something a
single `ask` call could say instead — repeating a rule in both places is how
the Persona/prompt overlap problem in the reports above happened. A rough
test: if you'd be fine with a different answer to this one when the next
question is phrased differently, it belongs in that question, not here.

By that test, **stance and output shape usually belong in the question, not
the Persona** — e.g. "before answering, ask what I've already tried" or
"answer as a table" as part of a specific `ask`, not a permanent Notebook
setting. Only promote either into Persona if you genuinely want it applied
to every future question on this Notebook regardless of how each is phrased
(e.g. a Notebook whose entire purpose is Socratic tutoring).

Two things that do hold for every future question, and so belong in Persona
rather than being repeated per-question:

- **Hedge vs. commit under uncertainty**: the grounding rules below default
  to "say not covered rather than guessing," right for factual claims, but
  some Advisors need a labeled best-effort recommendation even when sources
  are incomplete, rather than one that just declines. If that's the goal for
  this Notebook as a whole, say so once, here — e.g. "When sources are
  incomplete, you may still offer a recommendation, but label it clearly as
  inference, not sourced fact." Decide this on purpose; don't let strict
  grounding silently turn into an Advisor that never commits to anything.
- **Decision-history awareness**: for an Advisor meant to be revisited over
  time (this Skill's Evergreen premise), consider adding "if this answer
  conflicts with a judgment you gave in an earlier session on this Notebook,
  say so explicitly rather than presenting it as new" — this is inherently
  about the Notebook's whole lifetime, not any single question, so a
  per-question instruction can't substitute for it.

Whatever domain and stance you pick, add explicit grounding rules — answer
only from the provided sources, cite every factual claim, say "not covered"
rather than guessing, don't deny text that is actually present in a source,
never claim to have run code or changed files. Example (directive/expert
stance, spec-tracking domain):

```text
Act as a senior technical advisor for an AI coding agent platform team.

1. Answer strictly from the sources in this Notebook only; no outside
   inference or speculation.
2. Cite a source for every factual claim.
3. If a source doesn't cover something, say so explicitly — never guess.
4. Never deny text that is actually present in a source.
5. Never claim to have run code, created files, or deployed anything.
```

This is a starting default, not a validated optimum — recommended because
citing every claim and naming gaps explicitly makes an answer something the
user can actually go check, which is the point of a source-grounded
Advisor, independent of whether it changes any error rate. A controlled
comparison (`docs/reports/2026-08-27-persona-effect-experiment-final-report.md`)
found no measurable difference in fabrication rate between having this text,
a bare role sentence, or no persona at all; the one repeatable difference it
found was that this fuller version produces more structured, checkable
citations. That result is bounded to the handful of cases actually run and
does not generalize — treat it as one data point, not proof this template is
"better," and don't extend its numbers to other questions, sources, or model
versions.

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

Add a local file's content as a text source (no URL required):

```bash
python -m notebooklm_skill.cli source-add-file \
  --advisor-id market-watch \
  --file ./ARCHITECTURE.md \
  --state pinned
```

`--title` defaults to the file name. Reconciliation is keyed on title, not on a
canonical URL — a source of this kind has no URL. Re-run the same command to
reconcile rather than create a duplicate, same as `source-add-url`. This is the
only supported local-file import path; there is no project-folder scan or bulk
importer in v2 (see Legacy v1 below).

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

See "Ask and verify citations" below for structured reference objects and
citation footnotes. Without `--fresh` or `--conversation-id`, `ask` continues
whatever conversation is currently active on the notebook — do not treat
consecutive `ask` calls as independent questions unless you pass `--fresh`
(deletes the existing conversation first, guaranteeing an unrelated turn) or
address a specific `--conversation-id` explicitly.

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

## Ask and verify citations

Ask questions and automatically receive structured citation footnotes with highlighted passage offsets:

```bash
python -m notebooklm_skill.cli ask \
  --advisor-id market-watch \
  --question "What is the primary constraint identified in the sources?"
```

Output includes `answer`, `conversation_id`, `turn_number`, and `formatted_answer` with grounded source quotes and character ranges.

Add `--fresh` when the question must not be influenced by any prior turn on
this notebook (e.g. repeated-trial experiments, self-audit questions): it
deletes the notebook's current conversation before asking, so the next `ask`
starts one with nothing to extend. Add `--conversation-id ID` instead to
address a specific earlier conversation explicitly. `--fresh` and
`--conversation-id` are mutually exclusive.

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
