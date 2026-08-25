"""Fail-closed execution of an explicitly approved Apply Plan."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from notebooklm_skill.apply_plan import verify_apply_plan
from notebooklm_skill.backend import NotebookBackend, ResearchCandidate, SourceSnapshot
from notebooklm_skill.preview import canonicalize_url
from notebooklm_skill.storage import _atomic_write, _write_json


@dataclass(frozen=True)
class ApplyResult:
    plan_digest: str
    imported_source_ids: tuple[str, ...]
    deleted_source_ids: tuple[str, ...]
    protected_source_ids: tuple[str, ...]
    final_source_ids: tuple[str, ...]
    delta_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_digest": self.plan_digest,
            "imported_source_ids": list(self.imported_source_ids),
            "deleted_source_ids": list(self.deleted_source_ids),
            "protected_source_ids": list(self.protected_source_ids),
            "final_source_ids": list(self.final_source_ids),
            "delta_summary": self.delta_summary,
            "status": "completed",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApplyResult:
        if data.get("status") != "completed":
            raise ValueError("Apply result is not completed")
        return cls(
            plan_digest=str(data["plan_digest"]),
            imported_source_ids=tuple(str(item) for item in data["imported_source_ids"]),
            deleted_source_ids=tuple(str(item) for item in data["deleted_source_ids"]),
            protected_source_ids=tuple(str(item) for item in data["protected_source_ids"]),
            final_source_ids=tuple(str(item) for item in data["final_source_ids"]),
            delta_summary=str(data["delta_summary"]),
        )


class ApplyExecutor:
    def __init__(self, backend: NotebookBackend) -> None:
        self.backend = backend

    async def execute(
        self,
        *,
        plan_path: Path,
        approved_digest: str,
        evidence_directory: Path,
    ) -> ApplyResult:
        result_path = evidence_directory / "execution-result.json"
        if result_path.exists():
            raise FileExistsError("Apply Plan already has an execution result")
        plan = verify_apply_plan(plan_path)
        if plan["plan_digest"] != approved_digest:
            raise ValueError("Approved digest does not match Apply Plan")

        notebook_id = str(plan["notebook_id"])
        baseline_ids = set(str(item) for item in plan["source_snapshot_ids"])
        protected_ids = set(str(item) for item in plan["protected_source_ids"])
        retirement_ids = {
            str(item["backend_source_id"]) for item in plan["retirements"]
        }
        if protected_ids & retirement_ids:
            raise ValueError("Apply Plan attempts to retire a protected source")

        current = await self.backend.list_sources(notebook_id)
        current_ids = {item.source_id for item in current}
        if not baseline_ids <= current_ids:
            raise RuntimeError("Current sources are missing entries from the approved snapshot")

        additions = tuple(
            ResearchCandidate(
                title=str(item["title"]),
                url=str(item["url"]),
                cited=bool(item["cited"]),
            )
            for item in plan["additions"]
        )
        imported = self._resolve_existing_additions(current, additions)
        if current_ids == baseline_ids:
            imported = await self.backend.import_research_sources(
                notebook_id,
                str(plan["research_task_id"]),
                additions,
            )
        elif set(item.source_id for item in imported) != current_ids - baseline_ids:
            raise RuntimeError("Current sources contain changes outside the approved additions")
        if len(imported) != len(additions):
            raise RuntimeError("Not every approved addition was imported exactly once")

        ready = tuple(
            [
                await self.backend.wait_source_ready(notebook_id, source.source_id)
                for source in imported
            ]
        )
        if {source.source_id for source in ready} != {source.source_id for source in imported}:
            raise RuntimeError("Ready source IDs do not match imported source IDs")

        after_import = await self.backend.list_sources(notebook_id)
        expected_after_import = baseline_ids | {source.source_id for source in imported}
        if {source.source_id for source in after_import} != expected_after_import:
            raise RuntimeError("Source state changed unexpectedly after import")
        if not protected_ids <= expected_after_import:
            raise RuntimeError("A protected source disappeared before summary")

        evidence_directory.mkdir(parents=True, exist_ok=True)
        summary_path = evidence_directory / "delta-summary.md"
        if summary_path.is_file() and summary_path.read_text(encoding="utf-8").strip():
            summary = summary_path.read_text(encoding="utf-8").strip()
        else:
            ask_res = await self.backend.ask(
                notebook_id,
                "根據目前所有來源，說明本次新加入來源相對於既有來源帶來哪些變化。"
                "區分已確認事實、推論、衝突與未知資訊，並指出仍需查證的部分。",
            )
            summary = ask_res.answer if hasattr(ask_res, "answer") else str(ask_res)
            _atomic_write(summary_path, (summary.strip() + "\n").encode())

        backups: dict[str, tuple[Path, Path]] = {}
        source_by_id = {source.source_id: source for source in after_import}
        for retirement in plan["retirements"]:
            source_id = str(retirement["backend_source_id"])
            if source_id not in source_by_id:
                raise RuntimeError(f"Retirement source disappeared before backup: {source_id}")
            content = await self.backend.get_source_content(notebook_id, source_id)
            if not content.content.strip():
                raise RuntimeError(f"Retirement source backup is empty: {source_id}")
            stem = "source-" + hashlib.sha256(source_id.encode()).hexdigest()[:16]
            metadata_path = evidence_directory / "source-backups" / f"{stem}.json"
            content_path = evidence_directory / "source-backups" / f"{stem}.txt"
            _write_json(
                metadata_path,
                {
                    "source_id": source_id,
                    "title": content.title,
                    "url": content.url,
                    "content_file": content_path.name,
                    "content_sha256": hashlib.sha256(content.content.encode()).hexdigest(),
                    "plan_digest": approved_digest,
                },
            )
            _atomic_write(content_path, (content.content.rstrip() + "\n").encode())
            backups[source_id] = (metadata_path, content_path)

        before_delete = await self.backend.list_sources(notebook_id)
        if {source.source_id for source in before_delete} != expected_after_import:
            raise RuntimeError("Source state changed after backup; refusing deletion")
        if not protected_ids <= {source.source_id for source in before_delete}:
            raise RuntimeError("A protected source disappeared; refusing deletion")
        if set(backups) != retirement_ids or not all(
            metadata.is_file() and content.is_file() for metadata, content in backups.values()
        ):
            raise RuntimeError("Retirement backup invariant failed")

        for source_id in sorted(retirement_ids):
            await self.backend.delete_source(notebook_id, source_id)

        final_sources = await self.backend.list_sources(notebook_id)
        final_ids = {source.source_id for source in final_sources}
        expected_final = expected_after_import - retirement_ids
        if final_ids != expected_final:
            raise RuntimeError("Post-delete source verification failed")
        if not protected_ids <= final_ids:
            raise RuntimeError("Protected source verification failed after deletion")

        result = ApplyResult(
            plan_digest=approved_digest,
            imported_source_ids=tuple(sorted(source.source_id for source in imported)),
            deleted_source_ids=tuple(sorted(retirement_ids)),
            protected_source_ids=tuple(sorted(protected_ids)),
            final_source_ids=tuple(sorted(final_ids)),
            delta_summary=summary,
        )
        _write_json(result_path, result.to_dict())
        return result

    @staticmethod
    def _resolve_existing_additions(
        current: tuple[SourceSnapshot, ...],
        additions: tuple[ResearchCandidate, ...],
    ) -> tuple[SourceSnapshot, ...]:
        by_url: dict[str, list[SourceSnapshot]] = {}
        for source in current:
            if source.url and source.url.startswith(("http://", "https://")):
                by_url.setdefault(canonicalize_url(source.url), []).append(source)
        resolved: list[SourceSnapshot] = []
        for addition in additions:
            matches = by_url.get(canonicalize_url(addition.url), [])
            if len(matches) > 1:
                raise RuntimeError(f"Addition URL is duplicated in Notebook: {addition.url}")
            if matches:
                resolved.append(matches[0])
        return tuple(resolved)
