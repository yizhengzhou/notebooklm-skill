"""Versioned, provider-neutral Evergreen Advisor data models."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from notebooklm_skill.backend import ResponseLength

SCHEMA_VERSION = 1
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _validate_id(value: str, label: str) -> None:
    if not _ID_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")


def _require_schema(data: dict[str, Any]) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version: {data.get('schema_version')!r}")


@dataclass(frozen=True)
class BackendRef:
    type: str
    notebook_id: str

    def __post_init__(self) -> None:
        if not self.type.strip() or not self.notebook_id.strip():
            raise ValueError("Backend type and notebook_id are required")

    def to_dict(self) -> dict[str, str]:
        return {"type": self.type, "notebook_id": self.notebook_id}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BackendRef:
        return cls(type=str(data["type"]), notebook_id=str(data["notebook_id"]))


@dataclass(frozen=True)
class PersonaProfile:
    instructions: str
    response_length: ResponseLength = "default"

    def __post_init__(self) -> None:
        if not self.instructions.strip():
            raise ValueError("Persona instructions are required")
        if len(self.instructions) > 10_000:
            raise ValueError("Persona cannot exceed 10000 characters")
        if self.response_length not in {"default", "longer", "shorter"}:
            raise ValueError(f"Unsupported response length: {self.response_length}")


@dataclass(frozen=True)
class ResearchProfile:
    brief: str
    queries: tuple[str, ...]
    mode: Literal["fast", "deep"] = "deep"
    language: str = "zh-Hant"
    recency_days: int = 90
    max_new_sources_per_run: int = 10
    preferred_domains: tuple[str, ...] = ()
    update_mode: Literal["review"] = "review"
    deletion_mode: Literal["confirm"] = "confirm"
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.brief.strip() or not self.queries or any(not item.strip() for item in self.queries):
            raise ValueError("Research brief and non-empty queries are required")
        if self.mode not in {"fast", "deep"}:
            raise ValueError(f"Unsupported research mode: {self.mode}")
        if self.update_mode != "review" or self.deletion_mode != "confirm":
            raise ValueError("Phase 2 requires reviewed updates and confirmed deletion")
        if self.recency_days < 1 or self.max_new_sources_per_run < 1:
            raise ValueError("Research limits must be positive")
        if any(
            not domain.strip() or "://" in domain or "/" in domain
            for domain in self.preferred_domains
        ):
            raise ValueError("Preferred domains must be bare hostnames")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "enabled": self.enabled,
            "brief": self.brief,
            "queries": list(self.queries),
            "mode": self.mode,
            "language": self.language,
            "recency_days": self.recency_days,
            "max_new_sources_per_run": self.max_new_sources_per_run,
            "preferred_domains": list(self.preferred_domains),
            "update_mode": self.update_mode,
            "deletion_mode": self.deletion_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchProfile:
        _require_schema(data)
        return cls(
            enabled=bool(data["enabled"]),
            brief=str(data["brief"]),
            queries=tuple(str(item) for item in data["queries"]),
            mode=data["mode"],
            language=str(data["language"]),
            recency_days=int(data["recency_days"]),
            max_new_sources_per_run=int(data["max_new_sources_per_run"]),
            preferred_domains=tuple(str(item) for item in data.get("preferred_domains", [])),
            update_mode=data["update_mode"],
            deletion_mode=data["deletion_mode"],
        )


@dataclass(frozen=True)
class ScheduleProfile:
    mode: Literal["manual"] = "manual"
    suggested_interval_days: int = 30

    def __post_init__(self) -> None:
        if self.mode != "manual" or self.suggested_interval_days < 1:
            raise ValueError("Phase 2 supports only a positive manual schedule")

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode, "suggested_interval_days": self.suggested_interval_days}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScheduleProfile:
        return cls(mode=data["mode"], suggested_interval_days=int(data["suggested_interval_days"]))


@dataclass(frozen=True)
class AdvisorProfile:
    advisor_id: str
    title: str
    backend: BackendRef
    persona: PersonaProfile
    research: ResearchProfile
    schedule: ScheduleProfile = field(default_factory=ScheduleProfile)

    def __post_init__(self) -> None:
        _validate_id(self.advisor_id, "advisor_id")
        if not self.title.strip():
            raise ValueError("Advisor title is required")


@dataclass(frozen=True)
class WatchItem:
    watch_id: str
    kind: Literal["assumption", "decision", "trend", "risk", "question"]
    statement: str
    questions: tuple[str, ...] = ()
    evidence_for: tuple[str, ...] = ()
    evidence_against: tuple[str, ...] = ()
    revisit_when: tuple[str, ...] = ()
    status: Literal["active", "resolved", "paused"] = "active"

    def __post_init__(self) -> None:
        _validate_id(self.watch_id, "watch_id")
        if self.kind not in {"assumption", "decision", "trend", "risk", "question"}:
            raise ValueError(f"Unsupported watch kind: {self.kind}")
        if not self.statement.strip():
            raise ValueError("Watch statement is required")
        if self.status not in {"active", "resolved", "paused"}:
            raise ValueError(f"Unsupported watch status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "watch_id": self.watch_id,
            "kind": self.kind,
            "statement": self.statement,
            "questions": list(self.questions),
            "evidence_for": list(self.evidence_for),
            "evidence_against": list(self.evidence_against),
            "revisit_when": list(self.revisit_when),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatchItem:
        return cls(
            watch_id=str(data["watch_id"]),
            kind=data["kind"],
            statement=str(data["statement"]),
            questions=tuple(str(item) for item in data.get("questions", [])),
            evidence_for=tuple(str(item) for item in data.get("evidence_for", [])),
            evidence_against=tuple(str(item) for item in data.get("evidence_against", [])),
            revisit_when=tuple(str(item) for item in data.get("revisit_when", [])),
            status=data.get("status", "active"),
        )


@dataclass(frozen=True)
class SourceRecord:
    local_id: str
    backend_source_id: str
    title: str
    state: Literal["pinned", "active", "candidate", "superseded", "broken", "deleted"]
    origin: Literal["manual", "research", "import"]
    url: str | None = None
    canonical_url: str | None = None
    discovered_at: str | None = None
    last_verified_at: str | None = None
    last_modified_at: str | None = None
    research_run_id: str | None = None

    def __post_init__(self) -> None:
        _validate_id(self.local_id, "local source ID")
        if not self.backend_source_id.strip() or not self.title.strip():
            raise ValueError("Source backend ID and title are required")
        if self.state not in {"pinned", "active", "candidate", "superseded", "broken", "deleted"}:
            raise ValueError(f"Unsupported source state: {self.state}")
        if self.origin not in {"manual", "research", "import"}:
            raise ValueError(f"Unsupported source origin: {self.origin}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_id": self.local_id,
            "backend_source_id": self.backend_source_id,
            "title": self.title,
            "url": self.url,
            "canonical_url": self.canonical_url,
            "origin": self.origin,
            "state": self.state,
            "discovered_at": self.discovered_at,
            "last_verified_at": self.last_verified_at,
            "last_modified_at": self.last_modified_at,
            "research_run_id": self.research_run_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceRecord:
        return cls(**data)


@dataclass(frozen=True)
class RefreshRun:
    run_id: str
    advisor_id: str
    status: Literal["pending", "completed", "failed"]
    started_at: str
    completed_at: str | None = None
    baseline_source_ids: tuple[str, ...] = ()
    research_queries: tuple[str, ...] = ()
    watch_items_evaluated: tuple[str, ...] = ()
    proposed_additions: tuple[str, ...] = ()
    proposed_refreshes: tuple[str, ...] = ()
    proposed_superseded: tuple[str, ...] = ()
    proposed_deletions: tuple[str, ...] = ()
    approved_actions: tuple[str, ...] = ()
    imported_sources: tuple[str, ...] = ()
    deleted_sources: tuple[str, ...] = ()
    summary: str = ""

    def __post_init__(self) -> None:
        _validate_id(self.run_id, "run_id")
        _validate_id(self.advisor_id, "advisor_id")
        if self.status not in {"pending", "completed", "failed"}:
            raise ValueError(f"Unsupported refresh status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "advisor_id": self.advisor_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "summary": self.summary,
        }
        for name in (
            "baseline_source_ids",
            "research_queries",
            "watch_items_evaluated",
            "proposed_additions",
            "proposed_refreshes",
            "proposed_superseded",
            "proposed_deletions",
            "approved_actions",
            "imported_sources",
            "deleted_sources",
        ):
            data[name] = list(getattr(self, name))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RefreshRun:
        _require_schema(data)
        values = dict(data)
        values.pop("schema_version")
        for name in (
            "baseline_source_ids",
            "research_queries",
            "watch_items_evaluated",
            "proposed_additions",
            "proposed_refreshes",
            "proposed_superseded",
            "proposed_deletions",
            "approved_actions",
            "imported_sources",
            "deleted_sources",
        ):
            values[name] = tuple(str(item) for item in values.get(name, []))
        return cls(**values)
