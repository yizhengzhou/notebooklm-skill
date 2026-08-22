"""Review-first freshness planning and native source refresh execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

from notebooklm_skill.backend import NotebookBackend, SourceSnapshot
from notebooklm_skill.models import SCHEMA_VERSION, SourceRecord, _validate_id
from notebooklm_skill.preview import canonicalize_url
from notebooklm_skill.storage import _atomic_write, _read_json, _write_json

RefreshVerdict = Literal[
    "fresh",
    "stale",
    "broken",
    "missing",
    "deferred",
    "unknown",
    "check_failed",
    "duplicate",
    "static",
    "registry_conflict",
]


@dataclass(frozen=True)
class RefreshReview:
    source_id: str
    title: str
    verdict: RefreshVerdict
    reason: str
    url: str | None = None
    kind: str = "unknown"
    status: str = "unknown"
    drive_document_id: str | None = None
    drive_status: str | None = None
    registered_state: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "kind": self.kind,
            "status": self.status,
            "drive_document_id": self.drive_document_id,
            "drive_status": self.drive_status,
            "registered_state": self.registered_state,
            "verdict": self.verdict,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RefreshPlan:
    plan_id: str
    advisor_id: str
    notebook_id: str
    source_snapshot_ids: tuple[str, ...]
    reviews: tuple[RefreshReview, ...]
    status: str = "review_required"

    @property
    def proposed_refresh_ids(self) -> tuple[str, ...]:
        return tuple(item.source_id for item in self.reviews if item.verdict == "stale")

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "plan_id": self.plan_id,
            "advisor_id": self.advisor_id,
            "notebook_id": self.notebook_id,
            "source_snapshot_ids": list(self.source_snapshot_ids),
            "reviews": [item.to_dict() for item in self.reviews],
            "status": self.status,
            "safety": {
                "native_refresh_only": True,
                "no_add": True,
                "no_delete": True,
                "missing_is_not_obsolete": True,
                "explicit_approval_required": True,
            },
        }

    @property
    def digest(self) -> str:
        return _digest(self.unsigned_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "plan_digest": self.digest}


@dataclass(frozen=True)
class RefreshExecutionResult:
    plan_digest: str
    refreshed_source_ids: tuple[str, ...]
    already_fresh_source_ids: tuple[str, ...]
    final_source_ids: tuple[str, ...]
    research_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "completed",
            "plan_digest": self.plan_digest,
            "refreshed_source_ids": list(self.refreshed_source_ids),
            "already_fresh_source_ids": list(self.already_fresh_source_ids),
            "final_source_ids": list(self.final_source_ids),
            "research_summary": self.research_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RefreshExecutionResult:
        if data.get("status") != "completed":
            raise ValueError("Refresh result is not completed")
        return cls(
            plan_digest=str(data["plan_digest"]),
            refreshed_source_ids=tuple(str(item) for item in data["refreshed_source_ids"]),
            already_fresh_source_ids=tuple(
                str(item) for item in data["already_fresh_source_ids"]
            ),
            final_source_ids=tuple(str(item) for item in data["final_source_ids"]),
            research_summary=str(data.get("research_summary", "")),
        )


class RefreshPendingError(RuntimeError):
    pass


def update_registry_verification(
    registry: tuple[SourceRecord, ...],
    plan: RefreshPlan,
    *,
    verified_at: str,
    result: RefreshExecutionResult | None = None,
) -> tuple[SourceRecord, ...]:
    """Return registry records with successful freshness evidence timestamped."""
    if not verified_at.strip():
        raise ValueError("verified_at is required")
    verified_ids = {item.source_id for item in plan.reviews if item.verdict == "fresh"}
    if result is not None:
        if result.plan_digest != plan.digest:
            raise ValueError("Refresh result does not belong to this plan")
        verified_ids.update(result.refreshed_source_ids)
        verified_ids.update(result.already_fresh_source_ids)
    return tuple(
        replace(record, last_verified_at=verified_at)
        if record.backend_source_id in verified_ids
        else record
        for record in registry
    )


class RefreshPlanner:
    def __init__(self, backend: NotebookBackend) -> None:
        self.backend = backend

    async def build(
        self,
        *,
        plan_id: str,
        advisor_id: str,
        notebook_id: str,
        registry: tuple[SourceRecord, ...] = (),
    ) -> RefreshPlan:
        _validate_id(plan_id, "plan_id")
        _validate_id(advisor_id, "advisor_id")
        sources = tuple(sorted(await self.backend.list_sources(notebook_id), key=lambda x: x.source_id))
        source_ids = {source.source_id for source in sources}
        registry_by_backend = {source.backend_source_id: source for source in registry}
        if len(registry_by_backend) != len(registry):
            raise ValueError("Source Registry contains duplicate backend source IDs")

        reviews: list[RefreshReview] = []
        seen_handles: set[str] = set()
        for source in sources:
            record = registry_by_backend.get(source.source_id)
            verdict, reason = await self._review_source(
                notebook_id, source, record, seen_handles
            )
            reviews.append(self._review(source, record, verdict, reason))
        for record in sorted(registry, key=lambda x: x.backend_source_id):
            if record.backend_source_id not in source_ids:
                reviews.append(
                    RefreshReview(
                        source_id=record.backend_source_id,
                        title=record.title,
                        url=record.url,
                        kind="unknown",
                        status="missing",
                        registered_state=record.state,
                        verdict="missing",
                        reason="Registry source is absent from backend; missing is not obsolete.",
                    )
                )
        return RefreshPlan(
            plan_id=plan_id,
            advisor_id=advisor_id,
            notebook_id=notebook_id,
            source_snapshot_ids=tuple(sorted(source_ids)),
            reviews=tuple(reviews),
        )

    async def _review_source(
        self,
        notebook_id: str,
        source: SourceSnapshot,
        record: SourceRecord | None,
        seen_handles: set[str],
    ) -> tuple[RefreshVerdict, str]:
        if record is not None and record.state in {"candidate", "deleted", "superseded"}:
            return "registry_conflict", f"Registry state {record.state!r} is not refreshable."
        if record is not None and record.state == "broken":
            return "broken", "Registry already marks this source broken."
        if source.status == "error":
            return "broken", "NotebookLM ingestion status is error."
        if source.status in {"processing", "preparing"}:
            return "deferred", f"NotebookLM ingestion status is {source.status}."
        if source.status not in {"ready"}:
            return "unknown", f"Unknown ingestion status {source.status!r}; refusing refresh."

        if source.drive_status == "syncing":
            return "deferred", "Drive source is already syncing."
        if source.drive_status in {"inaccessible", "deleted", "gen_ai_access_denied"}:
            return "broken", f"Drive health is {source.drive_status}; source is retained."
        if source.drive_status == "unknown":
            return "unknown", "Drive status is unmapped; refusing refresh."
        if source.is_drive_degraded and source.drive_status is None:
            return "unknown", "Drive source is degraded without a named status."

        handle: str | None = None
        if source.drive_document_id:
            handle = f"drive:{source.drive_document_id}"
        elif source.url and source.url.startswith(("http://", "https://")):
            handle = f"url:{canonicalize_url(source.url)}"
        if handle is None:
            return "static", "Static source has no URL or Drive document ID."
        if handle in seen_handles:
            return "duplicate", "Another source has the same canonical URL or Drive document ID."
        seen_handles.add(handle)

        try:
            fresh = await self.backend.check_source_freshness(notebook_id, source.source_id)
        except Exception as exc:
            return "check_failed", f"Freshness check failed: {type(exc).__name__}: {exc}"
        if fresh:
            return "fresh", "Backend reports the source is fresh."
        return "stale", "Backend reports the source needs native refresh."

    @staticmethod
    def _review(
        source: SourceSnapshot,
        record: SourceRecord | None,
        verdict: RefreshVerdict,
        reason: str,
    ) -> RefreshReview:
        return RefreshReview(
            source_id=source.source_id,
            title=source.title,
            url=source.url,
            kind=source.kind,
            status=source.status,
            drive_document_id=source.drive_document_id,
            drive_status=source.drive_status,
            registered_state=record.state if record else None,
            verdict=verdict,
            reason=reason,
        )


class RefreshExecutor:
    def __init__(self, backend: NotebookBackend) -> None:
        self.backend = backend

    async def execute(
        self,
        *,
        plan_path: Path,
        approved_digest: str,
        work_directory: Path,
        research_summary: str = "",
    ) -> RefreshExecutionResult:
        plan = verify_refresh_plan(plan_path)
        if plan["plan_digest"] != approved_digest:
            raise ValueError("Approved digest does not match Refresh Plan")
        result_path = work_directory / "update-report.json"
        if result_path.exists():
            raise FileExistsError("Refresh Plan already has an execution result")
        notebook_id = str(plan["notebook_id"])
        baseline_ids = set(str(item) for item in plan["source_snapshot_ids"])
        current = await self.backend.list_sources(notebook_id)
        if {source.source_id for source in current} != baseline_ids:
            raise RuntimeError("Current sources do not match the approved refresh snapshot")

        checkpoint_path = work_directory / "refresh-checkpoint.json"
        checkpoint = self._load_checkpoint(checkpoint_path, approved_digest)
        attempted = set(checkpoint["attempted_source_ids"])
        completed = set(checkpoint["completed_source_ids"])
        outcomes = dict(checkpoint["outcomes"])
        proposed = tuple(
            str(item["source_id"]) for item in plan["reviews"] if item["verdict"] == "stale"
        )

        for source_id in proposed:
            if source_id in completed:
                continue
            if source_id not in attempted:
                if await self.backend.check_source_freshness(notebook_id, source_id):
                    completed.add(source_id)
                    outcomes[source_id] = "already_fresh"
                    self._save_checkpoint(
                        checkpoint_path, approved_digest, attempted, completed, outcomes
                    )
                    continue
                attempted.add(source_id)
                self._save_checkpoint(
                    checkpoint_path, approved_digest, attempted, completed, outcomes
                )
                await self.backend.refresh_source(notebook_id, source_id)

            await self.backend.wait_source_ready(notebook_id, source_id)
            if not await self.backend.check_source_freshness(notebook_id, source_id):
                raise RefreshPendingError(
                    f"Source {source_id} is still stale; resume from {checkpoint_path}"
                )
            completed.add(source_id)
            outcomes[source_id] = "native_refresh"
            self._save_checkpoint(checkpoint_path, approved_digest, attempted, completed, outcomes)

        final = await self.backend.list_sources(notebook_id)
        final_ids = {source.source_id for source in final}
        if final_ids != baseline_ids:
            raise RuntimeError("Source IDs changed during native refresh")
        result = RefreshExecutionResult(
            plan_digest=approved_digest,
            refreshed_source_ids=tuple(sorted(k for k, v in outcomes.items() if v == "native_refresh")),
            already_fresh_source_ids=tuple(
                sorted(k for k, v in outcomes.items() if v == "already_fresh")
            ),
            final_source_ids=tuple(sorted(final_ids)),
            research_summary=research_summary.strip(),
        )
        work_directory.mkdir(parents=True, exist_ok=True)
        _write_json(result_path, result.to_dict())
        _atomic_write(
            work_directory / "update-report.md",
            _render_update_report(plan, result).encode(),
        )
        return result

    @staticmethod
    def _load_checkpoint(path: Path, digest: str) -> dict[str, Any]:
        if not path.exists():
            return {
                "plan_digest": digest,
                "attempted_source_ids": [],
                "completed_source_ids": [],
                "outcomes": {},
            }
        checkpoint = _read_json(path)
        if checkpoint.get("plan_digest") != digest:
            raise ValueError("Refresh checkpoint digest mismatch")
        return checkpoint

    @staticmethod
    def _save_checkpoint(
        path: Path,
        digest: str,
        attempted: set[str],
        completed: set[str],
        outcomes: dict[str, str],
    ) -> None:
        _write_json(
            path,
            {
                "schema_version": SCHEMA_VERSION,
                "plan_digest": digest,
                "attempted_source_ids": sorted(attempted),
                "completed_source_ids": sorted(completed),
                "outcomes": outcomes,
            },
        )


def read_refresh_plan(path: Path) -> RefreshPlan:
    document = verify_refresh_plan(path)
    return RefreshPlan(
        plan_id=str(document["plan_id"]),
        advisor_id=str(document["advisor_id"]),
        notebook_id=str(document["notebook_id"]),
        source_snapshot_ids=tuple(str(item) for item in document["source_snapshot_ids"]),
        reviews=tuple(
            RefreshReview(
                source_id=str(item["source_id"]),
                title=str(item["title"]),
                verdict=item["verdict"],
                reason=str(item["reason"]),
                url=str(item["url"]) if item.get("url") is not None else None,
                kind=str(item["kind"]),
                status=str(item["status"]),
                drive_document_id=(
                    str(item["drive_document_id"])
                    if item.get("drive_document_id") is not None
                    else None
                ),
                drive_status=(
                    str(item["drive_status"]) if item.get("drive_status") is not None else None
                ),
                registered_state=(
                    str(item["registered_state"])
                    if item.get("registered_state") is not None
                    else None
                ),
            )
            for item in document["reviews"]
        ),
        status=str(document["status"]),
    )


def write_refresh_plan(plan: RefreshPlan, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "refresh-plan.json"
    markdown_path = directory / "refresh-plan.md"
    _write_json(json_path, plan.to_dict())
    _atomic_write(markdown_path, _render_plan(plan).encode())
    return json_path, markdown_path


def verify_refresh_plan(path: Path) -> dict[str, Any]:
    document = _read_json(path)
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported Refresh Plan schema")
    claimed = document.pop("plan_digest", None)
    if claimed != _digest(document):
        raise ValueError("Refresh Plan digest mismatch")
    if document.get("status") != "review_required":
        raise ValueError("Refresh Plan is not awaiting review")
    return {**document, "plan_digest": claimed}


def _digest(document: dict[str, Any]) -> str:
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _render_plan(plan: RefreshPlan) -> str:
    lines = [
        f"# Refresh Plan: {plan.plan_id}",
        "",
        f"- Digest: `{plan.digest}`",
        f"- Proposed native refreshes: **{len(plan.proposed_refresh_ids)}**",
        "- Source additions: **0**",
        "- Source deletions: **0**",
        "",
        "## Source review",
        "",
    ]
    lines.extend(f"- `{item.verdict}` {item.title} (`{item.source_id}`) — {item.reason}" for item in plan.reviews)
    return "\n".join(lines) + "\n"


def _render_update_report(plan: dict[str, Any], result: RefreshExecutionResult) -> str:
    lines = [
        f"# Update Report: {plan['plan_id']}",
        "",
        f"- Plan digest: `{result.plan_digest}`",
        f"- Native refreshes: **{len(result.refreshed_source_ids)}**",
        f"- Reconciled as already fresh: **{len(result.already_fresh_source_ids)}**",
        "- Source additions: **0**",
        "- Source deletions: **0**",
        "",
        "## Freshness review",
        "",
    ]
    lines.extend(
        f"- `{item['verdict']}` {item['title']} (`{item['source_id']}`) — {item['reason']}"
        for item in plan["reviews"]
    )
    lines.extend(("", "## Research cycle", "", result.research_summary or "No research cycle attached."))
    return "\n".join(lines) + "\n"
