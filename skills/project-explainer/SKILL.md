---
name: project-explainer
description: >
  Explain, onboard, recover context for, or create a source-grounded teaching
  treatment of the current software project through its project-local
  NotebookLM Project Brain. Use when asked to explain this project, onboard a
  contributor, recover project context, teach the architecture, or use the
  karpathy-explain preset. Fail closed unless canonical project grounding is
  complete and fresh.
metadata:
  version: "0.1.0"
---

# Project Explainer

Use Project Brain as an advisory source, never as a substitute for reading code,
Git state, tests, and runtime evidence.

## Required preflight

1. Call `brain_discover` from the current project.
2. Call `brain_health`.
3. Inspect `grounding.status` and `grounding.can_explain_project`.
4. Continue with a formal project explanation only when status is
   `project_ready`.

Never guess a Notebook ID or use the most recently selected Notebook.

## If grounding is not ready

For `research_only`, `project_partial`, `project_stale`, or `unknown`:

1. Do not call the result a complete explanation of the project.
2. Call `brain_onboarding_plan`.
3. Personally read the local candidate documents and relevant repository code.
4. Decide whether each candidate is current, canonical, correctly classified,
   and safe to upload. Filename heuristics are suggestions only.
5. Present a concise reviewed sync proposal to the user.
6. Obtain confirmation before any `source-add-file`, replacement, deletion, or
   artifact generation.
7. After approved synchronization, call `brain_grounding_check` again.

## Explanation workflow

1. Read the user's requested scope and audience.
2. Inspect the relevant local files, Git state, tests, and runtime evidence.
3. Call `brain_ask` with `purpose="project_explanation"` and a focused question.
4. Separate:
   - source-backed project facts;
   - local code/runtime verification;
   - inference;
   - unknowns or conflicts.
5. Cite Project Brain sources for NotebookLM-derived factual claims.
6. Do not claim NotebookLM ran code, inspected unuploaded files, or verified
   runtime behavior.

## Default output shape

- What the project does.
- Main architecture and data flow.
- Important invariants and decisions.
- Current implementation status.
- Known risks and unresolved questions.
- How to verify the claims locally.
- Recommended next reading or next action.

## Presets

### `karpathy-explain`

Use layered teaching:

1. one-paragraph intuition;
2. system map or compact ASCII diagram;
3. concrete end-to-end example;
4. major modules and why they exist;
5. failure modes and trade-offs;
6. code paths the reader should inspect;
7. optional visual/artifact proposal.

Do not generate slides, audio, video, infographic, or other artifacts until the
user confirms the artifact plan. The current read-only MCP batch cannot produce
those artifacts; use the future Studio Producer tools when available.

## Stop conditions

Stop and explain the exact remediation when:

- no project-local manifest exists;
- manifest and Advisor state disagree;
- the Notebook cannot be accessed;
- grounding is not `project_ready`;
- required sources are stale;
- local code/runtime evidence materially conflicts with NotebookLM sources.
