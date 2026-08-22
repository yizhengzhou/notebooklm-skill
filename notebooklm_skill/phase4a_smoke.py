"""Phase 4A smoke: one Preview Run followed by a review-only Apply Plan."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from notebooklm_skill.apply_plan import build_apply_plan, write_apply_plan
from notebooklm_skill.gemini_backend import GeminiNotebookBackend
from notebooklm_skill.models import SourceRecord
from notebooklm_skill.preview import PreviewEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook-id", required=True)
    parser.add_argument("--query-file", type=Path, required=True)
    parser.add_argument("--work-directory", type=Path, required=True)
    parser.add_argument("--pinned-source-id", required=True)
    parser.add_argument("--legacy-source-id", required=True)
    parser.add_argument("--preferred-domain", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=1800)
    return parser


async def run(args: argparse.Namespace) -> int:
    query = args.query_file.read_text(encoding="utf-8").strip()
    backend = GeminiNotebookBackend()
    baseline = await backend.list_sources(args.notebook_id)
    baseline_by_id = {source.source_id: source for source in baseline}
    expected_ids = {args.pinned_source_id, args.legacy_source_id}
    if set(baseline_by_id) != expected_ids:
        raise RuntimeError(
            f"Expected exactly the approved Pinned and Legacy sources; got {set(baseline_by_id)}"
        )

    preview = await PreviewEngine(backend).run(
        run_id="preview-4a-001",
        advisor_id="disposable-safe-apply",
        notebook_id=args.notebook_id,
        query=query,
        work_directory=args.work_directory / "preview",
        max_new_sources=3,
        preferred_domains=tuple(args.preferred_domain),
        timeout=args.timeout,
    )
    if not preview.proposed_additions:
        raise RuntimeError("Research produced no approved addition candidate")
    replacement = preview.proposed_additions[0]
    registry = (
        SourceRecord(
            local_id="src-pinned",
            backend_source_id=args.pinned_source_id,
            title=baseline_by_id[args.pinned_source_id].title,
            state="pinned",
            origin="manual",
        ),
        SourceRecord(
            local_id="src-legacy",
            backend_source_id=args.legacy_source_id,
            title=baseline_by_id[args.legacy_source_id].title,
            state="active",
            origin="manual",
        ),
    )
    plan = build_apply_plan(
        plan_id="apply-4a-001",
        preview=preview,
        sources=registry,
        retirement_requests={
            "src-legacy": (
                replacement.url,
                "Disposable Legacy fixture is retired only after its approved replacement is ready.",
            )
        },
    )
    json_path, markdown_path = write_apply_plan(plan, args.work_directory / "apply")
    print(
        json.dumps(
            {
                "status": "review_required",
                "notebook_id": args.notebook_id,
                "research_task_id": plan.research_task_id,
                "source_snapshot_ids": list(plan.source_snapshot_ids),
                "protected_source_ids": list(plan.protected_source_ids),
                "addition_count": len(plan.additions),
                "retirement_count": len(plan.retirements),
                "replacement_url": replacement.url,
                "plan_digest": plan.digest,
                "apply_plan_json": str(json_path),
                "apply_plan_markdown": str(markdown_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
