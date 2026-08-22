# Local Gemini Notebook Runtime

The v2 thin backend uses `notebooklm-py 0.8.1`. First-time authentication uses
an isolated Chromium profile rather than the user's everyday Chrome profile.

## Install

```bash
runtime="$HOME/.local/share/notebooklm-skill/runtime-0.8.1"
python3.12 -m venv "$runtime"
"$runtime/bin/python" -m pip install "notebooklm-py[browser]==0.8.1"
```

## Authenticate

```bash
export NOTEBOOKLM_HOME="$HOME/.local/share/notebooklm-skill/notebooklm-home"
"$runtime/bin/notebooklm" login
"$runtime/bin/notebooklm" auth check --test --json
```

Authentication is accepted only when the check reports both `"status": "ok"`
and `"checks.token_fetch": true`. Credentials remain under `NOTEBOOKLM_HOME`
and must never be committed or copied into an Advisor Profile.

## Install the Skill package and CLI

From the Skill directory:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/notebooklm-evergreen --help
```

The supported v2 entry points are `notebooklm-evergreen` and
`python -m notebooklm_skill.cli`. The old `scripts/run.py` wrapper is legacy v1.

## Persona smoke test

```bash
export NOTEBOOKLM_HOME="$HOME/.local/share/notebooklm-skill/notebooklm-home"
"$runtime/bin/python" -m notebooklm_skill.persona_smoke \
  --title "[Disposable] Persona smoke" \
  --persona-file /path/to/persona.txt \
  --response-length longer
```

The smoke test creates one notebook, configures its custom conversational style,
and reads the settings back. It does not add sources, ask questions, run Deep
Research, or delete the notebook.
