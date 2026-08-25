"""Gemini Notebook backend implemented with notebooklm-py public APIs."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Literal

from notebooklm import ChatGoal, ChatResponseLength, NotebookLMClient
from notebooklm.research import select_cited_sources

from notebooklm_skill.backend import (
    AskResponse,
    BackendCapabilities,
    ChatConfig,
    CitationReference,
    NotebookRef,
    ResearchCandidate,
    ResearchPollResult,
    ResearchStartRef,
    ResponseLength,
    SourceContent,
    SourceSnapshot,
)
from notebooklm_skill.preview import canonicalize_url

ClientFactory = Callable[[], AbstractAsyncContextManager[Any]]

_RESPONSE_LENGTH_TO_API = {
    "default": ChatResponseLength.DEFAULT,
    "longer": ChatResponseLength.LONGER,
    "shorter": ChatResponseLength.SHORTER,
}
_RESPONSE_LENGTH_FROM_API = {value: key for key, value in _RESPONSE_LENGTH_TO_API.items()}


class PersonaVerificationError(RuntimeError):
    """The server did not read back the requested persona configuration."""


class GeminiNotebookBackend:
    backend_type = "gemini-notebook"
    capabilities = BackendCapabilities()

    def __init__(
        self,
        *,
        profile: str | None = None,
        storage_path: str | None = None,
        client_factory: ClientFactory | None = None,
    ) -> None:
        if profile is not None and storage_path is not None:
            raise ValueError("Use either profile or storage_path, not both")
        self.profile = profile
        self.storage_path = storage_path
        self._client_factory = client_factory or self._default_client_factory

    def _default_client_factory(self) -> AbstractAsyncContextManager[Any]:
        return NotebookLMClient.from_storage(path=self.storage_path, profile=self.profile)

    async def create_notebook(self, title: str) -> NotebookRef:
        if not title.strip():
            raise ValueError("Notebook title cannot be empty")
        async with self._client_factory() as client:
            notebook = await client.notebooks.create(title.strip())
        return NotebookRef(notebook_id=notebook.id, title=notebook.title)

    async def get_notebook(self, notebook_id: str) -> NotebookRef:
        async with self._client_factory() as client:
            notebook = await client.notebooks.get(notebook_id)
        return NotebookRef(notebook_id=notebook.id, title=notebook.title)

    async def configure_chat(
        self,
        notebook_id: str,
        persona: str,
        response_length: ResponseLength = "default",
    ) -> ChatConfig:
        persona = persona.strip()
        if not persona:
            raise ValueError("Persona cannot be empty")
        if len(persona) > 10_000:
            raise ValueError("Persona cannot exceed 10000 characters")
        try:
            api_length = _RESPONSE_LENGTH_TO_API[response_length]
        except KeyError as exc:
            raise ValueError(f"Unsupported response length: {response_length}") from exc

        async with self._client_factory() as client:
            await client.chat.configure(
                notebook_id,
                goal=ChatGoal.CUSTOM,
                response_length=api_length,
                custom_prompt=persona,
            )
            settings = await client.chat.get_settings(notebook_id)

        actual = self._to_chat_config(settings)
        if settings.goal is not ChatGoal.CUSTOM or actual != ChatConfig(persona, response_length):
            raise PersonaVerificationError(
                f"Persona verification failed for notebook {notebook_id}: {actual!r}"
            )
        return actual

    async def get_chat_config(self, notebook_id: str) -> ChatConfig:
        async with self._client_factory() as client:
            settings = await client.chat.get_settings(notebook_id)
        return self._to_chat_config(settings)

    async def list_sources(self, notebook_id: str) -> tuple[SourceSnapshot, ...]:
        async with self._client_factory() as client:
            sources = await client.sources.list(notebook_id)
        return tuple(self._to_source_snapshot(source) for source in sources)

    async def add_text_source(self, notebook_id: str, title: str, content: str) -> SourceSnapshot:
        if not title.strip() or not content.strip():
            raise ValueError("Text source title and content are required")
        async with self._client_factory() as client:
            source = await client.sources.add_text(
                notebook_id,
                title.strip(),
                content.strip(),
                wait=True,
            )
        return self._to_source_snapshot(source, fallback_title=title)

    async def add_url_source(self, notebook_id: str, url: str) -> SourceSnapshot:
        canonical = canonicalize_url(url)
        async with self._client_factory() as client:
            source = await client.sources.add_url(notebook_id, canonical, wait=False)
        return self._to_source_snapshot(source)

    async def start_research(
        self,
        notebook_id: str,
        query: str,
        mode: Literal["fast", "deep"] = "deep",
    ) -> ResearchStartRef:
        if not query.strip():
            raise ValueError("Research query cannot be empty")
        if mode not in {"fast", "deep"}:
            raise ValueError(f"Unsupported research mode: {mode}")
        async with self._client_factory() as client:
            started = await client.research.start(
                notebook_id,
                query.strip(),
                source="web",
                mode=mode,
            )
        task_id = started.report_id or started.task_id
        session_id = started.task_id if started.report_id else None
        return ResearchStartRef(
            task_id=task_id,
            query=started.query,
            mode=mode,
            session_id=session_id,
        )

    async def poll_research(self, notebook_id: str, task_id: str) -> ResearchPollResult:
        async with self._client_factory() as client:
            result = await client.research.poll(notebook_id, task_id=task_id)

        status = result.status.value
        if status == "no_research":
            status = "not_found"
        cited_ids: set[int] = set()
        if status == "completed" and result.report:
            cited_selection = select_cited_sources(result.sources, result.report)
            if not cited_selection.used_fallback:
                cited_ids = {id(item) for item in cited_selection.sources}
        candidates = tuple(
            ResearchCandidate(
                title=source.title,
                url=source.url,
                cited=id(source) in cited_ids,
                ordinal=getattr(source, "source_ordinal", idx + 1),
            )
            for idx, source in enumerate(result.sources)
            if source.url.startswith(("http://", "https://"))
        )
        return ResearchPollResult(
            task_id=result.task_id,
            status=status,
            query=result.query,
            candidates=candidates,
            summary=result.summary,
            report=result.report,
        )

    async def import_research_sources(
        self,
        notebook_id: str,
        task_id: str,
        candidates: tuple[ResearchCandidate, ...],
    ) -> tuple[SourceSnapshot, ...]:
        if not candidates:
            return ()
        payload = [
            {
                "url": candidate.url,
                "title": candidate.title,
                "research_task_id": task_id,
                "source_ordinal": candidate.ordinal,
            }
            for candidate in candidates
        ]
        async with self._client_factory() as client:
            await client.research.import_sources_with_verification(
                notebook_id,
                task_id,
                payload,
                allow_duplicate=False,
            )
            current = await client.sources.list(notebook_id)

        by_url: dict[str, list[Any]] = {}
        for source in current:
            if source.url and source.url.startswith(("http://", "https://")):
                by_url.setdefault(canonicalize_url(source.url), []).append(source)
        resolved: list[SourceSnapshot] = []
        for candidate in candidates:
            matches = by_url.get(canonicalize_url(candidate.url), [])
            if len(matches) != 1:
                raise RuntimeError(
                    f"Expected one imported source for {candidate.url}, found {len(matches)}"
                )
            source = matches[0]
            resolved.append(self._to_source_snapshot(source, fallback_title=candidate.title))
        return tuple(resolved)

    async def wait_source_ready(self, notebook_id: str, source_id: str) -> SourceSnapshot:
        async with self._client_factory() as client:
            source = await client.sources.wait_until_ready(notebook_id, source_id)
        return self._to_source_snapshot(source)

    async def get_source_content(self, notebook_id: str, source_id: str) -> SourceContent:
        async with self._client_factory() as client:
            fulltext = await client.sources.get_fulltext(
                notebook_id,
                source_id,
                output_format="text",
            )
        return SourceContent(
            source_id=fulltext.source_id,
            title=fulltext.title,
            content=fulltext.content,
            url=fulltext.url,
        )

    async def ask(
        self,
        notebook_id: str,
        question: str,
        *,
        conversation_id: str | None = None,
    ) -> AskResponse:
        async with self._client_factory() as client:
            result = await client.chat.ask(notebook_id, question, conversation_id=conversation_id)
        refs: list[CitationReference] = []
        for r in getattr(result, "references", []) or []:
            refs.append(
                CitationReference(
                    source_id=getattr(r, "source_id", ""),
                    citation_number=getattr(r, "citation_number", None),
                    cited_text=getattr(r, "cited_text", None),
                    start_char=getattr(r, "start_char", None),
                    end_char=getattr(r, "end_char", None),
                    chunk_id=getattr(r, "chunk_id", None),
                )
            )
        return AskResponse(
            answer=result.answer,
            conversation_id=getattr(result, "conversation_id", None),
            turn_number=getattr(result, "turn_number", 1),
            references=tuple(refs),
        )

    async def delete_source(self, notebook_id: str, source_id: str) -> None:
        async with self._client_factory() as client:
            await client.sources.delete(notebook_id, source_id)

    async def check_source_freshness(self, notebook_id: str, source_id: str) -> bool:
        async with self._client_factory() as client:
            return await client.sources.check_freshness(notebook_id, source_id)

    async def refresh_source(self, notebook_id: str, source_id: str) -> None:
        async with self._client_factory() as client:
            await client.sources.refresh(notebook_id, source_id)

    @staticmethod
    def _to_source_snapshot(source: Any, fallback_title: str = "") -> SourceSnapshot:
        kind_value = getattr(getattr(source, "kind", None), "value", None)
        status_name = getattr(getattr(source, "status", None), "name", None)
        drive_status_name = getattr(getattr(source, "drive_status", None), "name", None)
        modified = getattr(source, "last_modified_at", None)
        return SourceSnapshot(
            source_id=source.id,
            title=source.title or fallback_title,
            url=getattr(source, "url", None),
            kind=str(kind_value or "unknown"),
            status=str(status_name or "ready").lower(),
            drive_document_id=getattr(source, "drive_document_id", None),
            drive_status=str(drive_status_name).lower() if drive_status_name else None,
            is_drive_degraded=bool(getattr(source, "is_drive_degraded", False)),
            last_modified_at=modified.isoformat() if modified is not None else None,
        )

    @staticmethod
    def _to_chat_config(settings: Any) -> ChatConfig:
        try:
            response_length = _RESPONSE_LENGTH_FROM_API[settings.response_length]
        except KeyError as exc:
            raise PersonaVerificationError(
                f"Unknown response length returned by backend: {settings.response_length!r}"
            ) from exc
        return ChatConfig(
            persona=settings.custom_prompt or "",
            response_length=response_length,
        )
