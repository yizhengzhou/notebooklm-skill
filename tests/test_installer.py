import json
from pathlib import Path

import pytest

import notebooklm_skill.installer as installer
from notebooklm_skill.installer import (
    InstallConflictError,
    apply_install_plan,
    build_install_plan,
    detect_client,
    resolve_install_target,
    uninstall_project_integration,
)


def test_bundled_skill_matches_repository_skill() -> None:
    repository_skill = (
        Path(__file__).resolve().parent.parent
        / "skills/project-explainer/SKILL.md"
    )
    assert installer.bundled_skill_path().read_bytes() == repository_skill.read_bytes()


def test_auto_detects_pi_from_agent_environment(tmp_path: Path) -> None:
    assert (
        detect_client(tmp_path, environment={"PI_CODING_AGENT": "1"}) == "pi"
    )


def test_auto_detection_refuses_ambiguous_client_directories(tmp_path: Path) -> None:
    (tmp_path / ".pi").mkdir()
    (tmp_path / ".claude").mkdir()

    with pytest.raises(InstallConflictError, match="Multiple Agent clients"):
        detect_client(tmp_path, environment={})


def test_install_is_preview_first_no_clobber_and_idempotent(tmp_path: Path) -> None:
    target = resolve_install_target(
        tmp_path,
        "pi",
        python_executable=tmp_path / ".venv/bin/python",
    )
    target.mcp_config_path.parent.mkdir(parents=True)
    target.mcp_config_path.write_text(
        json.dumps({"custom": {"keep": True}, "mcpServers": {"other": {"url": "https://example.com/mcp"}}}),
        encoding="utf-8",
    )

    plan = build_install_plan(target)
    assert plan.can_install is True
    assert plan.mcp_action == "merge_server"
    assert plan.skill_action == "create"

    preview = apply_install_plan(plan, confirm=False)
    assert preview["status"] == "needs_confirmation"
    assert not target.skill_path.exists()
    assert "project-brain" not in target.mcp_config_path.read_text(encoding="utf-8")

    installed = apply_install_plan(plan, confirm=True)
    assert installed["status"] == "installed"
    document = json.loads(target.mcp_config_path.read_text(encoding="utf-8"))
    assert document["custom"] == {"keep": True}
    assert document["mcpServers"]["other"]["url"] == "https://example.com/mcp"
    assert document["mcpServers"]["project-brain"] == target.mcp_entry
    assert target.skill_path.read_bytes() == installer.bundled_skill_path().read_bytes()

    repeat = build_install_plan(target)
    assert repeat.mcp_action == "unchanged"
    assert repeat.skill_action == "unchanged"
    assert apply_install_plan(repeat, confirm=True)["changed_files"] == []


def test_install_refuses_existing_managed_name_or_modified_skill(tmp_path: Path) -> None:
    target = resolve_install_target(tmp_path, "generic")
    target.mcp_config_path.write_text(
        json.dumps({"mcpServers": {"project-brain": {"command": "other"}}}),
        encoding="utf-8",
    )
    target.skill_path.parent.mkdir(parents=True)
    target.skill_path.write_text("custom skill", encoding="utf-8")

    plan = build_install_plan(target)
    assert plan.can_install is False
    assert len(plan.conflicts) == 2
    with pytest.raises(InstallConflictError):
        apply_install_plan(plan, confirm=True)
    assert target.skill_path.read_text(encoding="utf-8") == "custom skill"


def test_install_rolls_back_all_files_if_second_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = resolve_install_target(tmp_path, "generic")
    plan = build_install_plan(target)
    real_atomic_write = installer._atomic_write
    calls = 0

    def fail_second_write(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected config write failure")
        real_atomic_write(path, content)

    monkeypatch.setattr(installer, "_atomic_write", fail_second_write)
    with pytest.raises(OSError, match="injected"):
        apply_install_plan(plan, confirm=True)

    assert not target.mcp_config_path.exists()
    assert not target.skill_path.exists()


def test_uninstall_removes_only_exact_managed_entries(tmp_path: Path) -> None:
    target = resolve_install_target(tmp_path, "claude")
    apply_install_plan(build_install_plan(target), confirm=True)
    document = json.loads(target.mcp_config_path.read_text(encoding="utf-8"))
    document["mcpServers"]["other"] = {"url": "https://example.com/mcp"}
    target.mcp_config_path.write_text(json.dumps(document), encoding="utf-8")
    manifest = tmp_path / ".notebooklm/brain.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}", encoding="utf-8")

    preview = uninstall_project_integration(target, confirm=False)
    assert preview["status"] == "needs_confirmation"
    assert target.skill_path.exists()

    result = uninstall_project_integration(target, confirm=True)
    assert result["status"] == "uninstalled"
    assert not target.skill_path.exists()
    remaining = json.loads(target.mcp_config_path.read_text(encoding="utf-8"))
    assert remaining["mcpServers"] == {"other": {"url": "https://example.com/mcp"}}
    assert manifest.exists()
