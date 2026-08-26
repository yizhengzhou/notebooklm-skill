"""Stateful orchestration for the user-facing Evergreen Advisor workflow."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from notebooklm_skill.advisor import AdvisorService, AdvisorSetup
from notebooklm_skill.apply_executor import ApplyExecutor, ApplyResult
from notebooklm_skill.apply_plan import verify_apply_plan
from notebooklm_skill.backend import AskResponse, NotebookBackend
from notebooklm_skill.export import export_bundle
from notebooklm_skill.models import (
    AdvisorProfile,
    BackendRef,
    PersonaProfile,
    RefreshRun,
    ResearchProfile,
    SourceRecord,
    WatchItem,
)
from notebooklm_skill.preview import PreviewEngine, PreviewPlan, canonicalize_url
from notebooklm_skill.refresh import (
    RefreshExecutionResult,
    RefreshExecutor,
    RefreshPlan,
    read_refresh_plan,
    update_registry_verification,
)
from notebooklm_skill.storage import AdvisorStore, _atomic_write, _read_json, _write_json


class BackendCapabilityError(RuntimeError):
    pass


class AdvisorPersistenceError(RuntimeError):
    def __init__(self, notebook_id: str, message: str) -> None:
        super().__init__(message)
        self.notebook_id = notebook_id


class SourceRegistrationError(RuntimeError):
    def __init__(self, backend_source_id: str, message: str) -> None:
        super().__init__(message)
        self.backend_source_id = backend_source_id


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compose_research_query(
    profile: ResearchProfile,
    watchlist: tuple[WatchItem, ...],
    runs: tuple[RefreshRun, ...] = (),
) -> str:
    """Compose one evidence-seeking query from persistent profile state."""
    completed = sorted(
        (run.completed_at for run in runs if run.status == "completed" and run.completed_at),
        reverse=True,
    )
    lines = [
        profile.brief.strip(),
        "",
        "Research questions:",
        *(f"- {query.strip()}" for query in profile.queries),
        "",
        f"Prefer evidence from the last {profile.recency_days} days.",
        f"Answer in {profile.language}.",
    ]
    if completed:
        lines.append(f"Identify changes since the last successful refresh: {completed[0]}.")
    active = tuple(item for item in watchlist if item.status == "active")
    if active:
        lines.extend(("", "Watch items to test with supporting and opposing evidence:"))
        for item in active:
            lines.append(f"- [{item.kind}] {item.statement}")
            lines.extend(f"  - Question: {question}" for question in item.questions)
            lines.extend(f"  - Revisit when: {condition}" for condition in item.revisit_when)
    lines.extend(
        (
            "",
            "Prioritize official, primary, or field-recognized high-quality sources.",
            "Separate confirmed changes, likely changes, conflicting evidence, and unknowns.",
            "Do not treat absence from one search as evidence that an assumption is true or false.",
        )
    )
    return "\n".join(lines).strip()


class EvergreenService:
    def __init__(self, backend: NotebookBackend, store: AdvisorStore) -> None:
        self.backend = backend
        self.store = store

    async def setup(
        self,
        *,
        advisor_id: str,
        title: str,
        persona: PersonaProfile,
        research: ResearchProfile,
        watchlist: tuple[WatchItem, ...] = (),
        notebook_id: str | None = None,
    ) -> AdvisorSetup:
        if not self.backend.capabilities.persona_readback:
            raise BackendCapabilityError("Backend cannot verify Persona configuration")
        destination = self.store.advisor_directory(advisor_id)
        if destination.exists():
            raise FileExistsError(f"Advisor already exists: {advisor_id}")
        advisor = AdvisorService(self.backend)
        result = (
            await advisor.adopt(notebook_id, persona.instructions, persona.response_length)
            if notebook_id
            else await advisor.create(title, persona.instructions, persona.response_length)
        )
        profile = AdvisorProfile(
            advisor_id=advisor_id,
            title=title,
            backend=BackendRef(
                type=self.backend.backend_type,
                notebook_id=result.notebook.notebook_id,
            ),
            persona=persona,
            research=research,
        )
        try:
            backend_sources = await self.backend.list_sources(result.notebook.notebook_id)
            used: set[str] = set()
            timestamp = utc_now()
            registry: list[SourceRecord] = []
            for source in backend_sources:
                local_id = self._new_local_id(source.source_id, used)
                used.add(local_id)
                canonical = (
                    canonicalize_url(source.url)
                    if source.url and source.url.startswith(("http://", "https://"))
                    else None
                )
                registry.append(
                    SourceRecord(
                        local_id=local_id,
                        backend_source_id=source.source_id,
                        title=source.title,
                        state="active",
                        origin="manual",
                        url=source.url,
                        canonical_url=canonical,
                        discovered_at=timestamp,
                    )
                )
            self.store.create(profile, watchlist=watchlist, sources=tuple(registry))
        except Exception as exc:
            raise AdvisorPersistenceError(
                result.notebook.notebook_id,
                f"Notebook and Persona exist, but local Advisor persistence failed: {exc}",
            ) from exc
        return result

    async def add_url_source(
        self,
        *,
        advisor_id: str,
        url: str,
        state: str = "active",
    ) -> SourceRecord:
        if not self.backend.capabilities.url_sources:
            raise BackendCapabilityError("Backend does not support URL sources")
        if state not in {"active", "pinned"}:
            raise ValueError("New URL source state must be active or pinned")
        canonical = canonicalize_url(url)
        profile, _, registry = self.store.load(advisor_id)
        current = await self.backend.list_sources(profile.backend.notebook_id)
        current_by_id = {source.source_id: source for source in current}

        registered = [
            source
            for source in registry
            if source.state != "deleted" and source.canonical_url == canonical
        ]
        if len(registered) > 1:
            raise RuntimeError(f"Registry contains duplicate URL source: {canonical}")
        if registered:
            record = registered[0]
            if record.backend_source_id not in current_by_id:
                raise RuntimeError(
                    f"Registered URL source is missing from backend: {record.backend_source_id}"
                )
            if state == "pinned" and record.state != "pinned":
                return self.set_source_state(
                    advisor_id=advisor_id,
                    local_id=record.local_id,
                    state="pinned",
                )
            return record

        matching_backend = [
            source
            for source in current
            if source.url
            and source.url.startswith(("http://", "https://"))
            and canonicalize_url(source.url) == canonical
        ]
        if len(matching_backend) > 1:
            raise RuntimeError(f"Backend contains duplicate URL source: {canonical}")
        if matching_backend:
            ready = await self.backend.wait_source_ready(
                profile.backend.notebook_id,
                matching_backend[0].source_id,
            )
        else:
            created = await self.backend.add_url_source(profile.backend.notebook_id, canonical)
            ready = await self.backend.wait_source_ready(
                profile.backend.notebook_id,
                created.source_id,
            )
        if ready.status != "ready":
            raise RuntimeError(f"URL source did not become ready: {ready.source_id}")
        used = {source.local_id for source in registry}
        record = SourceRecord(
            local_id=self._new_local_id(ready.source_id, used),
            backend_source_id=ready.source_id,
            title=ready.title,
            state=state,
            origin="manual",
            url=ready.url or canonical,
            canonical_url=canonical,
            discovered_at=utc_now(),
            last_verified_at=utc_now(),
        )
        try:
            self.store.save_sources(advisor_id, (*registry, record))
        except Exception as exc:
            raise SourceRegistrationError(
                ready.source_id,
                f"URL source exists, but local registry persistence failed: {exc}",
            ) from exc
        return record

    async def add_text_source(
        self,
        *,
        advisor_id: str,
        title: str,
        content: str,
        state: str = "active",
    ) -> SourceRecord:
        if not self.backend.capabilities.text_sources:
            raise BackendCapabilityError("Backend does not support text sources")
        if state not in {"active", "pinned"}:
            raise ValueError("New text source state must be active or pinned")
        if not title.strip():
            raise ValueError("Text source title is required")
        if not content.strip():
            raise ValueError("Text source content must not be empty")
        profile, _, registry = self.store.load(advisor_id)

        registered = [
            source
            for source in registry
            if source.state != "deleted" and source.url is None and source.title == title
        ]
        if len(registered) > 1:
            raise RuntimeError(f"Registry contains duplicate text source title: {title}")
        if registered:
            record = registered[0]
            current = await self.backend.list_sources(profile.backend.notebook_id)
            current_by_id = {source.source_id: source for source in current}
            if record.backend_source_id not in current_by_id:
                raise RuntimeError(
                    f"Registered text source is missing from backend: {record.backend_source_id}"
                )
            if state == "pinned" and record.state != "pinned":
                return self.set_source_state(
                    advisor_id=advisor_id,
                    local_id=record.local_id,
                    state="pinned",
                )
            return record

        created = await self.backend.add_text_source(profile.backend.notebook_id, title, content)
        ready = await self.backend.wait_source_ready(
            profile.backend.notebook_id,
            created.source_id,
        )
        if ready.status != "ready":
            raise RuntimeError(f"Text source did not become ready: {ready.source_id}")
        used = {source.local_id for source in registry}
        record = SourceRecord(
            local_id=self._new_local_id(ready.source_id, used),
            backend_source_id=ready.source_id,
            title=ready.title,
            state=state,
            origin="manual",
            url=None,
            canonical_url=None,
            discovered_at=utc_now(),
            last_verified_at=utc_now(),
        )
        try:
            self.store.save_sources(advisor_id, (*registry, record))
        except Exception as exc:
            raise SourceRegistrationError(
                ready.source_id,
                f"Text source exists, but local registry persistence failed: {exc}",
            ) from exc
        return record

    def set_source_state(
        self,
        *,
        advisor_id: str,
        local_id: str,
        state: str,
    ) -> SourceRecord:
        if state not in {"active", "pinned", "broken"}:
            raise ValueError("Source state must be active, pinned, or broken")
        _, _, sources = self.store.load(advisor_id)
        matches = [source for source in sources if source.local_id == local_id]
        if len(matches) != 1:
            raise ValueError(f"Expected one local source {local_id!r}, found {len(matches)}")
        updated_record = replace(matches[0], state=state)
        updated = tuple(
            updated_record if source.local_id == local_id else source for source in sources
        )
        self.store.save_sources(advisor_id, updated)
        return updated_record

    async def preview(
        self,
        *,
        advisor_id: str,
        run_id: str,
        work_directory: Path,
        timeout: float = 1800,
    ) -> PreviewPlan:
        if not self.backend.capabilities.deep_research:
            raise BackendCapabilityError("Backend does not support Deep Research previews")
        profile, watchlist, _ = self.store.load(advisor_id)
        query = compose_research_query(
            profile.research,
            watchlist,
            self.store.load_refresh_runs(advisor_id),
        )
        return await PreviewEngine(self.backend).run(
            run_id=run_id,
            advisor_id=advisor_id,
            notebook_id=profile.backend.notebook_id,
            query=query,
            work_directory=work_directory,
            max_new_sources=profile.research.max_new_sources_per_run,
            preferred_domains=profile.research.preferred_domains,
            timeout=timeout,
        )

    async def ask(
        self,
        advisor_id: str,
        question: str,
        *,
        conversation_id: str | None = None,
        fresh: bool = False,
    ) -> AskResponse:
        if not self.backend.capabilities.chat_query:
            raise BackendCapabilityError("Backend does not support Advisor chat queries")
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty")
        if fresh and conversation_id is not None:
            raise ValueError("fresh and conversation_id are mutually exclusive")
        profile, _, _ = self.store.load(advisor_id)
        if fresh:
            existing = await self.backend.get_conversation_id(profile.backend.notebook_id)
            if existing is not None:
                await self.backend.delete_conversation(profile.backend.notebook_id, existing)
        result = await self.backend.ask(
            profile.backend.notebook_id,
            question,
            conversation_id=conversation_id,
        )
        if isinstance(result, str):
            return AskResponse(answer=result)
        return result

    async def export_advisor(self, advisor_id: str, destination: Path) -> dict[str, object]:
        profile, _, sources = self.store.load(advisor_id)
        exported = export_bundle(self.store, advisor_id, destination)
        content_directory = exported / "source-content"
        entries: list[dict[str, object]] = []
        for source in sources:
            if source.state == "deleted":
                entries.append(
                    {
                        "local_id": source.local_id,
                        "backend_source_id": source.backend_source_id,
                        "status": "tombstone",
                    }
                )
                continue
            try:
                content = await self.backend.get_source_content(
                    profile.backend.notebook_id,
                    source.backend_source_id,
                )
                filename = f"{source.local_id}.txt"
                _atomic_write(
                    content_directory / filename,
                    (content.content.rstrip() + "\n").encode(),
                )
                entries.append(
                    {
                        "local_id": source.local_id,
                        "backend_source_id": source.backend_source_id,
                        "status": "exported",
                        "content_file": filename,
                    }
                )
            except Exception as exc:
                entries.append(
                    {
                        "local_id": source.local_id,
                        "backend_source_id": source.backend_source_id,
                        "status": "unavailable",
                        "error_type": type(exc).__name__,
                    }
                )
        _write_json(
            content_directory / "manifest.json",
            {"schema_version": 1, "items": entries},
        )
        return {
            "path": str(exported),
            "exported_sources": sum(item["status"] == "exported" for item in entries),
            "unavailable_sources": sum(item["status"] == "unavailable" for item in entries),
            "tombstones": sum(item["status"] == "tombstone" for item in entries),
        }

    async def apply(
        self,
        *,
        advisor_id: str,
        run_id: str,
        plan_path: Path,
        approved_digest: str,
        evidence_directory: Path,
    ) -> ApplyResult:
        started_at = utc_now()
        profile, watchlist, sources = self.store.load(advisor_id)
        plan = verify_apply_plan(plan_path)
        self._validate_plan_owner(plan, profile)
        if plan["additions"] and not self.backend.capabilities.selective_import:
            raise BackendCapabilityError("Backend does not support selective research import")
        if plan["retirements"] and not self.backend.capabilities.source_delete:
            raise BackendCapabilityError("Backend does not support source retirement")
        result_path = evidence_directory / "execution-result.json"
        result = (
            ApplyResult.from_dict(_read_json(result_path))
            if result_path.exists()
            else await ApplyExecutor(self.backend).execute(
                plan_path=plan_path,
                approved_digest=approved_digest,
                evidence_directory=evidence_directory,
            )
        )
        if result.plan_digest != approved_digest:
            raise ValueError("Apply result digest mismatch")
        if self._run_already_committed(advisor_id, run_id, approved_digest):
            return result

        current = await self.backend.list_sources(profile.backend.notebook_id)
        updated, imported_local, deleted_local = self._reconcile_apply_sources(
            sources,
            current,
            plan,
            imported_source_ids=set(result.imported_source_ids),
            run_id=run_id,
            timestamp=utc_now(),
        )
        run = RefreshRun(
            run_id=run_id,
            advisor_id=advisor_id,
            status="completed",
            started_at=started_at,
            completed_at=utc_now(),
            baseline_source_ids=tuple(str(item) for item in plan["source_snapshot_ids"]),
            research_queries=profile.research.queries,
            watch_items_evaluated=tuple(
                item.watch_id for item in watchlist if item.status == "active"
            ),
            proposed_additions=tuple(str(item["canonical_url"]) for item in plan["additions"]),
            proposed_deletions=tuple(
                str(item["backend_source_id"]) for item in plan["retirements"]
            ),
            approved_actions=(f"apply:{approved_digest}",),
            imported_sources=imported_local,
            deleted_sources=deleted_local,
            summary=result.delta_summary,
        )
        self.store.commit_refresh(advisor_id, sources=updated, run=run)
        return result

    async def commit_native_refresh(
        self,
        *,
        advisor_id: str,
        run_id: str,
        plan: RefreshPlan,
        plan_path: Path,
        approved_digest: str,
        work_directory: Path,
        research_summary: str = "",
    ) -> RefreshExecutionResult:
        if not self.backend.capabilities.native_refresh:
            raise BackendCapabilityError("Backend does not support native source refresh")
        verified_plan = read_refresh_plan(plan_path)
        if verified_plan != plan or plan.digest != approved_digest:
            raise ValueError("Approved digest or Refresh Plan object does not match plan file")
        started_at = utc_now()
        profile, watchlist, sources = self.store.load(advisor_id)
        if plan.advisor_id != advisor_id or plan.notebook_id != profile.backend.notebook_id:
            raise ValueError("Refresh Plan belongs to a different Advisor or Notebook")
        result_path = work_directory / "update-report.json"
        result = (
            RefreshExecutionResult.from_dict(_read_json(result_path))
            if result_path.exists()
            else await RefreshExecutor(self.backend).execute(
                plan_path=plan_path,
                approved_digest=approved_digest,
                work_directory=work_directory,
                research_summary=research_summary,
            )
        )
        if result.plan_digest != approved_digest:
            raise ValueError("Refresh result digest mismatch")
        if self._run_already_committed(advisor_id, run_id, approved_digest):
            return result
        updated = update_registry_verification(
            sources,
            plan,
            verified_at=utc_now(),
            result=result,
        )
        run = RefreshRun(
            run_id=run_id,
            advisor_id=advisor_id,
            status="completed",
            started_at=started_at,
            completed_at=utc_now(),
            baseline_source_ids=plan.source_snapshot_ids,
            research_queries=profile.research.queries,
            watch_items_evaluated=tuple(
                item.watch_id for item in watchlist if item.status == "active"
            ),
            proposed_refreshes=plan.proposed_refresh_ids,
            approved_actions=(f"refresh:{approved_digest}",),
            summary=research_summary.strip() or "Native source freshness cycle completed.",
        )
        self.store.commit_refresh(advisor_id, sources=updated, run=run)
        return result

    def _run_already_committed(self, advisor_id: str, run_id: str, digest: str) -> bool:
        for run in self.store.load_refresh_runs(advisor_id):
            if run.run_id == run_id:
                if any(action.endswith(digest) for action in run.approved_actions):
                    return True
                raise ValueError(f"Refresh run ID already used by another operation: {run_id}")
        return False

    @staticmethod
    def _validate_plan_owner(plan: dict, profile: AdvisorProfile) -> None:
        if plan["advisor_id"] != profile.advisor_id:
            raise ValueError("Apply Plan belongs to a different Advisor")
        if plan["notebook_id"] != profile.backend.notebook_id:
            raise ValueError("Apply Plan belongs to a different Notebook")

    @staticmethod
    def _reconcile_apply_sources(
        registry: tuple[SourceRecord, ...],
        current: tuple,
        plan: dict,
        *,
        imported_source_ids: set[str],
        run_id: str,
        timestamp: str,
    ) -> tuple[tuple[SourceRecord, ...], tuple[str, ...], tuple[str, ...]]:
        retirement_ids = {
            str(item["backend_source_id"]) for item in plan["retirements"]
        }
        updated: list[SourceRecord] = []
        deleted_local: list[str] = []
        for record in registry:
            if record.backend_source_id in retirement_ids:
                if record.state == "pinned":
                    raise ValueError("Pinned source cannot become a tombstone")
                updated.append(replace(record, state="deleted"))
                deleted_local.append(record.local_id)
            else:
                updated.append(record)

        existing_backend_ids = {record.backend_source_id for record in registry}
        additions_by_url = {
            canonicalize_url(str(item["url"])): item for item in plan["additions"]
        }
        used_local_ids = {record.local_id for record in updated}
        imported_local: list[str] = []
        mapped_backend_ids: set[str] = set()
        for source in current:
            if source.source_id in existing_backend_ids or not source.url:
                continue
            addition = additions_by_url.get(canonicalize_url(source.url))
            if addition is None:
                continue
            local_id = EvergreenService._new_local_id(source.source_id, used_local_ids)
            used_local_ids.add(local_id)
            imported_local.append(local_id)
            mapped_backend_ids.add(source.source_id)
            updated.append(
                SourceRecord(
                    local_id=local_id,
                    backend_source_id=source.source_id,
                    title=source.title,
                    state="active",
                    origin="research",
                    url=source.url,
                    canonical_url=canonicalize_url(source.url),
                    discovered_at=timestamp,
                    last_verified_at=timestamp,
                    research_run_id=run_id,
                )
            )
        if mapped_backend_ids != imported_source_ids:
            raise RuntimeError("Imported backend sources could not be reconciled into the registry")
        return tuple(updated), tuple(sorted(imported_local)), tuple(sorted(deleted_local))

    @staticmethod
    def _new_local_id(backend_source_id: str, used: set[str]) -> str:
        stem = re.sub(r"[^a-z0-9]+", "-", backend_source_id.lower()).strip("-")
        base = f"src-{stem[:48]}" if stem else "src-source"
        candidate = base[:64]
        suffix = 2
        while candidate in used:
            tail = f"-{suffix}"
            candidate = f"{base[:64 - len(tail)]}{tail}"
            suffix += 1
        return candidate


def format_answer_with_citations(
    response: AskResponse,
    sources: tuple[SourceRecord, ...] = (),
) -> str:
    """Format the Ask response with structured citation footnotes."""
    output = response.answer.strip()
    if not response.references:
        return output

    source_map = {s.backend_source_id: s for s in sources}
    footnotes: list[str] = ["\n\n---\n\n### 📚 引用出處與原文對照表 (Citations & Highlights)"]

    seen_refs: set[tuple[int | None, str, str | None]] = set()
    for ref in response.references:
        ref_key = (ref.citation_number, ref.source_id, ref.cited_text)
        if ref_key in seen_refs:
            continue
        seen_refs.add(ref_key)

        num_str = f"[{ref.citation_number}]" if ref.citation_number is not None else "[*]"
        src = source_map.get(ref.source_id)
        title = ref.source_title or (src.title if src else None) or ref.source_id
        url_part = f" ({src.url})" if (src and src.url) else ""

        char_info = ""
        if ref.start_char is not None and ref.end_char is not None:
            char_info = f" (字元 {ref.start_char}–{ref.end_char})"

        quote_part = ""
        if ref.cited_text and ref.cited_text.strip():
            cleaned_quote = ref.cited_text.strip().replace("\n", " ")
            if len(cleaned_quote) > 200:
                cleaned_quote = cleaned_quote[:200] + "..."
            quote_part = f'\n  > "{cleaned_quote}"'

        footnotes.append(f"- **{num_str} {title}**{url_part}{char_info}{quote_part}")

    return output + "\n" + "\n".join(footnotes)


def load_setup_document(path: Path) -> tuple[
    str,
    str,
    PersonaProfile,
    ResearchProfile,
    tuple[WatchItem, ...],
]:
    data = json.loads(path.read_text(encoding="utf-8"))
    persona_data = data["persona"]
    research_data = dict(data["research"])
    research_data.setdefault("schema_version", 1)
    return (
        str(data["advisor_id"]),
        str(data["title"]),
        PersonaProfile(
            instructions=str(persona_data["instructions"]),
            response_length=persona_data.get("response_length", "default"),
        ),
        ResearchProfile.from_dict(research_data),
        tuple(WatchItem.from_dict(item) for item in data.get("watchlist", [])),
    )
