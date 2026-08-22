"""Execute one explicitly approved Phase 4B Apply Plan."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from notebooklm_skill.apply_executor import ApplyExecutor
from notebooklm_skill.gemini_backend import GeminiNotebookBackend


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--approved-digest", required=True)
    parser.add_argument("--evidence-directory", type=Path, required=True)
    return parser


async def run(args: argparse.Namespace) -> int:
    result = await ApplyExecutor(GeminiNotebookBackend()).execute(
        plan_path=args.plan,
        approved_digest=args.approved_digest,
        evidence_directory=args.evidence_directory,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False))
    return 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
