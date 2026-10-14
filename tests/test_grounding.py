from pathlib import Path

from notebooklm_skill.grounding import assess_project_grounding, normalized_text_sha256
from notebooklm_skill.models import SourceRecord
from notebooklm_skill.project_brain import ProjectBrainManifest


def _manifest() -> ProjectBrainManifest:
    return ProjectBrainManifest(
        project_id="demo",
        advisor_id="demo-brain",
        backend_type="gemini-notebook",
        notebook_id="notebook-1",
    )


def _source(
    local_id: str,
    *,
    roles: tuple[str, ...] = (),
    path: str | None = None,
    content: str | None = None,
    origin: str = "manual",
) -> SourceRecord:
    return SourceRecord(
        local_id=local_id,
        backend_source_id=f"backend-{local_id}",
        title=local_id,
        state="active",
        origin=origin,
        roles=roles,
        project_path=path,
        content_sha256=normalized_text_sha256(content) if content is not None else None,
    )


def test_research_only_never_claims_project_explanation_ready(tmp_path: Path) -> None:
    report = assess_project_grounding(
        _manifest(),
        (_source("research", origin="research", roles=("external_research",)),),
        tmp_path,
    )

    assert report.status == "research_only"
    assert report.can_explain_project is False
    assert set(report.missing_roles) == {
        "project_overview",
        "architecture",
        "current_status",
        "decisions",
    }


def test_partial_project_sources_report_missing_roles(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("overview", encoding="utf-8")
    report = assess_project_grounding(
        _manifest(),
        (
            _source(
                "overview",
                roles=("project_overview",),
                path="README.md",
                content="overview",
            ),
        ),
        tmp_path,
    )

    assert report.status == "project_partial"
    assert report.available_roles == ("project_overview",)
    assert "architecture" in report.missing_roles


def test_complete_fresh_project_sources_are_ready_then_become_stale(tmp_path: Path) -> None:
    entries = {
        "README.md": ("project_overview", "overview"),
        "docs/architecture.md": ("architecture", "architecture"),
        "docs/current-status.md": ("current_status", "status"),
        "docs/decisions.md": ("decisions", "decisions"),
    }
    sources = []
    for index, (path, (role, content)) in enumerate(entries.items()):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        sources.append(
            _source(
                f"source-{index}",
                roles=(role,),
                path=path,
                content=content,
            )
        )

    ready = assess_project_grounding(_manifest(), tuple(sources), tmp_path)
    assert ready.status == "project_ready"
    assert ready.can_explain_project is True

    (tmp_path / "docs/current-status.md").write_text("changed", encoding="utf-8")
    stale = assess_project_grounding(_manifest(), tuple(sources), tmp_path)
    assert stale.status == "project_stale"
    assert stale.can_explain_project is False
    assert stale.stale_roles == ("current_status",)


def test_complete_roles_without_local_provenance_remain_unknown(tmp_path: Path) -> None:
    roles = ("project_overview", "architecture", "current_status", "decisions")
    sources = tuple(_source(role.replace("_", "-"), roles=(role,)) for role in roles)

    report = assess_project_grounding(_manifest(), sources, tmp_path)

    assert report.status == "unknown"
    assert set(report.freshness_unknown_roles) == set(roles)
    assert report.can_explain_project is False
