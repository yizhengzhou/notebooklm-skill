import asyncio
from dataclasses import replace
from pathlib import Path

from notebooklm_skill.doctor import diagnose_project_brain
from notebooklm_skill.installer import apply_install_plan, build_install_plan, resolve_install_target
from notebooklm_skill.project_brain import bind_project
from notebooklm_skill.storage import AdvisorStore
from tests.fake_backend import FakeNotebook, FakeNotebookBackend
from tests.sample_data import sample_profile


def test_doctor_distinguishes_installed_from_bound_and_live(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    state_root = tmp_path / "advisors"
    target = resolve_install_target(project, "pi")
    apply_install_plan(build_install_plan(target), confirm=True)
    backend = FakeNotebookBackend()
    store = AdvisorStore(state_root)

    without_binding = asyncio.run(diagnose_project_brain(target, backend, store))
    assert without_binding["status"] == "needs_attention"
    assert without_binding["installation_ok"] is True
    assert without_binding["mcp_tools_ok"] is True
    assert without_binding["binding"]["status"] == "needs_brain_init"

    profile = sample_profile(advisor_id="project-brain")
    store.create(profile)
    bind_project(project, profile)
    backend.notebooks[profile.backend.notebook_id] = FakeNotebook(
        notebook_id=profile.backend.notebook_id,
        title=profile.title,
    )
    backend.sources[profile.backend.notebook_id] = ()

    configured = asyncio.run(diagnose_project_brain(target, backend, store))
    assert configured["status"] == "ready"
    assert configured["binding"]["status"] == "configured"
    assert configured["binding"]["grounding"]["status"] == "unknown"
    assert configured["project_explanation_ready"] is False
    assert configured["configured_mcp_launch"]["ok"] is True


def test_doctor_fails_when_configured_mcp_command_cannot_start(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = resolve_install_target(project, "generic")
    broken = replace(
        target,
        mcp_entry={
            **target.mcp_entry,
            "command": "/usr/bin/false",
        },
    )
    apply_install_plan(build_install_plan(broken), confirm=True)

    result = asyncio.run(
        diagnose_project_brain(
            broken,
            FakeNotebookBackend(),
            AdvisorStore(tmp_path / "advisors"),
        )
    )

    assert result["integration_files_ok"] is True
    assert result["configured_mcp_launch"]["ok"] is False
    assert result["configured_mcp_launch"]["returncode"] != 0
    assert result["installation_ok"] is False
    assert result["status"] == "needs_attention"
