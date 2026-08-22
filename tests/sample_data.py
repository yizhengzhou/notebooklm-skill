from notebooklm_skill.models import (
    AdvisorProfile,
    BackendRef,
    PersonaProfile,
    RefreshRun,
    ResearchProfile,
    SourceRecord,
    WatchItem,
)


def sample_profile(title: str = "Cross-domain advisor") -> AdvisorProfile:
    return AdvisorProfile(
        advisor_id="cross-domain-advisor",
        title=title,
        backend=BackendRef(type="gemini-notebook", notebook_id="notebook-123"),
        persona=PersonaProfile(
            instructions="Act as an evidence-focused, cross-domain research advisor.",
            response_length="longer",
        ),
        research=ResearchProfile(
            brief="Track meaningful changes in this research area.",
            queries=("What changed recently?", "What evidence challenges our assumptions?"),
            preferred_domains=("example.com",),
        ),
    )


def sample_watchlist() -> tuple[WatchItem, ...]:
    return (
        WatchItem(
            watch_id="watch-001",
            kind="assumption",
            statement="The core product assumption remains supported.",
            questions=("What new supporting or opposing evidence exists?",),
            revisit_when=("A high-quality conflicting study is published",),
        ),
    )


def sample_sources() -> tuple[SourceRecord, ...]:
    return (
        SourceRecord(
            local_id="src-001",
            backend_source_id="backend-source-1",
            title="Canonical source",
            url="https://example.com/research",
            canonical_url="https://example.com/research",
            origin="manual",
            state="pinned",
        ),
    )


def sample_run() -> RefreshRun:
    return RefreshRun(
        run_id="refresh-001",
        advisor_id="cross-domain-advisor",
        status="completed",
        started_at="2026-08-22T01:00:00Z",
        completed_at="2026-08-22T01:05:00Z",
        baseline_source_ids=("src-001",),
        research_queries=("What changed recently?",),
        watch_items_evaluated=("watch-001",),
        summary="No confirmed change.",
    )
