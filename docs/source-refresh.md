# Source Refresh

Phase 5 uses NotebookLM's native source freshness and refresh APIs. It never
implements refresh as delete + re-add.

## Review phase

`RefreshPlanner.build()` snapshots the backend source IDs, reconciles the local
Source Registry, and classifies each source:

- `fresh`: URL/Drive source reported fresh.
- `stale`: eligible for an explicitly approved native refresh.
- `broken`: ingestion error or a named degraded Drive state; retained.
- `missing`: registry entry absent from the backend; retained in the registry.
- `deferred`: processing, preparing, or Drive syncing.
- `unknown` / `check_failed`: insufficient evidence; no refresh proposed.
- `duplicate`: same canonical URL or Drive document ID; no add or delete.
- `static`: pasted text or another non-live source.
- `registry_conflict`: registry state is not refreshable.

The generated `refresh-plan.json` has a SHA-256 digest and requires explicit
approval before mutation. `update_registry_verification()` timestamps
`last_verified_at` only for sources with positive freshness evidence: sources
classified fresh, or stale sources successfully reconciled by the executor.

## Apply phase

`RefreshExecutor.execute()`:

1. verifies the approved digest;
2. requires the exact backend source-ID snapshot;
3. rechecks freshness immediately before each operation;
4. writes an attempted-operation checkpoint before calling native refresh;
5. calls `sources.refresh()` without add/delete;
6. waits for ingestion readiness and verifies freshness;
7. verifies that the final source-ID set is unchanged;
8. emits JSON and Markdown update reports.

If a refresh times out after committing, resume checks backend state and does
not call refresh twice. If an attempted operation is still stale, resume stops
with `RefreshPendingError` rather than blindly retrying. A new reviewed plan is
required to retry an unresolved operation.

## Drive safety

Drive health and NotebookLM ingestion status are separate axes. A Drive source
can remain ingestion-ready while its backing file is deleted or inaccessible.
Named degraded Drive states are warnings and are never interpreted as approval
to delete a source. `syncing` is deferred; unmapped states fail closed.

## Update report

The update report combines freshness results with an optional research-cycle
summary. It always states source addition and deletion counts; native refresh
must keep both at zero.
