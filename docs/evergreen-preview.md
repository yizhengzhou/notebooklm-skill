# Evergreen Research Preview

A Preview Run performs Deep Research without importing, refreshing, or deleting
Notebook sources.

## Safety sequence

1. Snapshot current source IDs and metadata.
2. Start one Deep Research task and immediately save its task ID.
3. Poll that exact task ID.
4. On timeout, retain `checkpoint.json`; rerunning the same run resumes it and
   must not start another task.
5. Canonicalize and deduplicate discovered URLs.
6. Rank configured `preferred_domains` first, then cited candidates, and enforce `max_new_sources`.
7. List sources again and fail if the ID set changed.
8. Write `preview.json` and `preview.md` only after the source invariant passes.

The Preview Engine deliberately has no source-import or source-delete method.
Applying a preview belongs to Phase 4 and requires a separate approval gate.

## Live smoke command

```bash
python -m notebooklm_skill.preview_smoke \
  --run-id preview-001 \
  --advisor-id disposable-advisor \
  --notebook-id NOTEBOOK_ID \
  --query-file /path/to/query.txt \
  --work-directory /tmp/evergreen-preview \
  --preferred-domain google.com \
  --preferred-domain googleblog.com
```

The work directory is resumable state. Keep it after a timeout and invoke the
same command again. Changing the run ID, notebook ID, advisor ID, mode, or query
while reusing a checkpoint fails closed.
