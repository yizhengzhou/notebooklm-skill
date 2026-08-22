import asyncio
from pathlib import Path

import pytest

from notebooklm_skill.backend import SourceSnapshot
from notebooklm_skill.models import SourceRecord
from notebooklm_skill.refresh import (
    RefreshExecutor,
    RefreshPendingError,
    RefreshPlanner,
    read_refresh_plan,
    update_registry_verification,
    write_refresh_plan,
)
from tests.fake_backend import FakeNotebookBackend


async def setup_refresh_plan(tmp_path: Path):
    backend = FakeNotebookBackend()
    notebook = await backend.create_notebook("Refresh")
    sources = (
        SourceSnapshot("fresh-url", "Fresh URL", "https://example.com/fresh", kind="web_page"),
        SourceSnapshot("stale-url", "Stale URL", "https://example.com/stale", kind="web_page"),
        SourceSnapshot(
            "z-duplicate-url",
            "Duplicate URL",
            "https://example.com/stale?utm_source=test",
            kind="web_page",
        ),
        SourceSnapshot(
            "drive-source",
            "Drive source",
            kind="google_docs",
            drive_document_id="drive-1",
            drive_status="active",
        ),
        SourceSnapshot("static-source", "Static", kind="pasted_text"),
        SourceSnapshot(
            "broken-source",
            "Broken",
            "https://example.com/broken",
            kind="web_page",
            status="error",
        ),
        SourceSnapshot(
            "deleted-drive",
            "Deleted Drive",
            kind="google_docs",
            drive_document_id="drive-2",
            drive_status="deleted",
            is_drive_degraded=True,
        ),
    )
    backend.sources[notebook.notebook_id] = sources
    backend.freshness.update(
        {"fresh-url": True, "stale-url": False, "drive-source": False}
    )
    registry = tuple(
        SourceRecord(
            local_id=f"local-{index}",
            backend_source_id=source.source_id,
            title=source.title,
            state="pinned" if source.source_id == "fresh-url" else "active",
            origin="manual",
            url=source.url,
        )
        for index, source in enumerate(sources, start=1)
    ) + (
        SourceRecord(
            local_id="local-missing",
            backend_source_id="missing-source",
            title="Missing",
            state="active",
            origin="manual",
        ),
    )
    plan = await RefreshPlanner(backend).build(
        plan_id="refresh-001",
        advisor_id="advisor-001",
        notebook_id=notebook.notebook_id,
        registry=registry,
    )
    plan_path, _ = write_refresh_plan(plan, tmp_path / "plan")
    return backend, notebook.notebook_id, plan, plan_path


def test_refresh_planner_classifies_without_mutation(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, notebook_id, plan, plan_path = await setup_refresh_plan(tmp_path)
        verdicts = {item.source_id: item.verdict for item in plan.reviews}

        assert verdicts == {
            "broken-source": "broken",
            "deleted-drive": "broken",
            "drive-source": "stale",
            "z-duplicate-url": "duplicate",
            "fresh-url": "fresh",
            "stale-url": "stale",
            "static-source": "static",
            "missing-source": "missing",
        }
        assert read_refresh_plan(plan_path) == plan
        assert set(plan.proposed_refresh_ids) == {"drive-source", "stale-url"}
        assert not any(event.startswith(("refresh:", "delete:", "add_")) for event in backend.events)
        assert len(await backend.list_sources(notebook_id)) == 7

    asyncio.run(scenario())


def test_refresh_executor_uses_native_refresh_and_keeps_source_ids(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, notebook_id, plan, plan_path = await setup_refresh_plan(tmp_path)
        baseline = {source.source_id for source in await backend.list_sources(notebook_id)}
        backend.events.clear()

        result = await RefreshExecutor(backend).execute(
            plan_path=plan_path,
            approved_digest=plan.digest,
            work_directory=tmp_path / "run",
            research_summary="Research preview attached.",
        )

        assert set(result.refreshed_source_ids) == {"drive-source", "stale-url"}
        assert set(result.final_source_ids) == baseline
        assert {event for event in backend.events if event.startswith("refresh:")} == {
            "refresh:drive-source",
            "refresh:stale-url",
        }
        assert not any(event.startswith(("delete:", "add_", "import")) for event in backend.events)
        assert (tmp_path / "run" / "update-report.json").is_file()
        assert "Research preview attached." in (tmp_path / "run" / "update-report.md").read_text()

    asyncio.run(scenario())


def test_refresh_timeout_resumes_without_second_refresh(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, _, plan, plan_path = await setup_refresh_plan(tmp_path)
        backend.refresh_commit_then_fail_ids.add("stale-url")
        executor = RefreshExecutor(backend)

        with pytest.raises(TimeoutError):
            await executor.execute(
                plan_path=plan_path,
                approved_digest=plan.digest,
                work_directory=tmp_path / "run",
            )
        result = await executor.execute(
            plan_path=plan_path,
            approved_digest=plan.digest,
            work_directory=tmp_path / "run",
        )

        assert "stale-url" in result.refreshed_source_ids
        assert backend.events.count("refresh:stale-url") == 1

    asyncio.run(scenario())


def test_uncommitted_refresh_failure_is_not_blindly_retried(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, _, plan, plan_path = await setup_refresh_plan(tmp_path)
        backend.fail_refresh_ids.add("stale-url")
        executor = RefreshExecutor(backend)

        with pytest.raises(RuntimeError, match="injected refresh failure"):
            await executor.execute(
                plan_path=plan_path,
                approved_digest=plan.digest,
                work_directory=tmp_path / "run",
            )
        backend.fail_refresh_ids.clear()
        with pytest.raises(RefreshPendingError):
            await executor.execute(
                plan_path=plan_path,
                approved_digest=plan.digest,
                work_directory=tmp_path / "run",
            )

        assert backend.events.count("refresh:stale-url") == 1
        assert not any(event.startswith("delete:") for event in backend.events)

    asyncio.run(scenario())


def test_registry_verification_updates_only_proven_sources(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, _, plan, plan_path = await setup_refresh_plan(tmp_path)
        registry = (
            SourceRecord(
                local_id="verified-fresh",
                backend_source_id="fresh-url",
                title="Fresh",
                state="active",
                origin="manual",
            ),
            SourceRecord(
                local_id="verified-stale",
                backend_source_id="stale-url",
                title="Stale",
                state="active",
                origin="manual",
            ),
            SourceRecord(
                local_id="verified-missing",
                backend_source_id="missing-source",
                title="Missing",
                state="active",
                origin="manual",
            ),
        )
        planned = update_registry_verification(
            registry, plan, verified_at="2026-08-22T00:00:00Z"
        )
        assert planned[0].last_verified_at == "2026-08-22T00:00:00Z"
        assert planned[1].last_verified_at is None
        assert planned[2].last_verified_at is None

        result = await RefreshExecutor(backend).execute(
            plan_path=plan_path,
            approved_digest=plan.digest,
            work_directory=tmp_path / "run",
        )
        completed = update_registry_verification(
            registry,
            plan,
            verified_at="2026-08-22T01:00:00Z",
            result=result,
        )
        assert completed[0].last_verified_at == "2026-08-22T01:00:00Z"
        assert completed[1].last_verified_at == "2026-08-22T01:00:00Z"
        assert completed[2].last_verified_at is None

    asyncio.run(scenario())


def test_wrong_refresh_digest_has_zero_mutation(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, _, _, plan_path = await setup_refresh_plan(tmp_path)
        backend.events.clear()

        with pytest.raises(ValueError, match="Approved digest"):
            await RefreshExecutor(backend).execute(
                plan_path=plan_path,
                approved_digest="wrong",
                work_directory=tmp_path / "run",
            )

        assert backend.events == []

    asyncio.run(scenario())
