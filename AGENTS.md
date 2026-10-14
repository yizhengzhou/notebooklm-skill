# Agent Installation Contract

This repository is Agent-installable. When the user asks to install, set up,
connect, or enable NotebookLM Project Brain, do not require the user to restate
the steps below.

## Default scope

- Install project-locally by default.
- Never modify user/global Agent configuration unless explicitly requested.
- Never upload, replace, or delete Notebook sources during installation.
- Never guess a Notebook or Advisor.
- Preserve unrelated MCP servers and Agent skills.

## Installation workflow

From this repository:

1. Read `docs/agent-install.md` and `docs/project-brain-pilot.md`.
2. Ensure the package is installed in its local virtual environment:

   ```bash
   uv sync
   # or: python -m pip install -e .
   ```

3. Preview the exact target files and conflicts:

   ```bash
   .venv/bin/notebooklm-evergreen brain-install-plan \
     --project-root /absolute/path/to/target-project \
     --client auto
   ```

4. If the user explicitly requested installation and the plan has no conflicts,
   apply it:

   ```bash
   .venv/bin/notebooklm-evergreen brain-install \
     --project-root /absolute/path/to/target-project \
     --client auto \
     --confirm
   ```

5. Run diagnostics:

   ```bash
   .venv/bin/notebooklm-evergreen brain-doctor \
     --project-root /absolute/path/to/target-project \
     --client auto
   ```

6. If diagnostics say `needs_brain_init`, list registered Advisors. If exactly
   one Advisor was explicitly named by the user, bind it. Otherwise ask the
   user to select or approve creation/adoption; do not infer from recency.

7. Run `brain-doctor` again. Local files/server manifest are correct when
   `installation_ok=true`, `mcp_tools_ok=true`, and binding status is
   `configured`. `project_explanation_ready` may remain false until a separately
   reviewed source onboarding operation is approved.

8. Reload or restart the Agent client when the installer reports
   `client_reload_required=true`. After reload, call MCP `brain_capabilities`
   and `brain_health`. Only that post-reload call proves the client loaded the
   server; `brain-doctor` does not claim to verify the live client connection.

## Supported project-local clients

- `pi`: `.pi/mcp.json` plus portable `.agents/skills/`.
- `claude`: `.mcp.json` plus `.claude/skills/`.
- `generic`: `.mcp.json` plus portable `.agents/skills/`.

`auto` uses the running Agent environment first, then existing client-specific
project directories. Ambiguous detection must stop with a concrete `--client`
choice rather than guessing.

## Safety and rollback

- `brain-install` is preview-first and no-clobber.
- A conflicting `project-brain` server or modified `project-explainer` skill
  blocks installation.
- Multi-file writes roll back if any write fails.
- `brain-uninstall --confirm` removes only exact managed MCP/Skill content. It
  does not delete `.notebooklm/brain.json`, Advisor state, the Notebook, or any
  Notebook source.
- Authentication remains in `notebooklm-py` storage; never copy credentials into
  repository files.

## Development verification

After changing installer behavior, run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check notebooklm_skill tests
git diff --check
```
