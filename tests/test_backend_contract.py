import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from notebooklm import ChatGoal, ChatResponseLength
from notebooklm.types import (
    ResearchSource,
    ResearchStart,
    ResearchStatus,
    ResearchTask,
    SourceFulltext,
)

from notebooklm_skill.advisor import AdvisorService, PersonaSetupError
from notebooklm_skill.backend import ChatConfig, NotebookBackend
from notebooklm_skill.gemini_backend import GeminiNotebookBackend, PersonaVerificationError
from tests.fake_backend import FakeNotebookBackend


@dataclass
class ChatSettings:
    goal: ChatGoal
    response_length: ChatResponseLength
    custom_prompt: str


class StubNotebooksAPI:
    def __init__(self) -> None:
        self.items: dict[str, SimpleNamespace] = {}

    async def create(self, title: str) -> SimpleNamespace:
        notebook = SimpleNamespace(id=f"stub-{len(self.items) + 1}", title=title)
        self.items[notebook.id] = notebook
        return notebook

    async def get(self, notebook_id: str) -> SimpleNamespace:
        return self.items[notebook_id]


class StubChatAPI:
    def __init__(self) -> None:
        self.settings: dict[str, ChatSettings] = {}
        self.force_mismatch = False

    async def configure(
        self,
        notebook_id: str,
        *,
        goal: ChatGoal,
        response_length: ChatResponseLength,
        custom_prompt: str,
    ) -> None:
        if self.force_mismatch:
            custom_prompt = "unexpected persona"
        self.settings[notebook_id] = ChatSettings(goal, response_length, custom_prompt)

    async def get_settings(self, notebook_id: str) -> ChatSettings:
        return self.settings[notebook_id]

    async def ask(
        self,
        notebook_id: str,
        question: str,
        *,
        conversation_id: str | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            answer="Delta summary",
            conversation_id="conv-1",
            turn_number=1,
            references=[],
        )


class StubSourcesAPI:
    def __init__(self) -> None:
        self.fresh = True
        self.refresh_calls: list[tuple[str, str]] = []
        self.items = [
            SimpleNamespace(
                id="source-1",
                title="Existing source",
                url="https://example.com/existing",
            )
        ]

    async def list(self, notebook_id: str) -> list[SimpleNamespace]:
        return self.items

    async def add_text(
        self,
        notebook_id: str,
        title: str,
        content: str,
        *,
        wait: bool,
    ) -> SimpleNamespace:
        source = SimpleNamespace(id="text-source-1", title=title, url=None)
        self.items.append(source)
        return source

    async def add_url(
        self,
        notebook_id: str,
        url: str,
        *,
        wait: bool,
    ) -> SimpleNamespace:
        assert wait is False
        source = SimpleNamespace(id="url-source-1", title="URL source", url=url)
        self.items.append(source)
        return source

    async def wait_until_ready(self, notebook_id: str, source_id: str) -> SimpleNamespace:
        return next(source for source in self.items if source.id == source_id)

    async def get_fulltext(
        self, notebook_id: str, source_id: str, *, output_format: str
    ) -> SourceFulltext:
        assert output_format == "text"
        source = next(source for source in self.items if source.id == source_id)
        return SourceFulltext(source.id, source.title, "Full text", url=source.url)

    async def delete(self, notebook_id: str, source_id: str) -> None:
        self.items = [source for source in self.items if source.id != source_id]

    async def check_freshness(self, notebook_id: str, source_id: str) -> bool:
        return self.fresh

    async def refresh(self, notebook_id: str, source_id: str) -> None:
        self.refresh_calls.append((notebook_id, source_id))
        self.fresh = True


class StubResearchAPI:
    def __init__(self, sources: StubSourcesAPI) -> None:
        self.sources = sources
        self.started: list[tuple[str, str, str, str]] = []

    async def start(self, notebook_id: str, query: str, source: str, mode: str) -> ResearchStart:
        self.started.append((notebook_id, query, source, mode))
        return ResearchStart("session-1", "task-1", notebook_id, query, mode)

    async def poll(self, notebook_id: str, task_id: str) -> ResearchTask:
        url = "https://example.com/new"
        return ResearchTask(
            task_id,
            ResearchStatus.COMPLETED,
            query="query",
            sources=(ResearchSource(url=url, title="New source"),),
            summary="Summary",
            report=f"Evidence: [New source]({url})",
        )

    async def import_sources_with_verification(
        self,
        notebook_id: str,
        task_id: str,
        payload: list[dict],
        *,
        allow_duplicate: bool,
    ) -> list[dict[str, str]]:
        imported = []
        for index, item in enumerate(payload, start=1):
            source = SimpleNamespace(
                id=f"imported-{index}", title=item["title"], url=item["url"]
            )
            self.sources.items.append(source)
            imported.append({"id": source.id, "title": source.title, "url": source.url})
        return imported


class StubClient:
    def __init__(self) -> None:
        self.notebooks = StubNotebooksAPI()
        self.chat = StubChatAPI()
        self.sources = StubSourcesAPI()
        self.research = StubResearchAPI(self.sources)


class StubClientFactory:
    def __init__(self) -> None:
        self.client = StubClient()

    def __call__(self):
        @asynccontextmanager
        async def context():
            yield self.client

        return context()


async def assert_backend_contract(backend: NotebookBackend) -> None:
    notebook = await backend.create_notebook("Cross-domain advisor")
    assert notebook.title == "Cross-domain advisor"
    assert await backend.get_notebook(notebook.notebook_id) == notebook

    expected = ChatConfig(
        persona="You are an evidence-focused psychology research advisor.",
        response_length="longer",
    )
    assert await backend.configure_chat(
        notebook.notebook_id,
        expected.persona,
        expected.response_length,
    ) == expected
    assert await backend.get_chat_config(notebook.notebook_id) == expected


@pytest.mark.parametrize("backend", [FakeNotebookBackend(), GeminiNotebookBackend(client_factory=StubClientFactory())])
def test_backends_share_create_and_persona_contract(backend: NotebookBackend) -> None:
    asyncio.run(assert_backend_contract(backend))


def test_advisor_service_creates_and_configures_as_one_operation() -> None:
    async def scenario() -> None:
        service = AdvisorService(FakeNotebookBackend())
        result = await service.create("Advisor", "Cross-domain persona", "longer")

        assert result.notebook.title == "Advisor"
        assert result.chat_config == ChatConfig("Cross-domain persona", "longer")

    asyncio.run(scenario())


def test_advisor_service_adopts_without_creating_another_notebook() -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        existing = await backend.create_notebook("Existing advisor")
        service = AdvisorService(backend)

        result = await service.adopt(existing.notebook_id, "Updated persona", "shorter")

        assert result.notebook == existing
        assert len(backend.notebooks) == 1
        assert result.chat_config == ChatConfig("Updated persona", "shorter")

    asyncio.run(scenario())


def test_create_preserves_notebook_id_when_persona_setup_fails() -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        backend.fail_configuration = True
        service = AdvisorService(backend)

        with pytest.raises(PersonaSetupError, match="persona setup failed") as caught:
            await service.create("Advisor", "Any cross-domain persona")

        assert caught.value.notebook_id in backend.notebooks

    asyncio.run(scenario())


def test_gemini_backend_maps_research_without_importing() -> None:
    async def scenario() -> None:
        factory = StubClientFactory()
        backend = GeminiNotebookBackend(client_factory=factory)
        notebook = await backend.create_notebook("Advisor")

        sources = await backend.list_sources(notebook.notebook_id)
        text_source = await backend.add_text_source(
            notebook.notebook_id, "Pinned", "Pinned content"
        )
        url_source = await backend.add_url_source(
            notebook.notebook_id, "https://example.com/guide?utm_source=test"
        )
        started = await backend.start_research(notebook.notebook_id, "query", "deep")
        result = await backend.poll_research(notebook.notebook_id, started.task_id)

        assert sources[0].source_id == "source-1"
        assert text_source.source_id == "text-source-1"
        assert url_source.url == "https://example.com/guide"
        assert started.task_id == "task-1"
        assert started.session_id == "session-1"
        assert factory.client.research.started == [
            (notebook.notebook_id, "query", "web", "deep")
        ]
        assert result.status == "completed"
        assert result.candidates[0].cited is True

        imported = await backend.import_research_sources(
            notebook.notebook_id,
            started.task_id,
            result.candidates,
        )
        ready = await backend.wait_source_ready(notebook.notebook_id, imported[0].source_id)
        content = await backend.get_source_content(notebook.notebook_id, ready.source_id)
        answer = await backend.ask(notebook.notebook_id, "Summarize changes")
        factory.client.sources.fresh = False
        assert await backend.check_source_freshness(notebook.notebook_id, ready.source_id) is False
        await backend.refresh_source(notebook.notebook_id, ready.source_id)
        await backend.delete_source(notebook.notebook_id, ready.source_id)

        assert ready.url == "https://example.com/new"
        assert content.content == "Full text"
        assert answer == "Delta summary"
        assert factory.client.sources.refresh_calls == [
            (notebook.notebook_id, ready.source_id)
        ]
        assert ready.source_id not in {
            source.source_id for source in await backend.list_sources(notebook.notebook_id)
        }

    asyncio.run(scenario())


def test_gemini_backend_fails_when_persona_readback_does_not_match() -> None:
    async def scenario() -> None:
        factory = StubClientFactory()
        backend = GeminiNotebookBackend(client_factory=factory)
        notebook = await backend.create_notebook("Advisor")
        factory.client.chat.force_mismatch = True

        with pytest.raises(PersonaVerificationError, match="verification failed"):
            await backend.configure_chat(notebook.notebook_id, "Requested persona", "shorter")

    asyncio.run(scenario())
