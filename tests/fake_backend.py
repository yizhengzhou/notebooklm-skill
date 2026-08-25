"""Small in-memory backend for offline orchestration tests."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

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


@dataclass
class FakeNotebook:
    notebook_id: str
    title: str
    persona: str = ""
    response_length: ResponseLength = "default"


class FakeNotebookBackend:
    """In-memory implementation of the Phase 1 backend contract."""

    backend_type = "fake-notebook"
    capabilities = BackendCapabilities()

    def __init__(self) -> None:
        self.notebooks: dict[str, FakeNotebook] = {}
        self.sources: dict[str, tuple[SourceSnapshot, ...]] = {}
        self.research_results: dict[str, list[ResearchPollResult]] = {}
        self.research_start_count = 0
        self.research_poll_count = 0
        self.events: list[str] = []
        self.source_contents: dict[str, str] = {}
        self.fail_configuration = False
        self.fail_import = False
        self.fail_wait = False
        self.fail_ask = False
        self.fail_fulltext = False
        self.freshness: dict[str, bool] = {}
        self.fail_freshness_ids: set[str] = set()
        self.fail_refresh_ids: set[str] = set()
        self.refresh_commit_then_fail_ids: set[str] = set()
        self.fail_add_url = False
        self.add_url_commit_then_fail = False

    async def create_notebook(self, title: str) -> NotebookRef:
        notebook_id = f"fake-{uuid4()}"
        self.notebooks[notebook_id] = FakeNotebook(notebook_id=notebook_id, title=title)
        self.sources[notebook_id] = ()
        return NotebookRef(notebook_id=notebook_id, title=title)

    async def get_notebook(self, notebook_id: str) -> NotebookRef:
        notebook = self.notebooks[notebook_id]
        return NotebookRef(notebook_id=notebook.notebook_id, title=notebook.title)

    async def configure_chat(
        self,
        notebook_id: str,
        persona: str,
        response_length: ResponseLength = "default",
    ) -> ChatConfig:
        if self.fail_configuration:
            raise RuntimeError("injected persona failure")
        if response_length not in {"default", "longer", "shorter"}:
            raise ValueError(f"Unsupported response length: {response_length}")
        notebook = self.notebooks[notebook_id]
        notebook.persona = persona
        notebook.response_length = response_length
        return ChatConfig(persona=persona, response_length=response_length)

    async def get_chat_config(self, notebook_id: str) -> ChatConfig:
        notebook = self.notebooks[notebook_id]
        return ChatConfig(
            persona=notebook.persona,
            response_length=notebook.response_length,
        )

    async def list_sources(self, notebook_id: str) -> tuple[SourceSnapshot, ...]:
        return self.sources[notebook_id]

    async def add_text_source(self, notebook_id: str, title: str, content: str) -> SourceSnapshot:
        source = SourceSnapshot(
            source_id=f"source-{len(self.sources[notebook_id]) + 1}",
            title=title,
        )
        self.sources[notebook_id] = (*self.sources[notebook_id], source)
        self.source_contents[source.source_id] = content
        self.events.append(f"add_text:{source.source_id}")
        return source

    async def add_url_source(self, notebook_id: str, url: str) -> SourceSnapshot:
        source = SourceSnapshot(
            source_id=f"url-source-{len(self.sources[notebook_id]) + 1}",
            title=url,
            url=url,
            kind="web",
            status="processing",
        )
        if not self.fail_add_url:
            self.sources[notebook_id] = (*self.sources[notebook_id], source)
            self.source_contents[source.source_id] = f"URL content: {url}"
            self.events.append(f"add_url:{source.source_id}")
        if self.fail_add_url or self.add_url_commit_then_fail:
            self.add_url_commit_then_fail = False
            raise TimeoutError("injected URL source failure")
        return source

    async def start_research(
        self,
        notebook_id: str,
        query: str,
        mode: str = "deep",
    ) -> ResearchStartRef:
        self.research_start_count += 1
        task_id = f"research-{self.research_start_count}"
        self.research_results.setdefault(
            task_id,
            [ResearchPollResult(task_id, "completed", query)],
        )
        return ResearchStartRef(task_id=task_id, query=query, mode=mode)

    async def poll_research(self, notebook_id: str, task_id: str) -> ResearchPollResult:
        self.research_poll_count += 1
        results = self.research_results[task_id]
        if len(results) > 1:
            return results.pop(0)
        return results[0]

    async def import_research_sources(
        self,
        notebook_id: str,
        task_id: str,
        candidates: tuple[ResearchCandidate, ...],
    ) -> tuple[SourceSnapshot, ...]:
        self.events.append("import")
        if self.fail_import:
            raise RuntimeError("injected import failure")
        imported = tuple(
            SourceSnapshot(
                source_id=f"imported-{index}",
                title=candidate.title,
                url=candidate.url,
            )
            for index, candidate in enumerate(candidates, start=1)
        )
        self.sources[notebook_id] = (*self.sources[notebook_id], *imported)
        for source in imported:
            self.source_contents[source.source_id] = f"Imported: {source.title}"
            self.freshness[source.source_id] = True
        return imported

    async def wait_source_ready(self, notebook_id: str, source_id: str) -> SourceSnapshot:
        self.events.append(f"wait:{source_id}")
        if self.fail_wait:
            raise RuntimeError("injected wait failure")
        source = next(source for source in self.sources[notebook_id] if source.source_id == source_id)
        if source.status != "ready":
            source = SourceSnapshot(
                source_id=source.source_id,
                title=source.title,
                url=source.url,
                kind=source.kind,
                status="ready",
            )
            self.sources[notebook_id] = tuple(
                source if item.source_id == source_id else item
                for item in self.sources[notebook_id]
            )
        return source

    async def get_source_content(self, notebook_id: str, source_id: str) -> SourceContent:
        self.events.append(f"backup:{source_id}")
        if self.fail_fulltext:
            raise RuntimeError("injected fulltext failure")
        source = next(source for source in self.sources[notebook_id] if source.source_id == source_id)
        return SourceContent(
            source_id=source.source_id,
            title=source.title,
            content=self.source_contents.get(source_id, ""),
            url=source.url,
        )

    async def ask(self, notebook_id: str, question: str) -> AskResponse:
        self.events.append("ask")
        if self.fail_ask:
            raise RuntimeError("injected ask failure")
        return AskResponse(
            answer="Delta summary",
            conversation_id="fake-conv-1",
            turn_number=1,
            references=(
                CitationReference(
                    source_id="source-1",
                    citation_number=1,
                    cited_text="Pinned content",
                    start_char=0,
                    end_char=14,
                ),
            ),
        )

    async def delete_source(self, notebook_id: str, source_id: str) -> None:
        self.events.append(f"delete:{source_id}")
        self.sources[notebook_id] = tuple(
            source for source in self.sources[notebook_id] if source.source_id != source_id
        )

    async def check_source_freshness(self, notebook_id: str, source_id: str) -> bool:
        self.events.append(f"freshness:{source_id}")
        if source_id in self.fail_freshness_ids:
            raise RuntimeError("injected freshness failure")
        return self.freshness.get(source_id, True)

    async def refresh_source(self, notebook_id: str, source_id: str) -> None:
        self.events.append(f"refresh:{source_id}")
        if source_id in self.fail_refresh_ids:
            raise RuntimeError("injected refresh failure")
        self.freshness[source_id] = True
        if source_id in self.refresh_commit_then_fail_ids:
            self.refresh_commit_then_fail_ids.remove(source_id)
            raise TimeoutError("injected committed refresh timeout")
