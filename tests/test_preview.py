import asyncio
import json
from pathlib import Path

import pytest

from notebooklm_skill.backend import ResearchCandidate, ResearchPollResult, SourceSnapshot
from notebooklm_skill.preview import (
    PreviewEngine,
    PreviewTimeoutError,
    SourceMutationDetectedError,
    canonicalize_url,
    read_preview_plan,
)
from tests.fake_backend import FakeNotebookBackend


async def no_sleep(_: float) -> None:
    return None


def test_url_canonicalization_removes_tracking_and_normalizes() -> None:
    assert canonicalize_url(
        "HTTPS://Example.COM:443/research/?utm_source=newsletter&b=2&a=1#section"
    ) == "https://example.com/research?a=1&b=2"


def test_preview_deduplicates_candidates_and_does_not_mutate_sources(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Preview")
        backend.sources[notebook.notebook_id] = (
            SourceSnapshot("source-1", "Existing", "https://example.com/existing"),
        )
        backend.research_results["research-1"] = [
            ResearchPollResult("research-1", "in_progress", "query"),
            ResearchPollResult(
                "research-1",
                "completed",
                "query",
                candidates=(
                    ResearchCandidate(
                        "Cited new source", "https://google.com/new?utm_source=x", True, 2
                    ),
                    ResearchCandidate("Duplicate", "https://google.com/new", False, 3),
                    ResearchCandidate("Existing", "https://example.com/existing/", True, 1),
                    ResearchCandidate("Over budget", "https://example.org/other", False, 4),
                ),
                summary="One meaningful change.",
            ),
        ]
        engine = PreviewEngine(backend, sleep=no_sleep)

        plan = await engine.run(
            run_id="preview-001",
            advisor_id="advisor-001",
            notebook_id=notebook.notebook_id,
            query="query",
            work_directory=tmp_path / "preview",
            max_new_sources=1,
            poll_interval=0,
        )

        assert backend.research_start_count == 1
        assert plan.baseline_source_ids == plan.final_source_ids == ("source-1",)
        assert [item.decision for item in plan.candidates] == [
            "already_present",
            "propose_add",
            "duplicate",
            "over_budget",
        ]
        assert json.loads((tmp_path / "preview" / "preview.json").read_text())[
            "sources_unchanged"
        ]
        assert (tmp_path / "preview" / "preview.md").is_file()

    asyncio.run(scenario())


def test_preview_plan_round_trips_from_json(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Preview")
        backend.research_results["research-1"] = [
            ResearchPollResult("research-1", "completed", "query")
        ]
        directory = tmp_path / "preview"
        plan = await PreviewEngine(backend).run(
            run_id="preview-roundtrip",
            advisor_id="advisor-001",
            notebook_id=notebook.notebook_id,
            query="query",
            work_directory=directory,
        )

        assert read_preview_plan(directory / "preview.json") == plan

    asyncio.run(scenario())


def test_preferred_domains_rank_ahead_of_research_ordinal(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Preview")
        backend.research_results["research-1"] = [
            ResearchPollResult(
                "research-1",
                "completed",
                "query",
                candidates=(
                    ResearchCandidate("Third party", "https://example.com/first", True, 1),
                    ResearchCandidate("Official", "https://support.google.com/answer/1", True, 2),
                ),
            )
        ]
        plan = await PreviewEngine(backend).run(
            run_id="preview-001",
            advisor_id="advisor-001",
            notebook_id=notebook.notebook_id,
            query="query",
            work_directory=tmp_path / "preview",
            max_new_sources=1,
            preferred_domains=("google.com",),
        )

        assert plan.proposed_additions[0].title == "Official"
        assert plan.proposed_additions[0].preferred_domain is True

    asyncio.run(scenario())


def test_timeout_resume_reuses_task_instead_of_starting_again(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Preview")
        backend.research_results["research-1"] = [
            ResearchPollResult("research-1", "in_progress", "query"),
            ResearchPollResult("research-1", "completed", "query"),
        ]
        engine = PreviewEngine(backend, sleep=no_sleep)
        kwargs = {
            "run_id": "preview-001",
            "advisor_id": "advisor-001",
            "notebook_id": notebook.notebook_id,
            "query": "query",
            "work_directory": tmp_path / "preview",
        }

        with pytest.raises(PreviewTimeoutError) as caught:
            await engine.run(**kwargs, timeout=0)
        assert caught.value.task_id == "research-1"
        assert backend.research_start_count == 1

        plan = await engine.run(**kwargs, timeout=10, poll_interval=0)
        assert plan.research_task_id == "research-1"
        assert backend.research_start_count == 1

    asyncio.run(scenario())


def test_preview_fails_if_source_ids_change(tmp_path: Path) -> None:
    class MutatingBackend(FakeNotebookBackend):
        async def poll_research(self, notebook_id: str, task_id: str) -> ResearchPollResult:
            result = await super().poll_research(notebook_id, task_id)
            self.sources[notebook_id] = (SourceSnapshot("unexpected", "Unexpected"),)
            return result

    async def scenario() -> None:
        backend = MutatingBackend()
        notebook = await backend.create_notebook("Preview")
        engine = PreviewEngine(backend)

        with pytest.raises(SourceMutationDetectedError):
            await engine.run(
                run_id="preview-001",
                advisor_id="advisor-001",
                notebook_id=notebook.notebook_id,
                query="query",
                work_directory=tmp_path / "preview",
            )

    asyncio.run(scenario())
