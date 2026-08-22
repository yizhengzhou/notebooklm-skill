"""Non-mutating Evergreen research preview engine."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from notebooklm_skill.backend import NotebookBackend, ResearchCandidate, SourceSnapshot
from notebooklm_skill.models import SCHEMA_VERSION, _validate_id
from notebooklm_skill.storage import _atomic_write, _read_json, _write_json

_TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


class PreviewTimeoutError(TimeoutError):
    def __init__(self, task_id: str, checkpoint_path: Path) -> None:
        super().__init__(f"Research task {task_id} timed out; resume from {checkpoint_path}")
        self.task_id = task_id
        self.checkpoint_path = checkpoint_path


class ResearchFailedError(RuntimeError):
    pass


class SourceMutationDetectedError(RuntimeError):
    pass


@dataclass(frozen=True)
class CandidateReview:
    title: str
    url: str
    canonical_url: str
    cited: bool
    preferred_domain: bool
    ordinal: int | None
    decision: Literal["propose_add", "already_present", "duplicate", "over_budget"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "canonical_url": self.canonical_url,
            "cited": self.cited,
            "preferred_domain": self.preferred_domain,
            "ordinal": self.ordinal,
            "decision": self.decision,
        }


@dataclass(frozen=True)
class PreviewPlan:
    run_id: str
    advisor_id: str
    notebook_id: str
    research_task_id: str
    query: str
    baseline_source_ids: tuple[str, ...]
    final_source_ids: tuple[str, ...]
    candidates: tuple[CandidateReview, ...]
    research_summary: str = ""

    @property
    def proposed_additions(self) -> tuple[CandidateReview, ...]:
        return tuple(item for item in self.candidates if item.decision == "propose_add")

    def to_dict(self) -> dict[str, Any]:
        counts = {
            decision: sum(item.decision == decision for item in self.candidates)
            for decision in ("propose_add", "already_present", "duplicate", "over_budget")
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "advisor_id": self.advisor_id,
            "notebook_id": self.notebook_id,
            "research_task_id": self.research_task_id,
            "query": self.query,
            "baseline_source_ids": list(self.baseline_source_ids),
            "final_source_ids": list(self.final_source_ids),
            "sources_unchanged": self.baseline_source_ids == self.final_source_ids,
            "counts": counts,
            "candidates": [item.to_dict() for item in self.candidates],
            "research_summary": self.research_summary,
        }


def read_preview_plan(path: Path) -> PreviewPlan:
    document = _read_json(path)
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported Preview Plan schema")
    candidates = tuple(
        CandidateReview(
            title=str(item["title"]),
            url=str(item["url"]),
            canonical_url=str(item["canonical_url"]),
            cited=bool(item["cited"]),
            preferred_domain=bool(item["preferred_domain"]),
            ordinal=int(item["ordinal"]) if item.get("ordinal") is not None else None,
            decision=item["decision"],
        )
        for item in document["candidates"]
    )
    plan = PreviewPlan(
        run_id=str(document["run_id"]),
        advisor_id=str(document["advisor_id"]),
        notebook_id=str(document["notebook_id"]),
        research_task_id=str(document["research_task_id"]),
        query=str(document["query"]),
        baseline_source_ids=tuple(str(item) for item in document["baseline_source_ids"]),
        final_source_ids=tuple(str(item) for item in document["final_source_ids"]),
        candidates=candidates,
        research_summary=str(document.get("research_summary", "")),
    )
    if plan.baseline_source_ids != plan.final_source_ids:
        raise ValueError("Preview Plan contains a mutated source snapshot")
    return plan


def canonicalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"Unsupported research URL: {url!r}")
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower()
    port = parsed.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        hostname = f"{hostname}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_QUERY_KEYS and not key.lower().startswith("utm_")
    ]
    return urlunsplit((scheme, hostname, path, urlencode(sorted(query)), ""))


def _source_document(source: SourceSnapshot) -> dict[str, Any]:
    return {"source_id": source.source_id, "title": source.title, "url": source.url}


def _source_from_document(data: dict[str, Any]) -> SourceSnapshot:
    return SourceSnapshot(
        source_id=str(data["source_id"]),
        title=str(data["title"]),
        url=str(data["url"]) if data.get("url") is not None else None,
    )


def _is_preferred_domain(url: str, preferred_domains: tuple[str, ...]) -> bool:
    hostname = (urlsplit(url).hostname or "").lower()
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in preferred_domains)


def _build_candidate_reviews(
    candidates: tuple[ResearchCandidate, ...],
    baseline: tuple[SourceSnapshot, ...],
    max_new_sources: int,
    preferred_domains: tuple[str, ...],
) -> tuple[CandidateReview, ...]:
    if max_new_sources < 1:
        raise ValueError("max_new_sources must be positive")
    existing_urls = {
        canonicalize_url(source.url)
        for source in baseline
        if source.url and source.url.startswith(("http://", "https://"))
    }
    normalized_domains = tuple(
        domain.lower().strip().lstrip(".") for domain in preferred_domains if domain.strip()
    )
    ordered = sorted(
        candidates,
        key=lambda item: (
            not _is_preferred_domain(item.url, normalized_domains),
            not item.cited,
            item.ordinal is None,
            item.ordinal or 0,
            item.title.lower(),
        ),
    )
    seen: set[str] = set()
    additions = 0
    reviews: list[CandidateReview] = []
    for candidate in ordered:
        canonical = canonicalize_url(candidate.url)
        if canonical in existing_urls:
            decision = "already_present"
        elif canonical in seen:
            decision = "duplicate"
        elif additions >= max_new_sources:
            decision = "over_budget"
            seen.add(canonical)
        else:
            decision = "propose_add"
            additions += 1
            seen.add(canonical)
        reviews.append(
            CandidateReview(
                title=candidate.title,
                url=candidate.url,
                canonical_url=canonical,
                cited=candidate.cited,
                preferred_domain=_is_preferred_domain(candidate.url, normalized_domains),
                ordinal=candidate.ordinal,
                decision=decision,
            )
        )
    return tuple(reviews)


class PreviewEngine:
    def __init__(
        self,
        backend: NotebookBackend,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.backend = backend
        self.sleep = sleep
        self.monotonic = monotonic

    async def run(
        self,
        *,
        run_id: str,
        advisor_id: str,
        notebook_id: str,
        query: str,
        work_directory: Path,
        max_new_sources: int = 10,
        preferred_domains: tuple[str, ...] = (),
        timeout: float = 1800,
        poll_interval: float = 5,
    ) -> PreviewPlan:
        _validate_id(run_id, "run_id")
        _validate_id(advisor_id, "advisor_id")
        if not query.strip():
            raise ValueError("Research query cannot be empty")
        work_directory.mkdir(parents=True, exist_ok=True)
        checkpoint_path = work_directory / "checkpoint.json"

        if checkpoint_path.exists():
            checkpoint = _read_json(checkpoint_path)
            self._validate_checkpoint(checkpoint, run_id, advisor_id, notebook_id, query)
            task_id = str(checkpoint["research_task_id"])
            baseline = tuple(_source_from_document(item) for item in checkpoint["baseline_sources"])
        else:
            baseline = await self.backend.list_sources(notebook_id)
            started = await self.backend.start_research(notebook_id, query, mode="deep")
            task_id = started.task_id
            checkpoint = {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "advisor_id": advisor_id,
                "notebook_id": notebook_id,
                "query": query,
                "mode": "deep",
                "research_task_id": task_id,
                "research_session_id": started.session_id,
                "status": "in_progress",
                "baseline_sources": [_source_document(item) for item in baseline],
            }
            _write_json(checkpoint_path, checkpoint)

        deadline = self.monotonic() + timeout
        while True:
            result = await self.backend.poll_research(notebook_id, task_id)
            if result.status == "completed":
                break
            if result.status in {"failed", "not_found"}:
                raise ResearchFailedError(
                    f"Research task {task_id} ended with status {result.status}"
                )
            if self.monotonic() >= deadline:
                raise PreviewTimeoutError(task_id, checkpoint_path)
            await self.sleep(min(poll_interval, max(0.0, deadline - self.monotonic())))

        final_sources = await self.backend.list_sources(notebook_id)
        baseline_ids = tuple(sorted(item.source_id for item in baseline))
        final_ids = tuple(sorted(item.source_id for item in final_sources))
        if baseline_ids != final_ids:
            raise SourceMutationDetectedError(
                f"Source IDs changed during preview: {baseline_ids!r} -> {final_ids!r}"
            )

        plan = PreviewPlan(
            run_id=run_id,
            advisor_id=advisor_id,
            notebook_id=notebook_id,
            research_task_id=task_id,
            query=query,
            baseline_source_ids=baseline_ids,
            final_source_ids=final_ids,
            candidates=_build_candidate_reviews(
                result.candidates,
                baseline,
                max_new_sources,
                preferred_domains,
            ),
            research_summary=result.summary,
        )
        _write_json(work_directory / "preview.json", plan.to_dict())
        _atomic_write(work_directory / "preview.md", self._render_markdown(plan).encode())
        checkpoint["status"] = "completed"
        _write_json(checkpoint_path, checkpoint)
        return plan

    @staticmethod
    def _validate_checkpoint(
        checkpoint: dict[str, Any],
        run_id: str,
        advisor_id: str,
        notebook_id: str,
        query: str,
    ) -> None:
        expected = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "advisor_id": advisor_id,
            "notebook_id": notebook_id,
            "query": query,
            "mode": "deep",
        }
        mismatches = {
            key: (checkpoint.get(key), value)
            for key, value in expected.items()
            if checkpoint.get(key) != value
        }
        if mismatches:
            raise ValueError(f"Checkpoint does not match requested preview: {mismatches}")

    @staticmethod
    def _render_markdown(plan: PreviewPlan) -> str:
        lines = [
            f"# Evergreen Preview: {plan.run_id}",
            "",
            f"- Research task: `{plan.research_task_id}`",
            f"- Sources unchanged: **{plan.baseline_source_ids == plan.final_source_ids}**",
            f"- Proposed additions: **{len(plan.proposed_additions)}**",
            "",
            "## Proposed additions",
            "",
        ]
        if not plan.proposed_additions:
            lines.append("No new sources are proposed.")
        for item in plan.proposed_additions:
            signals = []
            if item.preferred_domain:
                signals.append("preferred domain")
            if item.cited:
                signals.append("cited")
            suffix = f" — {', '.join(signals)}" if signals else ""
            lines.append(f"- [{item.title}]({item.url}){suffix}")
        if plan.research_summary:
            lines.extend(("", "## Research summary", "", plan.research_summary))
        return "\n".join(lines) + "\n"
