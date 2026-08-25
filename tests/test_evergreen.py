import asyncio
from pathlib import Path

import pytest

from notebooklm_skill.apply_plan import build_apply_plan, write_apply_plan
from notebooklm_skill.backend import BackendCapabilities, SourceSnapshot
from notebooklm_skill.evergreen import (
    AdvisorPersistenceError,
    BackendCapabilityError,
    EvergreenService,
    compose_research_query,
)
from notebooklm_skill.models import PersonaProfile, RefreshRun, ResearchProfile, SourceRecord
from notebooklm_skill.preview import CandidateReview, PreviewPlan
from notebooklm_skill.refresh import RefreshPlanner, write_refresh_plan
from notebooklm_skill.storage import AdvisorStore
from tests.fake_backend import FakeNotebookBackend
from tests.sample_data import sample_run, sample_watchlist


def research_profile() -> ResearchProfile:
    return ResearchProfile(
        brief="Track meaningful changes.",
        queries=("What changed?",),
        preferred_domains=("example.com",),
    )


def test_compose_research_query_includes_profile_watchlist_and_last_refresh() -> None:
    query = compose_research_query(
        research_profile(),
        sample_watchlist(),
        (sample_run(),),
    )

    assert "Track meaningful changes" in query
    assert "What changed?" in query
    assert "The core product assumption remains supported" in query
    assert "2026-08-22T01:05:00Z" in query
    assert "supporting and opposing evidence" in query


def test_missing_backend_capability_fails_explicitly(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )
        backend.capabilities = BackendCapabilities(deep_research=False)

        with pytest.raises(BackendCapabilityError, match="Deep Research"):
            await service.preview(
                advisor_id="advisor-001",
                run_id="preview-001",
                work_directory=tmp_path / "preview",
            )

    asyncio.run(scenario())


def test_setup_creates_persona_and_persists_provider_neutral_state(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)

        result = await service.setup(
            advisor_id="advisor-001",
            title="Cross-domain advisor",
            persona=PersonaProfile("Act as an evidence-focused advisor.", "longer"),
            research=research_profile(),
            watchlist=sample_watchlist(),
        )

        profile, watchlist, sources = store.load("advisor-001")
        assert profile.backend.notebook_id == result.notebook.notebook_id
        assert profile.persona.response_length == "longer"
        assert watchlist == sample_watchlist()
        assert sources == ()

    asyncio.run(scenario())


def test_setup_preserves_notebook_id_when_local_persistence_fails(tmp_path: Path) -> None:
    class FailingStore(AdvisorStore):
        def create(self, *args, **kwargs):
            raise OSError("injected persistence failure")

    async def scenario() -> None:
        backend = FakeNotebookBackend()
        service = EvergreenService(backend, FailingStore(tmp_path / "advisors"))

        with pytest.raises(AdvisorPersistenceError, match="persistence failed") as caught:
            await service.setup(
                advisor_id="advisor-001",
                title="Advisor",
                persona=PersonaProfile("Evidence-focused advisor."),
                research=research_profile(),
            )

        assert caught.value.notebook_id in backend.notebooks

    asyncio.run(scenario())


def test_adopt_registers_existing_sources_and_allows_pinning(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Existing")
        backend.sources[notebook.notebook_id] = (
            SourceSnapshot(
                "existing-url",
                "Existing source",
                "https://example.com/existing?utm_source=test",
            ),
        )
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)

        await service.setup(
            advisor_id="advisor-001",
            title="Existing",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
            notebook_id=notebook.notebook_id,
        )
        registered = store.load("advisor-001")[2]
        assert len(registered) == 1
        assert registered[0].canonical_url == "https://example.com/existing"

        pinned = service.set_source_state(
            advisor_id="advisor-001",
            local_id=registered[0].local_id,
            state="pinned",
        )
        assert pinned.state == "pinned"
        assert store.load("advisor-001")[2][0].state == "pinned"

    asyncio.run(scenario())


def test_add_url_source_pins_registers_and_reconciles_without_duplicates(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )

        first = await service.add_url_source(
            advisor_id="advisor-001",
            url="https://example.com/guide?utm_source=test",
            state="pinned",
        )
        again = await service.add_url_source(
            advisor_id="advisor-001",
            url="https://example.com/guide",
            state="pinned",
        )

        assert first == again
        assert first.state == "pinned"
        assert first.canonical_url == "https://example.com/guide"
        assert len(store.load("advisor-001")[2]) == 1
        assert len([event for event in backend.events if event.startswith("add_url:")]) == 1

    asyncio.run(scenario())


def test_add_url_source_resumes_after_backend_commit_timeout(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )
        backend.add_url_commit_then_fail = True

        with pytest.raises(TimeoutError):
            await service.add_url_source(
                advisor_id="advisor-001",
                url="https://example.com/guide",
                state="pinned",
            )
        assert store.load("advisor-001")[2] == ()

        recovered = await service.add_url_source(
            advisor_id="advisor-001",
            url="https://example.com/guide",
            state="pinned",
        )
        assert recovered.state == "pinned"
        assert len(store.load("advisor-001")[2]) == 1
        assert len([event for event in backend.events if event.startswith("add_url:")]) == 1

    asyncio.run(scenario())


def test_add_url_source_requires_backend_capability(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )
        backend.capabilities = BackendCapabilities(url_sources=False)

        with pytest.raises(BackendCapabilityError, match="URL sources"):
            await service.add_url_source(
                advisor_id="advisor-001",
                url="https://example.com/guide",
            )

    asyncio.run(scenario())


def test_ask_routes_question_through_registered_advisor(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )

        assert await service.ask("advisor-001", "What should we test?") == "Delta summary"
        assert backend.events[-1] == "ask"
        backend.capabilities = BackendCapabilities(chat_query=False)
        with pytest.raises(BackendCapabilityError, match="chat queries"):
            await service.ask("advisor-001", "What should we test?")

    asyncio.run(scenario())


def test_safe_apply_commits_addition_tombstone_and_run_history(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        setup = await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )
        notebook_id = setup.notebook.notebook_id
        pinned = await backend.add_text_source(notebook_id, "Pinned", "Keep")
        legacy = await backend.add_text_source(notebook_id, "Legacy", "Retire")
        registry = (
            SourceRecord("src-pinned", pinned.source_id, "Pinned", "pinned", "manual"),
            SourceRecord("src-legacy", legacy.source_id, "Legacy", "active", "manual"),
        )
        store.save_sources("advisor-001", registry)
        replacement = "https://example.com/replacement"
        preview = PreviewPlan(
            run_id="preview-001",
            advisor_id="advisor-001",
            notebook_id=notebook_id,
            research_task_id="research-001",
            query="query",
            baseline_source_ids=tuple(sorted((pinned.source_id, legacy.source_id))),
            final_source_ids=tuple(sorted((pinned.source_id, legacy.source_id))),
            candidates=(
                CandidateReview(
                    "Replacement",
                    replacement,
                    replacement,
                    True,
                    True,
                    1,
                    "propose_add",
                ),
            ),
        )
        plan = build_apply_plan(
            plan_id="apply-001",
            preview=preview,
            sources=registry,
            retirement_requests={"src-legacy": (replacement, "Approved replacement")},
        )
        plan_path, _ = write_apply_plan(plan, tmp_path / "plan")

        result = await service.apply(
            advisor_id="advisor-001",
            run_id="refresh-001",
            plan_path=plan_path,
            approved_digest=plan.digest,
            evidence_directory=tmp_path / "evidence",
        )

        _, _, updated = store.load("advisor-001")
        by_local = {source.local_id: source for source in updated}
        assert by_local["src-pinned"].state == "pinned"
        assert by_local["src-legacy"].state == "deleted"
        imported = [source for source in updated if source.origin == "research"]
        assert len(imported) == 1
        assert imported[0].backend_source_id in result.imported_source_ids
        runs = store.load_refresh_runs("advisor-001")
        assert runs[0].deleted_sources == ("src-legacy",)
        assert runs[0].imported_sources == (imported[0].local_id,)

        again = await service.apply(
            advisor_id="advisor-001",
            run_id="refresh-001",
            plan_path=plan_path,
            approved_digest=plan.digest,
            evidence_directory=tmp_path / "evidence",
        )
        assert again == result
        assert len(store.load_refresh_runs("advisor-001")) == 1

    asyncio.run(scenario())


def test_backend_aware_export_includes_readable_content_and_tombstones(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        setup = await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )
        source = await backend.add_text_source(
            setup.notebook.notebook_id, "Readable", "Portable source content"
        )
        store.save_sources(
            "advisor-001",
            (
                SourceRecord(
                    "src-readable",
                    source.source_id,
                    source.title,
                    "active",
                    "manual",
                ),
                SourceRecord(
                    "src-deleted",
                    "deleted-backend-id",
                    "Deleted",
                    "deleted",
                    "manual",
                ),
            ),
        )

        result = await service.export_advisor("advisor-001", tmp_path / "export")

        assert result["exported_sources"] == 1
        assert result["tombstones"] == 1
        assert (tmp_path / "export" / "source-content" / "src-readable.txt").read_text() == (
            "Portable source content\n"
        )
        assert (tmp_path / "export" / "source-content" / "manifest.json").is_file()

    asyncio.run(scenario())


def test_native_refresh_commits_verification_timestamp_and_history(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        store = AdvisorStore(tmp_path / "advisors")
        service = EvergreenService(backend, store)
        setup = await service.setup(
            advisor_id="advisor-001",
            title="Advisor",
            persona=PersonaProfile("Evidence-focused advisor."),
            research=research_profile(),
        )
        notebook_id = setup.notebook.notebook_id
        source = SourceSnapshot(
            "url-source",
            "Live URL",
            "https://example.com/live",
            kind="web_page",
        )
        backend.sources[notebook_id] = (source,)
        backend.freshness[source.source_id] = False
        store.save_sources(
            "advisor-001",
            (
                SourceRecord(
                    "src-live",
                    source.source_id,
                    source.title,
                    "active",
                    "manual",
                    url=source.url,
                ),
            ),
        )
        plan = await RefreshPlanner(backend).build(
            plan_id="native-001",
            advisor_id="advisor-001",
            notebook_id=notebook_id,
            registry=store.load("advisor-001")[2],
        )
        plan_path, _ = write_refresh_plan(plan, tmp_path / "refresh-plan")

        await service.commit_native_refresh(
            advisor_id="advisor-001",
            run_id="refresh-native",
            plan=plan,
            plan_path=plan_path,
            approved_digest=plan.digest,
            work_directory=tmp_path / "refresh-run",
        )

        updated = store.load("advisor-001")[2][0]
        run: RefreshRun = store.load_refresh_runs("advisor-001")[0]
        assert updated.last_verified_at is not None
        assert run.proposed_refreshes == (source.source_id,)
        assert run.approved_actions == (f"refresh:{plan.digest}",)
        assert backend.events.count(f"refresh:{source.source_id}") == 1

        await service.commit_native_refresh(
            advisor_id="advisor-001",
            run_id="refresh-native",
            plan=plan,
            plan_path=plan_path,
            approved_digest=plan.digest,
            work_directory=tmp_path / "refresh-run",
        )
        assert backend.events.count(f"refresh:{source.source_id}") == 1
        assert len(store.load_refresh_runs("advisor-001")) == 1

    asyncio.run(scenario())


def test_format_answer_with_citations(tmp_path: Path) -> None:
    from notebooklm_skill.backend import AskResponse, CitationReference
    from notebooklm_skill.evergreen import format_answer_with_citations
    from notebooklm_skill.models import SourceRecord

    res = AskResponse(
        answer="According to the spec [1], authorization discovery is mandatory.",
        conversation_id="conv-123",
        turn_number=1,
        references=(
            CitationReference(
                source_id="src-backend-1",
                citation_number=1,
                source_title="MCP Spec 2025",
                cited_text="MCP clients MUST support discovery.",
                start_char=100,
                end_char=136,
            ),
        ),
    )
    sources = (
        SourceRecord(
            local_id="src-001",
            backend_source_id="src-backend-1",
            title="MCP Spec 2025",
            state="active",
            origin="manual",
            url="https://example.com/spec",
        ),
    )
    formatted = format_answer_with_citations(res, sources)
    assert "[1] MCP Spec 2025" in formatted
    assert "https://example.com/spec" in formatted
    assert "字元 100–136" in formatted
    assert "MCP clients MUST support discovery." in formatted
