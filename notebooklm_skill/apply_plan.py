"""Review-only source addition and retirement plans for Phase 4A."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from notebooklm_skill.models import SCHEMA_VERSION, SourceRecord, _validate_id
from notebooklm_skill.preview import CandidateReview, PreviewPlan, canonicalize_url
from notebooklm_skill.storage import _atomic_write, _read_json, _write_json


@dataclass(frozen=True)
class PlannedAddition:
    title: str
    url: str
    canonical_url: str
    cited: bool
    preferred_domain: bool

    @classmethod
    def from_candidate(cls, candidate: CandidateReview) -> PlannedAddition:
        return cls(
            title=candidate.title,
            url=candidate.url,
            canonical_url=candidate.canonical_url,
            cited=candidate.cited,
            preferred_domain=candidate.preferred_domain,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "canonical_url": self.canonical_url,
            "cited": self.cited,
            "preferred_domain": self.preferred_domain,
        }


@dataclass(frozen=True)
class PlannedRetirement:
    local_id: str
    backend_source_id: str
    title: str
    reason: str
    replacement_url: str
    backup_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_id": self.local_id,
            "backend_source_id": self.backend_source_id,
            "title": self.title,
            "reason": self.reason,
            "replacement_url": self.replacement_url,
            "backup_required": self.backup_required,
        }


@dataclass(frozen=True)
class ApplyPlan:
    plan_id: str
    advisor_id: str
    notebook_id: str
    research_task_id: str
    source_snapshot_ids: tuple[str, ...]
    protected_source_ids: tuple[str, ...]
    additions: tuple[PlannedAddition, ...]
    retirements: tuple[PlannedRetirement, ...]
    status: str = "review_required"

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "plan_id": self.plan_id,
            "advisor_id": self.advisor_id,
            "notebook_id": self.notebook_id,
            "research_task_id": self.research_task_id,
            "source_snapshot_ids": list(self.source_snapshot_ids),
            "protected_source_ids": list(self.protected_source_ids),
            "additions": [item.to_dict() for item in self.additions],
            "retirements": [item.to_dict() for item in self.retirements],
            "status": self.status,
            "safety": {
                "add_before_delete": True,
                "wait_until_ready": True,
                "backup_before_delete": True,
                "explicit_approval_required": True,
            },
        }

    @property
    def digest(self) -> str:
        payload = json.dumps(
            self.unsigned_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
        return hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "plan_digest": self.digest}


def build_apply_plan(
    *,
    plan_id: str,
    preview: PreviewPlan,
    sources: tuple[SourceRecord, ...],
    retirement_requests: dict[str, tuple[str, str]],
    selected_urls: set[str] | None = None,
) -> ApplyPlan:
    _validate_id(plan_id, "plan_id")
    if selected_urls is None:
        selected_candidates = preview.proposed_additions
    else:
        normalized_selection = {canonicalize_url(url) for url in selected_urls}
        selectable = tuple(
            item
            for item in preview.candidates
            if item.decision in {"propose_add", "over_budget"}
        )
        selectable_urls = {item.canonical_url for item in selectable}
        unknown = normalized_selection - selectable_urls
        if unknown:
            raise ValueError(f"Selected URLs are not selectable Preview candidates: {sorted(unknown)}")
        if len(normalized_selection) > len(preview.proposed_additions):
            raise ValueError("Selected URLs exceed the Preview source budget")
        selected_candidates = tuple(
            item for item in selectable if item.canonical_url in normalized_selection
        )
    additions = tuple(PlannedAddition.from_candidate(item) for item in selected_candidates)
    addition_urls = {item.canonical_url for item in additions}
    sources_by_local_id = {source.local_id: source for source in sources}
    if len(sources_by_local_id) != len(sources):
        raise ValueError("Source Registry contains duplicate local IDs")

    retirements: list[PlannedRetirement] = []
    for local_id, (replacement_url, reason) in retirement_requests.items():
        source = sources_by_local_id.get(local_id)
        if source is None:
            raise ValueError(f"Unknown retirement source: {local_id}")
        if source.state == "pinned":
            raise ValueError(f"Pinned source cannot be retired: {local_id}")
        if source.backend_source_id not in preview.final_source_ids:
            raise ValueError(f"Retirement source is outside preview snapshot: {local_id}")
        canonical_replacement = canonicalize_url(replacement_url)
        if canonical_replacement not in addition_urls:
            raise ValueError(f"Retirement replacement is not a proposed addition: {replacement_url}")
        if not reason.strip():
            raise ValueError("Retirement reason is required")
        retirements.append(
            PlannedRetirement(
                local_id=source.local_id,
                backend_source_id=source.backend_source_id,
                title=source.title,
                reason=reason.strip(),
                replacement_url=canonical_replacement,
            )
        )

    return ApplyPlan(
        plan_id=plan_id,
        advisor_id=preview.advisor_id,
        notebook_id=preview.notebook_id,
        research_task_id=preview.research_task_id,
        source_snapshot_ids=preview.final_source_ids,
        protected_source_ids=tuple(
            sorted(source.backend_source_id for source in sources if source.state == "pinned")
        ),
        additions=additions,
        retirements=tuple(retirements),
    )


def write_apply_plan(plan: ApplyPlan, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "apply-plan.json"
    markdown_path = directory / "apply-plan.md"
    _write_json(json_path, plan.to_dict())
    _atomic_write(markdown_path, _render_markdown(plan).encode())
    return json_path, markdown_path


def verify_apply_plan(path: Path) -> dict[str, Any]:
    document = _read_json(path)
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported Apply Plan schema")
    claimed_digest = document.pop("plan_digest", None)
    payload = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    actual_digest = hashlib.sha256(payload).hexdigest()
    if claimed_digest != actual_digest:
        raise ValueError("Apply Plan digest mismatch")
    if document.get("status") != "review_required":
        raise ValueError("Apply Plan is not awaiting review")
    return {**document, "plan_digest": claimed_digest}


def _render_markdown(plan: ApplyPlan) -> str:
    lines = [
        f"# Apply Plan: {plan.plan_id}",
        "",
        f"- Digest: `{plan.digest}`",
        f"- Status: **{plan.status}**",
        f"- Protected sources: **{len(plan.protected_source_ids)}**",
        f"- Proposed additions: **{len(plan.additions)}**",
        f"- Proposed retirements: **{len(plan.retirements)}**",
        "",
        "## Additions",
        "",
    ]
    lines.extend(f"- [{item.title}]({item.url})" for item in plan.additions)
    lines.extend(("", "## Retirements", ""))
    if not plan.retirements:
        lines.append("No retirements proposed.")
    for item in plan.retirements:
        lines.append(
            f"- `{item.local_id}` {item.title} — {item.reason}; replacement: {item.replacement_url}"
        )
    lines.extend(
        (
            "",
            "## Required execution order",
            "",
            "1. Import approved additions.",
            "2. Wait until every replacement source is ready.",
            "3. Generate the delta summary.",
            "4. Back up retirement source metadata and full text.",
            "5. Revalidate the protected set and plan digest.",
            "6. Delete only explicitly approved retirement sources.",
        )
    )
    return "\n".join(lines) + "\n"
