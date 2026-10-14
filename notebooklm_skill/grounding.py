"""Project-source coverage and freshness assessment."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from notebooklm_skill.models import SourceRecord
from notebooklm_skill.project_brain import ProjectBrainManifest

GroundingStatus = Literal[
    "research_only",
    "project_partial",
    "project_ready",
    "project_stale",
    "unknown",
]

PROJECT_SOURCE_ROLES = {
    "project_overview",
    "architecture",
    "current_status",
    "decisions",
    "runbook",
    "handoff",
}


@dataclass(frozen=True)
class GroundingReport:
    status: GroundingStatus
    can_explain_project: bool
    required_roles: tuple[str, ...]
    available_roles: tuple[str, ...]
    missing_roles: tuple[str, ...]
    stale_roles: tuple[str, ...]
    freshness_unknown_roles: tuple[str, ...]
    project_source_count: int
    research_source_count: int
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "can_explain_project": self.can_explain_project,
            "required_roles": list(self.required_roles),
            "available_roles": list(self.available_roles),
            "missing_roles": list(self.missing_roles),
            "stale_roles": list(self.stale_roles),
            "freshness_unknown_roles": list(self.freshness_unknown_roles),
            "project_source_count": self.project_source_count,
            "research_source_count": self.research_source_count,
            "warnings": list(self.warnings),
        }


def normalized_text_sha256(content: str) -> str:
    return hashlib.sha256(content.strip().encode()).hexdigest()


def _source_freshness(source: SourceRecord, project_root: Path) -> Literal["fresh", "stale", "unknown"]:
    if source.project_path is None or source.content_sha256 is None:
        return "unknown"
    path = (project_root / source.project_path).resolve()
    root = project_root.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return "stale"
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "stale"
    return "fresh" if normalized_text_sha256(content) == source.content_sha256 else "stale"


def assess_project_grounding(
    manifest: ProjectBrainManifest,
    sources: tuple[SourceRecord, ...],
    project_root: Path,
) -> GroundingReport:
    """Assess whether explicit canonical project sources cover required roles."""
    active = tuple(source for source in sources if source.state not in {"deleted", "broken"})
    project_sources = tuple(
        source for source in active if PROJECT_SOURCE_ROLES.intersection(source.roles)
    )
    research_sources = tuple(
        source
        for source in active
        if "external_research" in source.roles or source.origin == "research"
    )
    available = sorted(
        {
            role
            for source in project_sources
            for role in source.roles
            if role in PROJECT_SOURCE_ROLES
        }
    )
    required = manifest.required_project_roles
    missing = tuple(role for role in required if role not in available)

    stale_roles: list[str] = []
    unknown_roles: list[str] = []
    for role in required:
        role_sources = tuple(source for source in project_sources if role in source.roles)
        if not role_sources:
            continue
        freshness = {_source_freshness(source, project_root) for source in role_sources}
        if "fresh" in freshness:
            continue
        if "stale" in freshness:
            stale_roles.append(role)
        else:
            unknown_roles.append(role)

    warnings: list[str] = []
    if not project_sources:
        if research_sources:
            status: GroundingStatus = "research_only"
            warnings.append(
                "Notebook has external research but no explicitly classified canonical project sources."
            )
        else:
            status = "unknown"
            warnings.append("No explicitly classified canonical project sources were found.")
    elif missing:
        status = "project_partial"
        warnings.append(f"Missing required project source roles: {', '.join(missing)}")
    elif stale_roles:
        status = "project_stale"
        warnings.append(f"Stale required project source roles: {', '.join(stale_roles)}")
    elif unknown_roles:
        status = "unknown"
        warnings.append(
            "Freshness cannot be proven for required roles: " + ", ".join(unknown_roles)
        )
    else:
        status = "project_ready"

    return GroundingReport(
        status=status,
        can_explain_project=status == "project_ready",
        required_roles=required,
        available_roles=tuple(available),
        missing_roles=missing,
        stale_roles=tuple(stale_roles),
        freshness_unknown_roles=tuple(unknown_roles),
        project_source_count=len(project_sources),
        research_source_count=len(research_sources),
        warnings=tuple(warnings),
    )
