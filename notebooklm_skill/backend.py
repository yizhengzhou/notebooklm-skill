"""Provider-neutral backend contract used by the thin skill."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

ResponseLength = Literal["default", "longer", "shorter"]


@dataclass(frozen=True)
class BackendCapabilities:
    persona_readback: bool = True
    deep_research: bool = True
    selective_import: bool = True
    native_refresh: bool = True
    source_delete: bool = True
    url_sources: bool = True
    chat_query: bool = True


@dataclass(frozen=True)
class NotebookRef:
    notebook_id: str
    title: str


@dataclass(frozen=True)
class ChatConfig:
    persona: str
    response_length: ResponseLength


@dataclass(frozen=True)
class SourceSnapshot:
    source_id: str
    title: str
    url: str | None = None
    kind: str = "unknown"
    status: str = "ready"
    drive_document_id: str | None = None
    drive_status: str | None = None
    is_drive_degraded: bool = False
    last_modified_at: str | None = None


@dataclass(frozen=True)
class ResearchStartRef:
    task_id: str
    query: str
    mode: Literal["fast", "deep"]
    session_id: str | None = None


@dataclass(frozen=True)
class ResearchCandidate:
    title: str
    url: str
    cited: bool = False
    ordinal: int | None = None


@dataclass(frozen=True)
class SourceContent:
    source_id: str
    title: str
    content: str
    url: str | None = None


@dataclass(frozen=True)
class ResearchPollResult:
    task_id: str
    status: Literal["in_progress", "completed", "failed", "not_found"]
    query: str
    candidates: tuple[ResearchCandidate, ...] = ()
    summary: str = ""
    report: str = ""


class NotebookBackend(Protocol):
    backend_type: str
    capabilities: BackendCapabilities

    async def create_notebook(self, title: str) -> NotebookRef: ...

    async def get_notebook(self, notebook_id: str) -> NotebookRef: ...

    async def configure_chat(
        self,
        notebook_id: str,
        persona: str,
        response_length: ResponseLength = "default",
    ) -> ChatConfig: ...

    async def get_chat_config(self, notebook_id: str) -> ChatConfig: ...

    async def list_sources(self, notebook_id: str) -> tuple[SourceSnapshot, ...]: ...

    async def add_text_source(self, notebook_id: str, title: str, content: str) -> SourceSnapshot: ...

    async def add_url_source(self, notebook_id: str, url: str) -> SourceSnapshot: ...

    async def start_research(
        self,
        notebook_id: str,
        query: str,
        mode: Literal["fast", "deep"] = "deep",
    ) -> ResearchStartRef: ...

    async def poll_research(self, notebook_id: str, task_id: str) -> ResearchPollResult: ...

    async def import_research_sources(
        self,
        notebook_id: str,
        task_id: str,
        candidates: tuple[ResearchCandidate, ...],
    ) -> tuple[SourceSnapshot, ...]: ...

    async def wait_source_ready(self, notebook_id: str, source_id: str) -> SourceSnapshot: ...

    async def get_source_content(self, notebook_id: str, source_id: str) -> SourceContent: ...

    async def ask(self, notebook_id: str, question: str) -> str: ...

    async def delete_source(self, notebook_id: str, source_id: str) -> None: ...

    async def check_source_freshness(self, notebook_id: str, source_id: str) -> bool: ...

    async def refresh_source(self, notebook_id: str, source_id: str) -> None: ...
