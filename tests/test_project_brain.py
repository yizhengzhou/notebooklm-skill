import json
from pathlib import Path

import pytest

from notebooklm_skill.project_brain import (
    ProjectBrainBindingError,
    ProjectBrainNotConfiguredError,
    bind_project,
    discover_project_brain,
    read_manifest,
)
from tests.sample_data import sample_profile


def test_bind_and_discover_project_brain_from_nested_directory(tmp_path: Path) -> None:
    project = tmp_path / "my-project"
    nested = project / "src" / "feature"
    nested.mkdir(parents=True)
    profile = sample_profile(advisor_id="my-project-brain")

    path = bind_project(project, profile)
    root, discovered_path, manifest = discover_project_brain(nested)

    assert path == project / ".notebooklm" / "brain.json"
    assert root == project
    assert discovered_path == path
    assert manifest.advisor_id == profile.advisor_id
    assert manifest.notebook_id == profile.backend.notebook_id
    assert manifest.required_project_roles == (
        "project_overview",
        "architecture",
        "current_status",
        "decisions",
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["roles"] == {
        "advisor": True,
        "librarian": True,
        "studio_producer": True,
    }
    assert "cookie" not in path.read_text(encoding="utf-8").lower()
    assert "token" not in path.read_text(encoding="utf-8").lower()


def test_binding_is_idempotent_but_refuses_different_advisor(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    first = sample_profile(advisor_id="first-brain")
    second = sample_profile(advisor_id="second-brain")

    path = bind_project(project, first)
    assert bind_project(project, first) == path

    with pytest.raises(ProjectBrainBindingError, match="refusing to overwrite"):
        bind_project(project, second)
    assert read_manifest(path).advisor_id == "first-brain"


def test_discovery_never_guesses_without_manifest(tmp_path: Path) -> None:
    with pytest.raises(ProjectBrainNotConfiguredError, match="PROJECT_BRAIN_NOT_CONFIGURED"):
        discover_project_brain(tmp_path)


def test_manifest_rejects_unsupported_schema(tmp_path: Path) -> None:
    path = tmp_path / "brain.json"
    path.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported"):
        read_manifest(path)
