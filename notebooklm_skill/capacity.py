"""Notebook and source capacity checks for fail-closed source mutation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from notebooklm_skill.backend import AccountLimits, NotebookBackend

DEFAULT_STANDARD_NOTEBOOK_LIMIT = 100
DEFAULT_STANDARD_SOURCE_LIMIT = 50

CapacityState = Literal["healthy", "warning", "critical", "exhausted", "blocked_capacity"]
LimitSource = Literal["live_server", "official_standard_fallback"]


class SourceCapacityExceededError(RuntimeError):
    """A source mutation would exceed the notebook's effective source limit."""

    def __init__(self, capacity: SourceCapacity) -> None:
        super().__init__(
            "Source capacity exhausted: "
            f"current={capacity.used}, planned_additions={capacity.planned_additions}, "
            f"peak={capacity.peak_used}, limit={capacity.limit}. "
            "No source-add RPC was sent. Retire reviewed sources, use another notebook, "
            "or upgrade the NotebookLM plan."
        )
        self.capacity = capacity


class SourceAddNotCommittedError(RuntimeError):
    """The backend did not expose the source after an apparently successful add."""


@dataclass(frozen=True)
class SourceCapacity:
    used: int
    limit: int
    remaining: int
    planned_additions: int
    peak_used: int
    utilization: float
    status: CapacityState
    limit_source: LimitSource
    tier: int | None = None
    preparing_orphans: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "planned_additions": self.planned_additions,
            "peak_used": self.peak_used,
            "utilization": self.utilization,
            "status": self.status,
            "limit_source": self.limit_source,
            "tier": self.tier,
            "preparing_orphans": self.preparing_orphans,
        }


def _capacity_state(*, used: int, peak_used: int, limit: int) -> CapacityState:
    if peak_used > limit:
        return "blocked_capacity"
    if used >= limit:
        return "exhausted"
    ratio = used / limit
    if ratio >= 0.9:
        return "critical"
    if ratio >= 0.8:
        return "warning"
    return "healthy"


async def inspect_source_capacity(
    backend: NotebookBackend,
    notebook_id: str,
    *,
    planned_additions: int = 0,
) -> SourceCapacity:
    """Read authoritative backend rows and calculate the planned peak usage.

    Every row returned by ``list_sources`` counts, regardless of processing
    state. NotebookLM may retain a ``preparing`` row after a failed upload and
    that row still consumes source quota.
    """
    if planned_additions < 0:
        raise ValueError("planned_additions must be non-negative")

    sources = await backend.list_sources(notebook_id)
    limits = AccountLimits()
    limit_source: LimitSource = "official_standard_fallback"
    if backend.capabilities.account_limits:
        try:
            limits = await backend.get_account_limits()
        except Exception:
            # Source operations still have their own backend verification. A
            # failed optional quota lookup uses the official free-tier limit,
            # never an unlimited assumption.
            limits = AccountLimits()
    if limits.source_limit is not None:
        limit = limits.source_limit
        limit_source = "live_server"
    else:
        limit = DEFAULT_STANDARD_SOURCE_LIMIT

    used = len(sources)
    peak_used = used + planned_additions
    remaining = max(limit - peak_used, 0)
    preparing = sum(source.status == "preparing" for source in sources)
    return SourceCapacity(
        used=used,
        limit=limit,
        remaining=remaining,
        planned_additions=planned_additions,
        peak_used=peak_used,
        utilization=used / limit,
        status=_capacity_state(used=used, peak_used=peak_used, limit=limit),
        limit_source=limit_source,
        tier=limits.tier,
        preparing_orphans=preparing,
    )


async def require_source_capacity(
    backend: NotebookBackend,
    notebook_id: str,
    *,
    planned_additions: int,
) -> SourceCapacity:
    """Fail before mutation when the plan cannot fit at peak usage."""
    capacity = await inspect_source_capacity(
        backend,
        notebook_id,
        planned_additions=planned_additions,
    )
    if capacity.peak_used > capacity.limit or (
        planned_additions > 0 and capacity.used >= capacity.limit
    ):
        raise SourceCapacityExceededError(capacity)
    return capacity
