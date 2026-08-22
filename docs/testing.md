# Testing

The default suite is fully offline. It does not authenticate with Google, open a
browser, create a Notebook, or consume Deep Research quota.

## Setup

```bash
python3 -m venv /tmp/notebooklm-skill-dev-venv
source /tmp/notebooklm-skill-dev-venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Run

```bash
python -m pytest -q
ruff check notebooklm_skill tests
python -m compileall -q notebooklm_skill tests
git diff --check
```

GitHub Actions runs pytest and Ruff on Python 3.11 and 3.12. Tests cover the
Fake Backend and Gemini adapter contract, profile storage/export, Persona setup,
resumable preview, safe apply, source refresh, formal registry/run commits, and
the user-facing CLI.

## Package and CLI smoke

```bash
python -m pip install -e .
notebooklm-evergreen --help
python -m notebooklm_skill.cli --help
```

## Live E2E

Live tests are opt-in because they may consume Deep Research quota or mutate
Google resources. Every Gate must state the exact resource and quota budget.
Disposable resources are included in the same approval as creation and are
automatically cleaned after PASS once evidence has been exported. On FAIL they
may remain temporarily only with a documented debugging purpose and cleanup
condition.
