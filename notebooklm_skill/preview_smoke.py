"""Phase 3 live smoke test for a non-mutating Deep Research preview."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from notebooklm_skill.gemini_backend import GeminiNotebookBackend
from notebooklm_skill.preview import PreviewEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--advisor-id", required=True)
    parser.add_argument("--notebook-id", required=True)
    parser.add_argument("--query-file", type=Path, required=True)
    parser.add_argument("--work-directory", type=Path, required=True)
    parser.add_argument("--max-new-sources", type=int, default=10)
    parser.add_argument("--preferred-domain", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=1800)
    return parser


async def run(args: argparse.Namespace) -> int:
    query = args.query_file.read_text(encoding="utf-8").strip()
    engine = PreviewEngine(GeminiNotebookBackend())
    plan = await engine.run(
        run_id=args.run_id,
        advisor_id=args.advisor_id,
        notebook_id=args.notebook_id,
        query=query,
        work_directory=args.work_directory,
        max_new_sources=args.max_new_sources,
        preferred_domains=tuple(args.preferred_domain),
        timeout=args.timeout,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "run_id": plan.run_id,
                "notebook_id": plan.notebook_id,
                "research_task_id": plan.research_task_id,
                "sources_unchanged": plan.baseline_source_ids == plan.final_source_ids,
                "candidate_count": len(plan.candidates),
                "proposed_addition_count": len(plan.proposed_additions),
                "preview_json": str(args.work_directory / "preview.json"),
                "preview_markdown": str(args.work_directory / "preview.md"),
            },
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
