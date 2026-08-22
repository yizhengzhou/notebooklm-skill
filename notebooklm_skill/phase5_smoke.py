"""Plan or execute an explicitly approved Phase 5 source refresh."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from notebooklm_skill.gemini_backend import GeminiNotebookBackend
from notebooklm_skill.refresh import (
    RefreshExecutor,
    RefreshPlanner,
    write_refresh_plan,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    preview = commands.add_parser("plan")
    preview.add_argument("--plan-id", required=True)
    preview.add_argument("--advisor-id", required=True)
    preview.add_argument("--notebook-id", required=True)
    preview.add_argument("--output-directory", type=Path, required=True)
    apply = commands.add_parser("apply")
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--approved-digest", required=True)
    apply.add_argument("--work-directory", type=Path, required=True)
    apply.add_argument("--research-summary", default="")
    return parser


async def run(args: argparse.Namespace) -> int:
    backend = GeminiNotebookBackend()
    if args.command == "plan":
        plan = await RefreshPlanner(backend).build(
            plan_id=args.plan_id,
            advisor_id=args.advisor_id,
            notebook_id=args.notebook_id,
        )
        paths = write_refresh_plan(plan, args.output_directory)
        print(
            json.dumps(
                {
                    "plan_digest": plan.digest,
                    "proposed_refresh_ids": list(plan.proposed_refresh_ids),
                    "paths": [str(path) for path in paths],
                },
                ensure_ascii=False,
            )
        )
        return 0
    result = await RefreshExecutor(backend).execute(
        plan_path=args.plan,
        approved_digest=args.approved_digest,
        work_directory=args.work_directory,
        research_summary=args.research_summary,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False))
    return 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
