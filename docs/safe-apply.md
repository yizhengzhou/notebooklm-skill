# Safe Apply

Phase 4 separates planning from execution.

## Phase 4A: review only

An Apply Plan binds these facts into a SHA-256 digest:

- Advisor, Notebook, and research task IDs
- complete pre-apply source ID snapshot
- protected/Pinned backend source IDs
- exact additions
- exact retirements and their replacement URLs
- mandatory add-before-delete, readiness, backup, and approval rules

The plan remains `review_required`. Building or writing it has no import or
delete capability. A changed plan has a different digest and requires review
again.

A retirement is rejected when the source is Pinned, absent from the Preview
snapshot, lacks a reason, or points to a replacement that is not in the approved
addition set.

## Phase 4B: execution order

1. Verify the approved plan digest and current source snapshot.
2. Import additions with duplicate protection.
3. Wait until every replacement is ready.
4. Generate a delta summary.
5. Back up each retirement source's metadata and full text.
6. Re-read source state and protected IDs.
7. Delete only explicitly approved retirement IDs.
8. Record actual additions, failures, backups, and deletions.

Any import/readiness/summary/backup/invariant failure stops before deletion. If an
import committed before a later failure, rerunning the same approved plan
reconciles the exact addition URLs and resumes without importing duplicates.
Unexpected, missing, or duplicate source IDs fail closed.
