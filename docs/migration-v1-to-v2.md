# Migrating from v1 Patchright to v2 Evergreen Advisor

v2 does not migrate the old project-folder library or browser profile. Google
Notebook IDs remain valid and should be adopted through the new backend.

## 1. Install and authenticate the thin runtime

```bash
pip install -r requirements.txt
notebooklm login
notebooklm auth check --test --json
```

Do not copy cookies or files from `data/browser_state/` into Advisor state.

## 2. Prepare an Advisor config

Create the Persona, Research Profile, and Watchlist JSON described in
[`SKILL.md`](../SKILL.md). One old notebook becomes one Advisor. The old forced
Research/Project pair is not recreated unless that structure is genuinely
useful to the user.

## 3. Adopt the existing Notebook

```bash
python -m notebooklm_skill.cli setup \
  --config advisor.json \
  --adopt-notebook-id GOOGLE_NOTEBOOK_ID
```

The Persona is applied and read back. Existing backend sources are registered as
`active`; none are silently pinned, superseded, refreshed, or deleted.

## 4. Pin core sources

Inspect local state and pin only sources that must never enter automatic
retirement:

```bash
python -m notebooklm_skill.cli show --advisor-id ADVISOR_ID
python -m notebooklm_skill.cli source-state \
  --advisor-id ADVISOR_ID --local-id src-ID --state pinned
```

## 5. Run the first preview

The first Evergreen run should be preview-only. Review candidate URLs, source
budget, missing registry entries, and broken sources before building an Apply
Plan.

## Legacy boundary

- `scripts/`, `data/library.json`, and `data/browser_state/` are v1-only.
- `requirements-legacy.txt` is v1-only.
- v2 never invokes Patchright as a fallback.
- Do not delete old local data until adoption and a backend-neutral export have
  been verified.
