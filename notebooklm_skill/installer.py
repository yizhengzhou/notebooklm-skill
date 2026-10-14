"""No-clobber project-local installation for Agent Skills and MCP clients."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from notebooklm_skill.storage import _atomic_write

InstallClient = Literal["auto", "pi", "claude", "generic"]
SERVER_NAME = "project-brain"
SKILL_NAME = "project-explainer"


class InstallConflictError(RuntimeError):
    """An existing client configuration differs from the managed definition."""


@dataclass(frozen=True)
class InstallTarget:
    client: str
    project_root: Path
    mcp_config_path: Path
    skill_path: Path
    mcp_entry: dict[str, object]


@dataclass(frozen=True)
class InstallPlan:
    target: InstallTarget
    mcp_action: str
    skill_action: str
    conflicts: tuple[str, ...]

    @property
    def can_install(self) -> bool:
        return not self.conflicts

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.can_install else "blocked_conflict",
            "client": self.target.client,
            "project_root": str(self.target.project_root),
            "mcp_config_path": str(self.target.mcp_config_path),
            "skill_path": str(self.target.skill_path),
            "mcp_action": self.mcp_action,
            "skill_action": self.skill_action,
            "conflicts": list(self.conflicts),
            "requires_confirmation": True,
        }


def detect_client(
    project_root: Path,
    requested: InstallClient = "auto",
    *,
    environment: Mapping[str, str] | None = None,
) -> str:
    if requested != "auto":
        return requested
    env = environment if environment is not None else os.environ
    if env.get("PI_CODING_AGENT") or env.get("PI_SESSION_ID"):
        return "pi"
    root = project_root.resolve()
    detected = []
    if (root / ".pi").exists():
        detected.append("pi")
    if (root / ".claude").exists():
        detected.append("claude")
    if len(detected) > 1:
        raise InstallConflictError(
            "Multiple Agent clients detected; pass --client pi or --client claude"
        )
    return detected[0] if detected else "generic"


def bundled_skill_path() -> Path:
    package_copy = (
        Path(__file__).resolve().parent
        / "bundled_skills"
        / SKILL_NAME
        / "SKILL.md"
    )
    if package_copy.is_file():
        return package_copy
    repository_copy = (
        Path(__file__).resolve().parent.parent / "skills" / SKILL_NAME / "SKILL.md"
    )
    if repository_copy.is_file():
        return repository_copy
    raise FileNotFoundError("Bundled project-explainer skill is missing")


def resolve_install_target(
    project_root: Path,
    client: InstallClient = "auto",
    *,
    environment: Mapping[str, str] | None = None,
    python_executable: Path | None = None,
) -> InstallTarget:
    root = project_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Project root not found: {root}")
    resolved_client = detect_client(root, client, environment=environment)
    if resolved_client == "pi":
        mcp_path = root / ".pi" / "mcp.json"
        skill_path = root / ".agents" / "skills" / SKILL_NAME / "SKILL.md"
    elif resolved_client == "claude":
        mcp_path = root / ".mcp.json"
        skill_path = root / ".claude" / "skills" / SKILL_NAME / "SKILL.md"
    else:
        mcp_path = root / ".mcp.json"
        skill_path = root / ".agents" / "skills" / SKILL_NAME / "SKILL.md"

    executable = (python_executable or Path(sys.executable)).resolve()
    entry: dict[str, object] = {
        "command": str(executable),
        "args": ["-m", "notebooklm_skill.mcp_server"],
        "cwd": str(root),
        "description": "Project-local NotebookLM Project Brain",
    }
    if resolved_client == "pi":
        entry["exposure"] = "direct"
    return InstallTarget(
        client=resolved_client,
        project_root=root,
        mcp_config_path=mcp_path,
        skill_path=skill_path,
        mcp_entry=entry,
    )


def _read_mcp_document(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"mcpServers": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InstallConflictError(f"MCP config must be a JSON object: {path}")
    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise InstallConflictError(f"mcpServers must be an object: {path}")
    return data


def build_install_plan(target: InstallTarget) -> InstallPlan:
    conflicts: list[str] = []
    try:
        document = _read_mcp_document(target.mcp_config_path)
        servers = document.get("mcpServers", {})
        assert isinstance(servers, dict)
        current_entry = servers.get(SERVER_NAME)
        if current_entry is None:
            mcp_action = "create_config" if not target.mcp_config_path.exists() else "merge_server"
        elif current_entry == target.mcp_entry:
            mcp_action = "unchanged"
        else:
            mcp_action = "conflict"
            conflicts.append(
                f"Existing mcpServers.{SERVER_NAME} differs at {target.mcp_config_path}"
            )
    except (json.JSONDecodeError, InstallConflictError) as exc:
        mcp_action = "conflict"
        conflicts.append(str(exc))

    desired_skill = bundled_skill_path().read_bytes()
    if not target.skill_path.exists():
        skill_action = "create"
    elif target.skill_path.read_bytes() == desired_skill:
        skill_action = "unchanged"
    else:
        skill_action = "conflict"
        conflicts.append(f"Existing skill differs at {target.skill_path}")

    return InstallPlan(
        target=target,
        mcp_action=mcp_action,
        skill_action=skill_action,
        conflicts=tuple(conflicts),
    )


def _restore(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_write(path, previous)


def apply_install_plan(plan: InstallPlan, *, confirm: bool) -> dict[str, object]:
    if not confirm:
        return {**plan.to_dict(), "status": "needs_confirmation"}
    if not plan.can_install:
        raise InstallConflictError("; ".join(plan.conflicts))

    target = plan.target
    paths = (target.mcp_config_path, target.skill_path)
    previous = {path: path.read_bytes() if path.exists() else None for path in paths}
    changed: list[str] = []
    try:
        if plan.skill_action == "create":
            _atomic_write(target.skill_path, bundled_skill_path().read_bytes())
            changed.append(str(target.skill_path))
        if plan.mcp_action in {"create_config", "merge_server"}:
            document = _read_mcp_document(target.mcp_config_path)
            servers = dict(document.get("mcpServers", {}))
            servers[SERVER_NAME] = target.mcp_entry
            document["mcpServers"] = servers
            payload = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
            _atomic_write(target.mcp_config_path, payload.encode())
            changed.append(str(target.mcp_config_path))
    except Exception:
        for path in reversed(paths):
            _restore(path, previous[path])
        raise

    return {
        **plan.to_dict(),
        "status": "installed",
        "changed_files": changed,
        "rollback_on_failure": True,
        "client_reload_required": bool(changed),
        "reload_instruction": (
            "Reload or restart the Agent client, then call brain_capabilities and brain_health."
            if changed
            else "No client reload is required; managed files were already exact."
        ),
        "next_step": "Run brain-doctor, then brain-init if no manifest exists.",
    }


def uninstall_project_integration(target: InstallTarget, *, confirm: bool) -> dict[str, object]:
    if not confirm:
        return {
            "status": "needs_confirmation",
            "client": target.client,
            "mcp_config_path": str(target.mcp_config_path),
            "skill_path": str(target.skill_path),
        }

    changed: list[str] = []
    if target.skill_path.exists():
        if target.skill_path.read_bytes() != bundled_skill_path().read_bytes():
            raise InstallConflictError(
                f"Refusing to delete modified skill: {target.skill_path}"
            )
        target.skill_path.unlink()
        changed.append(str(target.skill_path))

    if target.mcp_config_path.exists():
        document = _read_mcp_document(target.mcp_config_path)
        servers = dict(document.get("mcpServers", {}))
        current = servers.get(SERVER_NAME)
        if current is not None and current != target.mcp_entry:
            raise InstallConflictError(
                f"Refusing to remove modified mcpServers.{SERVER_NAME}"
            )
        if current == target.mcp_entry:
            del servers[SERVER_NAME]
            document["mcpServers"] = servers
            payload = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
            _atomic_write(target.mcp_config_path, payload.encode())
            changed.append(str(target.mcp_config_path))

    return {
        "status": "uninstalled",
        "client": target.client,
        "changed_files": changed,
        "notebook_deleted": False,
        "advisor_state_deleted": False,
        "manifest_deleted": False,
        "client_reload_required": bool(changed),
    }
