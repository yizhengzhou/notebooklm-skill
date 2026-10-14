# Agent-direct installation

This repository includes a machine-readable, preview-first installer. A coding
Agent can install Project Brain without the user copying MCP JSON or Skill files
by hand. Discovery entrypoints are provided through `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, GitHub Copilot instructions, and the root README.

## One-pass Agent procedure

```bash
uv sync

.venv/bin/notebooklm-evergreen brain-install-plan \
  --project-root /absolute/path/to/project \
  --client auto

.venv/bin/notebooklm-evergreen brain-install \
  --project-root /absolute/path/to/project \
  --client auto \
  --confirm

.venv/bin/notebooklm-evergreen brain-doctor \
  --project-root /absolute/path/to/project \
  --client auto
```

An explicit user request to install is approval to run `brain-install
--confirm` after the Agent has inspected a conflict-free plan. It is not approval
to select a Notebook, upload sources, or modify global configuration.

## What is installed

### Pi

```text
<project>/.pi/mcp.json
<project>/.agents/skills/project-explainer/SKILL.md
```

### Claude Code

```text
<project>/.mcp.json
<project>/.claude/skills/project-explainer/SKILL.md
```

### Generic Agent Skills + MCP client

```text
<project>/.mcp.json
<project>/.agents/skills/project-explainer/SKILL.md
```

The MCP entry runs the Python environment that executed the installer:

```text
<python> -m notebooklm_skill.mcp_server
```

This avoids relying on shell activation or a globally installed executable.

## Detection

`--client auto` uses:

1. Running Agent environment markers such as `PI_CODING_AGENT`.
2. Existing `.pi/` or `.claude/` project directories.
3. Generic Agent Skills + MCP layout when no client is identifiable.

If multiple client directories exist and the running Agent does not identify
itself, detection stops rather than guessing. Use an explicit `--client`.

## No-clobber behavior

The plan reports each target as `create`, `merge_server`, `unchanged`, or
`conflict`.

- Unrelated MCP servers and top-level config fields are preserved.
- Exact managed content is idempotent.
- A different `mcpServers.project-brain` entry is a conflict.
- A modified destination `project-explainer` Skill is a conflict.
- If one write in the installation fails, earlier writes are rolled back.
- No source, Notebook, manifest, or Advisor mutation occurs.

## Binding the Notebook

Installation and Notebook binding are separate. If `brain-doctor` returns
`needs_brain_init`, first inspect registered Advisors:

```bash
.venv/bin/notebooklm-evergreen list-advisors
```

Then bind an explicitly selected Advisor:

```bash
.venv/bin/notebooklm-evergreen brain-init \
  --project-root /absolute/path/to/project \
  --advisor-id EXPLICIT_ADVISOR_ID
```

Do not choose by “most recent Notebook.” If no suitable Advisor exists, create or
adopt one only after the user approves that choice.

## Doctor result

`brain-doctor` verifies:

- exact MCP configuration;
- exact installed Skill;
- expected server-side MCP tool manifest;
- the exact configured MCP command starts successfully from its configured cwd;
- project-local binding;
- Notebook access and live source capacity;
- grounding readiness.

Doctor launches the exact configured command with closed stdin, so a broken
Python path or missing package fails `installation_ok`. It still does not pretend
that a currently running Agent client has hot-loaded the new configuration.
When `client_reload_required=true`, reload or restart the client,
then call MCP `brain_capabilities` and `brain_health`. Pi project MCP config also
requires the project to be trusted; an untrusted project correctly ignores
`.pi/mcp.json`.

The integration itself is ready when:

```text
installation_ok = true
mcp_tools_ok = true
binding.status = configured
```

`project_explanation_ready=false` is not an installation failure. It means the
separate, reviewed canonical-document onboarding process is still required.
A successful post-reload `brain_capabilities`/`brain_health` call is the final
client-connection proof.

## Uninstall

Preview:

```bash
.venv/bin/notebooklm-evergreen brain-uninstall \
  --project-root /absolute/path/to/project \
  --client auto
```

Apply:

```bash
.venv/bin/notebooklm-evergreen brain-uninstall \
  --project-root /absolute/path/to/project \
  --client auto \
  --confirm
```

Uninstall removes only exact managed MCP and Skill content. It leaves the
manifest, Advisor state, Notebook, and Notebook sources intact. Modified managed
content is not deleted automatically.
