import json
import subprocess
from pathlib import Path

from notebooklm_skill.grounding import assess_project_grounding
from notebooklm_skill.onboarding import build_onboarding_plan, write_onboarding_plan
from notebooklm_skill.project_brain import ProjectBrainManifest


def _manifest() -> ProjectBrainManifest:
    return ProjectBrainManifest(
        project_id="demo",
        advisor_id="demo-brain",
        backend_type="gemini-notebook",
        notebook_id="notebook-1",
    )


def test_onboarding_plan_finds_likely_docs_but_requires_agent_review(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Project overview", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ARCHITECTURE.md").write_text("System structure", encoding="utf-8")
    (docs / "current-status.md").write_text("Current work", encoding="utf-8")
    adr = docs / "adr"
    adr.mkdir()
    (adr / "0001-storage.md").write_text("Decision", encoding="utf-8")
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "README.md").write_text("Dependency", encoding="utf-8")
    (tmp_path / "notes.md").write_text("Not canonical by name", encoding="utf-8")

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "README.md", "docs"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "initial",
        ],
        check=True,
    )

    manifest = _manifest()
    grounding = assess_project_grounding(manifest, (), tmp_path)
    plan = build_onboarding_plan(tmp_path, manifest, grounding)

    paths = {candidate.project_path for candidate in plan.candidates}
    assert paths == {
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/adr/0001-storage.md",
        "docs/current-status.md",
    }
    assert all(candidate.review_required for candidate in plan.candidates)
    assert all(candidate.git_tracked for candidate in plan.candidates)
    assert plan.git_commit is not None
    assert len(plan.digest) == 64

    json_path, markdown_path = write_onboarding_plan(plan, tmp_path / ".notebooklm/plans")
    document = json.loads(json_path.read_text(encoding="utf-8"))
    assert document["status"] == "awaiting_review"
    assert document["plan_digest"] == plan.digest
    assert "responsible project Agent" in markdown_path.read_text(encoding="utf-8")


def test_onboarding_plan_does_not_guess_from_arbitrary_text_files(tmp_path: Path) -> None:
    (tmp_path / "random.md").write_text("Architecture maybe", encoding="utf-8")
    manifest = _manifest()
    grounding = assess_project_grounding(manifest, (), tmp_path)

    plan = build_onboarding_plan(tmp_path, manifest, grounding)

    assert plan.candidates == ()
    assert plan.missing_roles == manifest.required_project_roles
