import asyncio
from pathlib import Path

import pytest

from notebooklm_skill.apply_executor import ApplyExecutor
from notebooklm_skill.apply_plan import build_apply_plan, write_apply_plan
from notebooklm_skill.models import SourceRecord
from notebooklm_skill.preview import CandidateReview, PreviewPlan
from tests.fake_backend import FakeNotebookBackend


async def setup_plan(tmp_path: Path):
    backend = FakeNotebookBackend()
    notebook = await backend.create_notebook("Safe apply")
    pinned = await backend.add_text_source(notebook.notebook_id, "Pinned", "Keep this")
    legacy = await backend.add_text_source(notebook.notebook_id, "Legacy", "Back this up")
    backend.events.clear()
    replacement_url = "https://support.google.com/notebooklm/answer/1"
    preview = PreviewPlan(
        run_id="preview-001",
        advisor_id="advisor-001",
        notebook_id=notebook.notebook_id,
        research_task_id="research-001",
        query="What changed?",
        baseline_source_ids=tuple(sorted((pinned.source_id, legacy.source_id))),
        final_source_ids=tuple(sorted((pinned.source_id, legacy.source_id))),
        candidates=(
            CandidateReview(
                title="Official replacement",
                url=replacement_url,
                canonical_url=replacement_url,
                cited=True,
                preferred_domain=True,
                ordinal=1,
                decision="propose_add",
            ),
        ),
    )
    registry = (
        SourceRecord(
            local_id="src-pinned",
            backend_source_id=pinned.source_id,
            title=pinned.title,
            state="pinned",
            origin="manual",
        ),
        SourceRecord(
            local_id="src-legacy",
            backend_source_id=legacy.source_id,
            title=legacy.title,
            state="active",
            origin="manual",
        ),
    )
    plan = build_apply_plan(
        plan_id="apply-001",
        preview=preview,
        sources=registry,
        retirement_requests={
            "src-legacy": (replacement_url, "Replaced by approved official source")
        },
    )
    plan_path, _ = write_apply_plan(plan, tmp_path / "plan")
    return backend, notebook.notebook_id, pinned, legacy, plan, plan_path


def test_apply_executor_enforces_safe_order_and_preserves_pinned(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, notebook_id, pinned, legacy, plan, plan_path = await setup_plan(tmp_path)
        evidence = tmp_path / "evidence"

        result = await ApplyExecutor(backend).execute(
            plan_path=plan_path,
            approved_digest=plan.digest,
            evidence_directory=evidence,
        )

        assert backend.events == [
            "import",
            "wait:imported-1",
            "ask",
            f"backup:{legacy.source_id}",
            f"delete:{legacy.source_id}",
        ]
        assert legacy.source_id in result.deleted_source_ids
        assert pinned.source_id in result.final_source_ids
        assert "imported-1" in result.final_source_ids
        assert (evidence / "execution-result.json").is_file()
        assert len(list((evidence / "source-backups").glob("*.json"))) == 1
        assert len(list((evidence / "source-backups").glob("*.txt"))) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("failure", ["fail_import", "fail_wait", "fail_ask", "fail_fulltext"])
def test_apply_executor_failure_before_delete_keeps_legacy(tmp_path: Path, failure: str) -> None:
    async def scenario() -> None:
        backend, notebook_id, pinned, legacy, plan, plan_path = await setup_plan(tmp_path)
        setattr(backend, failure, True)

        with pytest.raises(RuntimeError):
            await ApplyExecutor(backend).execute(
                plan_path=plan_path,
                approved_digest=plan.digest,
                evidence_directory=tmp_path / "evidence",
            )

        current = await backend.list_sources(notebook_id)
        current_ids = {source.source_id for source in current}
        assert pinned.source_id in current_ids
        assert legacy.source_id in current_ids
        assert not any(event.startswith("delete:") for event in backend.events)

    asyncio.run(scenario())


def test_apply_executor_resumes_without_importing_duplicates(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, _, _, legacy, plan, plan_path = await setup_plan(tmp_path)
        executor = ApplyExecutor(backend)
        backend.fail_ask = True
        with pytest.raises(RuntimeError):
            await executor.execute(
                plan_path=plan_path,
                approved_digest=plan.digest,
                evidence_directory=tmp_path / "evidence",
            )
        backend.fail_ask = False

        result = await executor.execute(
            plan_path=plan_path,
            approved_digest=plan.digest,
            evidence_directory=tmp_path / "evidence",
        )

        assert backend.events.count("import") == 1
        assert legacy.source_id in result.deleted_source_ids

    asyncio.run(scenario())


def test_apply_executor_resume_reuses_completed_summary(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, _, _, _, plan, plan_path = await setup_plan(tmp_path)
        executor = ApplyExecutor(backend)
        backend.fail_fulltext = True
        with pytest.raises(RuntimeError):
            await executor.execute(
                plan_path=plan_path,
                approved_digest=plan.digest,
                evidence_directory=tmp_path / "evidence",
            )
        backend.fail_fulltext = False

        await executor.execute(
            plan_path=plan_path,
            approved_digest=plan.digest,
            evidence_directory=tmp_path / "evidence",
        )

        assert backend.events.count("import") == 1
        assert backend.events.count("ask") == 1

    asyncio.run(scenario())


def test_apply_executor_rejects_wrong_approval_digest_without_mutation(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend, notebook_id, _, _, _, plan_path = await setup_plan(tmp_path)
        before = await backend.list_sources(notebook_id)

        with pytest.raises(ValueError, match="Approved digest"):
            await ApplyExecutor(backend).execute(
                plan_path=plan_path,
                approved_digest="wrong",
                evidence_directory=tmp_path / "evidence",
            )

        assert await backend.list_sources(notebook_id) == before
        assert backend.events == []

    asyncio.run(scenario())
