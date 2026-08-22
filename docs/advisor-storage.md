# Advisor Storage

Evergreen Advisor state is provider-neutral and separate from Google authentication.

## Default location

- macOS: `~/Library/Application Support/notebooklm-skill/advisors/`
- Linux: `~/.local/share/notebooklm-skill/advisors/`
- Windows: `%LOCALAPPDATA%/notebooklm-skill/advisors/`

Set `NOTEBOOKLM_SKILL_HOME` to override the application data root. The
`advisors/` directory is appended automatically.

Tests and temporary operations must inject an explicit `AdvisorStore(root)` and
must not use the default location.

## Layout

```text
advisors/<advisor_id>/
├── profile.json
├── persona.md
├── watchlist.json
├── sources.json
└── refresh-runs/
    └── <run_id>.json
```

Machine-readable files use schema-versioned JSON. Persona instructions use
UTF-8 Markdown. Writes use a same-directory temporary file, `fsync`, and atomic
replacement while holding an Advisor-specific lock. Refresh Run files are
immutable once created.

Authentication cookies, tokens, passwords, master tokens, and authentication
storage paths are forbidden from Advisor state and exports.

## Portable export

An export is written to a caller-selected, previously nonexistent directory. It
contains JSON, Markdown, immutable Refresh Run records, and a
`source-content/manifest.json`. The user-facing backend-aware export retrieves
readable full text into `<local_id>.txt`, records tombstones without refetching,
and marks unavailable content without fabricating it. `read_export_bundle()`
validates the schema and rejects credential-like keys.
