import json
from dataclasses import replace
from pathlib import Path

import pytest

from notebooklm_skill.apply_plan import build_apply_plan, verify_apply_plan, write_apply_plan
from notebooklm_skill.models import SourceRecord
from notebooklm_skill.preview import CandidateReview, PreviewPlan


def sample_preview() -> PreviewPlan:
    return PreviewPlan(
        run_id="preview-001",
        advisor_id="advisor-001",
        notebook_id="notebook-001",
        research_task_id="research-001",
        query="What changed?",
        baseline_source_ids=("backend-pinned", "backend-legacy"),
        final_source_ids=("backend-pinned", "backend-legacy"),
        candidates=(
            CandidateReview(
                title="Official replacement",
                url="https://support.google.com/notebooklm/answer/1",
                canonical_url="https://support.google.com/notebooklm/answer/1",
                cited=True,
                preferred_domain=True,
                ordinal=1,
                decision="propose_add",
            ),
        ),
    )


def sample_sources() -> tuple[SourceRecord, ...]:
    return (
        SourceRecord(
            local_id="src-pinned",
            backend_source_id="backend-pinned",
            title="Pinned baseline",
            state="pinned",
            origin="manual",
        ),
        SourceRecord(
            local_id="src-legacy",
            backend_source_id="backend-legacy",
            title="Legacy source",
            state="active",
            origin="manual",
        ),
    )


def test_apply_plan_is_review_only_signed_and_round_trippable(tmp_path: Path) -> None:
    plan = build_apply_plan(
        plan_id="apply-001",
        preview=sample_preview(),
        sources=sample_sources(),
        retirement_requests={
            "src-legacy": (
                "https://support.google.com/notebooklm/answer/1",
                "Disposable legacy source is replaced by the approved official source.",
            )
        },
    )
    json_path, markdown_path = write_apply_plan(plan, tmp_path)
    verified = verify_apply_plan(json_path)

    assert verified["plan_digest"] == plan.digest
    assert verified["status"] == "review_required"
    assert verified["protected_source_ids"] == ["backend-pinned"]
    assert verified["retirements"][0]["backup_required"] is True
    assert "Required execution order" in markdown_path.read_text()


def test_apply_plan_uses_explicit_selection_across_full_candidate_pool() -> None:
    preview = sample_preview()
    over_budget = CandidateReview(
        title="Independent field report",
        url="https://example.com/field-report",
        canonical_url="https://example.com/field-report",
        cited=True,
        preferred_domain=False,
        ordinal=2,
        decision="over_budget",
    )
    preview = replace(preview, candidates=(*preview.candidates, over_budget))

    plan = build_apply_plan(
        plan_id="apply-001",
        preview=preview,
        sources=sample_sources(),
        retirement_requests={},
        selected_urls={over_budget.url},
    )

    assert [item.url for item in plan.additions] == [over_budget.url]


def test_apply_plan_rejects_selection_above_preview_budget() -> None:
    preview = sample_preview()
    extra = tuple(
        CandidateReview(
            title=f"Field report {index}",
            url=f"https://example.com/report-{index}",
            canonical_url=f"https://example.com/report-{index}",
            cited=True,
            preferred_domain=False,
            ordinal=index,
            decision="over_budget",
        )
        for index in (2, 3)
    )
    preview = replace(preview, candidates=(*preview.candidates, *extra))

    with pytest.raises(ValueError, match="source budget"):
        build_apply_plan(
            plan_id="apply-001",
            preview=preview,
            sources=sample_sources(),
            retirement_requests={},
            selected_urls={item.url for item in preview.candidates},
        )


def test_apply_plan_rejects_pinned_retirement() -> None:
    with pytest.raises(ValueError, match="Pinned source cannot be retired"):
        build_apply_plan(
            plan_id="apply-001",
            preview=sample_preview(),
            sources=sample_sources(),
            retirement_requests={
                "src-pinned": (
                    "https://support.google.com/notebooklm/answer/1",
                    "Should fail",
                )
            },
        )


def test_apply_plan_rejects_unapproved_replacement() -> None:
    with pytest.raises(ValueError, match="not a proposed addition"):
        build_apply_plan(
            plan_id="apply-001",
            preview=sample_preview(),
            sources=sample_sources(),
            retirement_requests={
                "src-legacy": ("https://example.com/not-in-preview", "Should fail")
            },
        )


def test_apply_plan_detects_tampering(tmp_path: Path) -> None:
    plan = build_apply_plan(
        plan_id="apply-001",
        preview=sample_preview(),
        sources=sample_sources(),
        retirement_requests={},
    )
    json_path, _ = write_apply_plan(plan, tmp_path)
    document = json.loads(json_path.read_text())
    document["protected_source_ids"] = []
    json_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch"):
        verify_apply_plan(json_path)
