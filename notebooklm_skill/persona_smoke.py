"""Non-destructive Phase 1 live smoke test for notebook creation and persona read-back."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from notebooklm_skill.advisor import AdvisorService, PersonaSetupError
from notebooklm_skill.gemini_backend import GeminiNotebookBackend


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--persona-file", type=Path, required=True)
    parser.add_argument(
        "--response-length",
        choices=("default", "longer", "shorter"),
        default="default",
    )
    parser.add_argument("--profile")
    return parser


async def run(args: argparse.Namespace) -> int:
    persona = args.persona_file.read_text(encoding="utf-8").strip()
    backend = GeminiNotebookBackend(profile=args.profile)
    service = AdvisorService(backend)
    try:
        result = await service.create(args.title, persona, args.response_length)
    except PersonaSetupError as exc:
        print(
            json.dumps(
                {
                    "status": "persona_setup_failed",
                    "notebook_id": exc.notebook_id,
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "notebook_id": result.notebook.notebook_id,
                "title": result.notebook.title,
                "persona_verified": True,
                "response_length": result.chat_config.response_length,
            },
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
