import asyncio
from pathlib import Path

import pytest

from notebooklm_skill.grounding import normalized_text_sha256
from notebooklm_skill.mcp_server import create_project_brain_server
from notebooklm_skill.models import SourceRecord
from notebooklm_skill.project_brain import bind_project
from notebooklm_skill.storage import AdvisorStore
from tests.fake_backend import FakeNotebook, FakeNotebookBackend
from tests.sample_data import sample_profile


def _setup_project(tmp_path: Path, *, ready: bool) -> tuple[Path, Path, FakeNotebookBackend]:
    state_root = tmp_path / "advisors"
    project = tmp_path / "project"
    project.mkdir()
    profile = sample_profile(advisor_id="project-brain")
    sources = []
    if ready:
        documents = {
            "README.md": ("project_overview", "overview"),
            "docs/architecture.md": ("architecture", "architecture"),
            "docs/current-status.md": ("current_status", "status"),
            "docs/decisions.md": ("decisions", "decisions"),
        }
        for index, (relative, (role, content)) in enumerate(documents.items()):
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            sources.append(
                SourceRecord(
                    local_id=f"source-{index}",
                    backend_source_id=f"backend-{index}",
                    title=path.name,
                    state="pinned",
                    origin="manual",
                    roles=(role,),
                    project_path=relative,
                    content_sha256=normalized_text_sha256(content),
                )
            )
    store = AdvisorStore(state_root)
    store.create(profile, sources=tuple(sources))
    bind_project(project, profile)
    backend = FakeNotebookBackend()
    backend.notebooks[profile.backend.notebook_id] = FakeNotebook(
        notebook_id=profile.backend.notebook_id,
        title=profile.title,
    )
    backend.sources[profile.backend.notebook_id] = ()
    return state_root, project, backend


def test_mcp_exposes_read_only_project_brain_tools(tmp_path: Path) -> None:
    state_root, project, backend = _setup_project(tmp_path, ready=False)
    mcp = create_project_brain_server(backend=backend, state_root=state_root)

    async def scenario() -> None:
        tools = {tool.name for tool in await mcp.list_tools()}
        assert tools == {
            "brain_discover",
            "brain_capabilities",
            "brain_grounding_check",
            "brain_onboarding_plan",
            "brain_health",
            "brain_ask",
            "brain_recover",
        }

        discovered = await mcp.call_tool(
            "brain_discover", {"project_path": str(project)}
        )
        assert discovered.structured_content["configured"] is True
        assert (
            discovered.structured_content["manifest"]["advisor_id"]
            == "project-brain"
        )

        health = await mcp.call_tool("brain_health", {"project_path": str(project)})
        assert health.structured_content["grounding"]["status"] == "unknown"
        assert health.structured_content["source_capacity"]["limit"] == 50

        plan = await mcp.call_tool(
            "brain_onboarding_plan", {"project_path": str(project)}
        )
        assert plan.structured_content["status"] == "awaiting_review"
        assert plan.structured_content["candidates"] == []

    asyncio.run(scenario())


def test_mcp_project_explanation_and_recovery_fail_closed_until_ready(
    tmp_path: Path,
) -> None:
    state_root, project, backend = _setup_project(tmp_path, ready=False)
    mcp = create_project_brain_server(backend=backend, state_root=state_root)

    async def scenario() -> None:
        with pytest.raises(Exception, match="PROJECT_GROUNDING_INSUFFICIENT"):
            await mcp.call_tool(
                "brain_ask",
                {
                    "project_path": str(project),
                    "question": "Explain this project",
                    "purpose": "project_explanation",
                },
            )
        with pytest.raises(Exception, match="PROJECT_GROUNDING_INSUFFICIENT"):
            await mcp.call_tool("brain_recover", {"project_path": str(project)})
        assert "ask" not in backend.events

    asyncio.run(scenario())


def test_mcp_ready_project_can_ask_and_recover(tmp_path: Path) -> None:
    state_root, project, backend = _setup_project(tmp_path, ready=True)
    mcp = create_project_brain_server(backend=backend, state_root=state_root)

    async def scenario() -> None:
        grounding = await mcp.call_tool(
            "brain_grounding_check", {"project_path": str(project)}
        )
        assert grounding.structured_content["grounding"]["status"] == "project_ready"

        answer = await mcp.call_tool(
            "brain_ask",
            {
                "project_path": str(project),
                "question": "Explain this project",
                "purpose": "project_explanation",
            },
        )
        assert answer.structured_content["answer"] == "Delta summary"
        assert answer.structured_content["advisory_only"] is True

        recovery = await mcp.call_tool(
            "brain_recover", {"project_path": str(project)}
        )
        assert recovery.structured_content["grounding"]["can_explain_project"] is True
        assert backend.events.count("ask") == 2

    asyncio.run(scenario())
