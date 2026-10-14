"""Review-only discovery of canonical project documents."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from notebooklm_skill.grounding import GroundingReport, normalized_text_sha256
from notebooklm_skill.project_brain import ProjectBrainManifest
from notebooklm_skill.storage import _atomic_write, _write_json

_TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst"}
_EXCLUDED_PARTS = {
    ".git",
    ".notebooklm",
    ".venv",
    "node_modules",
    "build",
    "dist",
    "runs",
    "logs",
    "artifacts",
    "__pycache__",
}


@dataclass(frozen=True)
class OnboardingCandidate:
    project_path: str
    roles: tuple[str, ...]
    content_sha256: str
    size_bytes: int
    git_tracked: bool
    reason: str
    review_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
            "roles": list(self.roles),
            "content_sha256": self.content_sha256,
            "size_bytes": self.size_bytes,
            "git_tracked": self.git_tracked,
            "reason": self.reason,
            "review_required": self.review_required,
        }


@dataclass(frozen=True)
class OnboardingPlan:
    project_id: str
    advisor_id: str
    notebook_id: str
    grounding_status: str
    required_roles: tuple[str, ...]
    missing_roles: tuple[str, ...]
    git_commit: str | None
    candidates: tuple[OnboardingCandidate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "awaiting_review",
            "project_id": self.project_id,
            "advisor_id": self.advisor_id,
            "notebook_id": self.notebook_id,
            "grounding_status": self.grounding_status,
            "required_roles": list(self.required_roles),
            "missing_roles": list(self.missing_roles),
            "git_commit": self.git_commit,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }

    @property
    def digest(self) -> str:
        import json

        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def _git_metadata(project_root: Path) -> tuple[set[str], str | None]:
    try:
        tracked_result = subprocess.run(
            ["git", "-C", str(project_root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
        tracked = {
            item.decode(errors="surrogateescape")
            for item in tracked_result.stdout.split(b"\0")
            if item
        }
        commit_result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return tracked, commit_result.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return set(), None


def current_git_commit(project_root: Path) -> str | None:
    return _git_metadata(project_root.resolve())[1]


def _classify(path: Path) -> tuple[tuple[str, ...], str] | None:
    normalized = path.as_posix().lower()
    stem = path.stem.lower().replace("_", "-")
    roles: set[str] = set()
    reasons: list[str] = []

    if stem.startswith("readme") or any(token in stem for token in ("prd", "project-overview")):
        roles.add("project_overview")
        reasons.append("overview/readme naming")
    if any(token in normalized for token in ("architecture", "architectural", "/adr/")):
        roles.add("architecture")
        reasons.append("architecture/ADR naming")
    if any(token in stem for token in ("current-status", "project-status", "roadmap")):
        roles.add("current_status")
        reasons.append("status/roadmap naming")
    if "/adr/" in normalized or any(token in stem for token in ("decision", "decisions", "adr-")):
        roles.add("decisions")
        reasons.append("decision/ADR naming")
    if any(token in stem for token in ("runbook", "operations", "deployment", "troubleshooting")):
        roles.add("runbook")
        reasons.append("runbook/operations naming")
    if any(token in stem for token in ("handoff", "hand-off")):
        roles.add("handoff")
        roles.add("current_status")
        reasons.append("handoff naming")

    if not roles:
        return None
    return tuple(sorted(roles)), "; ".join(reasons)


def build_onboarding_plan(
    project_root: Path,
    manifest: ProjectBrainManifest,
    grounding: GroundingReport,
    *,
    max_file_bytes: int = 2_000_000,
) -> OnboardingPlan:
    """Find likely canonical docs; the responsible Agent must review content."""
    root = project_root.resolve()
    tracked, commit = _git_metadata(root)
    candidates: list[OnboardingCandidate] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if _EXCLUDED_PARTS.intersection(relative.parts):
            continue
        if path.stat().st_size > max_file_bytes:
            continue
        classification = _classify(relative)
        if classification is None:
            continue
        roles, reason = classification
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not content.strip():
            continue
        candidates.append(
            OnboardingCandidate(
                project_path=relative.as_posix(),
                roles=roles,
                content_sha256=normalized_text_sha256(content),
                size_bytes=path.stat().st_size,
                git_tracked=relative.as_posix() in tracked,
                reason=reason,
            )
        )

    return OnboardingPlan(
        project_id=manifest.project_id,
        advisor_id=manifest.advisor_id,
        notebook_id=manifest.notebook_id,
        grounding_status=grounding.status,
        required_roles=manifest.required_project_roles,
        missing_roles=grounding.missing_roles,
        git_commit=commit,
        candidates=tuple(candidates),
    )


def write_onboarding_plan(plan: OnboardingPlan, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "onboarding-plan.json"
    markdown_path = directory / "onboarding-plan.md"
    document = {**plan.to_dict(), "plan_digest": plan.digest}
    _write_json(json_path, document)

    lines = [
        f"# Project Brain Onboarding Plan: {plan.project_id}",
        "",
        "- Status: `awaiting_review`",
        f"- Grounding: `{plan.grounding_status}`",
        f"- Missing roles: {', '.join(plan.missing_roles) or 'none'}",
        f"- Git commit: `{plan.git_commit or 'unknown'}`",
        f"- Digest: `{plan.digest}`",
        "",
        "## Candidates",
        "",
    ]
    if not plan.candidates:
        lines.append("No likely canonical project documents were found by filename heuristics.")
    else:
        for candidate in plan.candidates:
            lines.append(
                f"- `{candidate.project_path}` — roles: {', '.join(candidate.roles)}; "
                f"tracked: {candidate.git_tracked}; reason: {candidate.reason}"
            )
    lines.extend(
        (
            "",
            "> This is a review-only heuristic plan. The responsible project Agent must read",
            "> each candidate and confirm that it is current, canonical, and safe to upload.",
        )
    )
    _atomic_write(markdown_path, ("\n".join(lines).rstrip() + "\n").encode())
    return json_path, markdown_path
