"""Project-local binding between a repository and one NotebookLM Advisor."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from notebooklm_skill.models import AdvisorProfile
from notebooklm_skill.storage import _atomic_write

PROJECT_BRAIN_SCHEMA_VERSION = 1
MANIFEST_RELATIVE_PATH = Path(".notebooklm") / "brain.json"


class ProjectBrainNotConfiguredError(FileNotFoundError):
    """No project-local Project Brain manifest was found."""


class ProjectBrainBindingError(RuntimeError):
    """The project manifest conflicts with the requested Advisor binding."""


@dataclass(frozen=True)
class ProjectBrainManifest:
    project_id: str
    advisor_id: str
    backend_type: str
    notebook_id: str
    scope: Literal["project"] = "project"
    advisor_enabled: bool = True
    librarian_enabled: bool = True
    studio_producer_enabled: bool = True
    required_project_roles: tuple[str, ...] = (
        "project_overview",
        "architecture",
        "current_status",
        "decisions",
    )

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id is required")
        if not self.advisor_id.strip():
            raise ValueError("advisor_id is required")
        if not self.backend_type.strip() or not self.notebook_id.strip():
            raise ValueError("backend type and full notebook ID are required")
        if self.scope != "project":
            raise ValueError("Project Brain manifest scope must be 'project'")
        if not self.required_project_roles or any(
            not role.strip() for role in self.required_project_roles
        ):
            raise ValueError("required_project_roles must not be empty")

    @classmethod
    def from_profile(cls, project_root: Path, profile: AdvisorProfile) -> ProjectBrainManifest:
        return cls(
            project_id=project_root.name,
            advisor_id=profile.advisor_id,
            backend_type=profile.backend.type,
            notebook_id=profile.backend.notebook_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": PROJECT_BRAIN_SCHEMA_VERSION,
            "project_id": self.project_id,
            "scope": self.scope,
            "advisor_id": self.advisor_id,
            "backend": {
                "type": self.backend_type,
                "notebook_id": self.notebook_id,
            },
            "roles": {
                "advisor": self.advisor_enabled,
                "librarian": self.librarian_enabled,
                "studio_producer": self.studio_producer_enabled,
            },
            "source_policy": {
                "required_project_roles": list(self.required_project_roles),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectBrainManifest:
        if data.get("schema_version") != PROJECT_BRAIN_SCHEMA_VERSION:
            raise ValueError("Unsupported Project Brain manifest schema")
        backend = data.get("backend")
        roles = data.get("roles", {})
        source_policy = data.get("source_policy", {})
        if not isinstance(backend, dict):
            raise ValueError("Project Brain manifest backend must be an object")
        if not isinstance(roles, dict) or not isinstance(source_policy, dict):
            raise ValueError("Project Brain manifest roles/source_policy must be objects")
        required = source_policy.get(
            "required_project_roles",
            ("project_overview", "architecture", "current_status", "decisions"),
        )
        if not isinstance(required, (list, tuple)):
            raise ValueError("required_project_roles must be an array")
        return cls(
            project_id=str(data["project_id"]),
            advisor_id=str(data["advisor_id"]),
            backend_type=str(backend["type"]),
            notebook_id=str(backend["notebook_id"]),
            scope=data.get("scope", "project"),
            advisor_enabled=bool(roles.get("advisor", True)),
            librarian_enabled=bool(roles.get("librarian", True)),
            studio_producer_enabled=bool(roles.get("studio_producer", True)),
            required_project_roles=tuple(str(role) for role in required),
        )


def manifest_path(project_root: Path) -> Path:
    return project_root.resolve() / MANIFEST_RELATIVE_PATH


def bind_project(project_root: Path, profile: AdvisorProfile) -> Path:
    """Create one no-clobber project-local manifest for an existing Advisor."""
    root = project_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Project root not found: {root}")
    path = manifest_path(root)
    proposed = ProjectBrainManifest.from_profile(root, profile)
    if path.exists():
        current = read_manifest(path)
        if current == proposed:
            return path
        raise ProjectBrainBindingError(
            f"Project Brain already bound to advisor={current.advisor_id!r}, "
            f"notebook={current.notebook_id!r}; refusing to overwrite"
        )
    payload = json.dumps(proposed.to_dict(), ensure_ascii=False, indent=2) + "\n"
    _atomic_write(path, payload.encode())
    return path


def read_manifest(path: Path) -> ProjectBrainManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Project Brain manifest must be a JSON object")
    return ProjectBrainManifest.from_dict(data)


def discover_project_brain(start: Path) -> tuple[Path, Path, ProjectBrainManifest]:
    """Find the nearest manifest from ``start`` upward without guessing a notebook."""
    resolved = start.resolve()
    if resolved.is_file():
        resolved = resolved.parent
    if not resolved.exists():
        raise FileNotFoundError(f"Discovery start path not found: {resolved}")
    for directory in (resolved, *resolved.parents):
        candidate = directory / MANIFEST_RELATIVE_PATH
        if candidate.is_file():
            return directory, candidate, read_manifest(candidate)
    raise ProjectBrainNotConfiguredError(
        f"PROJECT_BRAIN_NOT_CONFIGURED: no {MANIFEST_RELATIVE_PATH} found from {resolved}"
    )
