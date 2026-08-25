"""Command-line entry point for the thin Evergreen Notebook skill."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from notebooklm_skill.apply_plan import build_apply_plan, write_apply_plan
from notebooklm_skill.evergreen import EvergreenService, format_answer_with_citations, load_setup_document
from notebooklm_skill.gemini_backend import GeminiNotebookBackend
from notebooklm_skill.preview import read_preview_plan
from notebooklm_skill.refresh import RefreshPlanner, read_refresh_plan, write_refresh_plan
from notebooklm_skill.storage import AdvisorStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notebooklm-evergreen")
    parser.add_argument("--state-root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)

    setup = commands.add_parser("setup", help="Create or adopt an Evergreen Advisor")
    setup.add_argument("--config", type=Path, required=True)
    setup.add_argument("--adopt-notebook-id")

    show = commands.add_parser("show", help="Show local Advisor state")
    show.add_argument("--advisor-id", required=True)

    source_add_url = commands.add_parser(
        "source-add-url", help="Add or reconcile a canonical URL source"
    )
    source_add_url.add_argument("--advisor-id", required=True)
    source_add_url.add_argument("--url", required=True)
    source_add_url.add_argument("--state", choices=("active", "pinned"), default="active")

    source_add_file = commands.add_parser(
        "source-add-file", help="Add or reconcile a local file as a text source"
    )
    source_add_file.add_argument("--advisor-id", required=True)
    source_add_file.add_argument("--file", type=Path, required=True)
    source_add_file.add_argument(
        "--title", help="Defaults to the file name if not given"
    )
    source_add_file.add_argument("--state", choices=("active", "pinned"), default="active")

    source_state = commands.add_parser("source-state", help="Pin or classify a registered source")
    source_state.add_argument("--advisor-id", required=True)
    source_state.add_argument("--local-id", required=True)
    source_state.add_argument("--state", choices=("active", "pinned", "broken"), required=True)

    ask = commands.add_parser("ask", help="Ask the source-grounded Advisor")
    ask.add_argument("--advisor-id", required=True)
    question = ask.add_mutually_exclusive_group(required=True)
    question.add_argument("--question")
    question.add_argument("--question-file", type=Path)

    preview = commands.add_parser("preview", help="Run resumable Deep Research preview")
    preview.add_argument("--advisor-id", required=True)
    preview.add_argument("--run-id", required=True)
    preview.add_argument("--work-directory", type=Path, required=True)
    preview.add_argument("--timeout", type=float, default=1800)

    plan_apply = commands.add_parser("plan-apply", help="Build a reviewed addition/retirement plan")
    plan_apply.add_argument("--advisor-id", required=True)
    plan_apply.add_argument("--plan-id", required=True)
    plan_apply.add_argument("--preview", type=Path, required=True)
    plan_apply.add_argument("--selection", type=Path, required=True)
    plan_apply.add_argument("--retirements", type=Path)
    plan_apply.add_argument("--output-directory", type=Path, required=True)

    apply = commands.add_parser("apply", help="Execute an explicitly approved Apply Plan")
    apply.add_argument("--advisor-id", required=True)
    apply.add_argument("--run-id", required=True)
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--approved-digest", required=True)
    apply.add_argument("--evidence-directory", type=Path, required=True)

    refresh_plan = commands.add_parser("refresh-plan", help="Review URL/Drive freshness")
    refresh_plan.add_argument("--advisor-id", required=True)
    refresh_plan.add_argument("--plan-id", required=True)
    refresh_plan.add_argument("--output-directory", type=Path, required=True)

    refresh_apply = commands.add_parser(
        "refresh-apply", help="Execute an explicitly approved native refresh plan"
    )
    refresh_apply.add_argument("--advisor-id", required=True)
    refresh_apply.add_argument("--run-id", required=True)
    refresh_apply.add_argument("--plan", type=Path, required=True)
    refresh_apply.add_argument("--approved-digest", required=True)
    refresh_apply.add_argument("--work-directory", type=Path, required=True)
    refresh_apply.add_argument("--research-summary", default="")

    export = commands.add_parser("export", help="Export a backend-neutral Advisor bundle")
    export.add_argument("--advisor-id", required=True)
    export.add_argument("--destination", type=Path, required=True)
    return parser


def _selected_urls(path: Path) -> set[str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, list) or not all(isinstance(item, str) for item in document):
        raise ValueError("Selection file must be a JSON array of candidate URLs")
    return set(document)


def _retirement_requests(path: Path | None) -> dict[str, tuple[str, str]]:
    if path is None:
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(local_id): (str(item["replacement_url"]), str(item["reason"]))
        for local_id, item in document.items()
    }


def _print(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False))


async def run(args: argparse.Namespace) -> int:
    store = AdvisorStore(args.state_root)
    backend = GeminiNotebookBackend()
    service = EvergreenService(backend, store)

    if args.command == "setup":
        advisor_id, title, persona, research, watchlist = load_setup_document(args.config)
        result = await service.setup(
            advisor_id=advisor_id,
            title=title,
            persona=persona,
            research=research,
            watchlist=watchlist,
            notebook_id=args.adopt_notebook_id,
        )
        _print(
            {
                "advisor_id": advisor_id,
                "notebook_id": result.notebook.notebook_id,
                "persona_verified": True,
            }
        )
    elif args.command == "show":
        profile, watchlist, sources, runs = store.load_snapshot(args.advisor_id)
        _print(
            {
                "advisor_id": profile.advisor_id,
                "title": profile.title,
                "backend": profile.backend.to_dict(),
                "watch_items": len(watchlist),
                "source_count": len(sources),
                "sources": [
                    {
                        "local_id": source.local_id,
                        "title": source.title,
                        "state": source.state,
                        "backend_source_id": source.backend_source_id,
                    }
                    for source in sources
                ],
                "refresh_runs": len(runs),
            }
        )
    elif args.command == "source-add-url":
        source = await service.add_url_source(
            advisor_id=args.advisor_id,
            url=args.url,
            state=args.state,
        )
        _print(source.to_dict())
    elif args.command == "source-add-file":
        if not args.file.is_file():
            raise SystemExit(f"File not found: {args.file}")
        content = args.file.read_text(encoding="utf-8")
        title = args.title or args.file.name
        source = await service.add_text_source(
            advisor_id=args.advisor_id,
            title=title,
            content=content,
            state=args.state,
        )
        _print(source.to_dict())
    elif args.command == "source-state":
        source = service.set_source_state(
            advisor_id=args.advisor_id,
            local_id=args.local_id,
            state=args.state,
        )
        _print(source.to_dict())
    elif args.command == "ask":
        question = (
            args.question_file.read_text(encoding="utf-8")
            if args.question_file is not None
            else args.question
        )
        ask_res = await service.ask(args.advisor_id, question)
        profile, _, sources = store.load(args.advisor_id)
        formatted = format_answer_with_citations(ask_res, sources)
        _print(
            {
                "advisor_id": args.advisor_id,
                "question": question.strip(),
                "answer": ask_res.answer,
                "formatted_answer": formatted,
                "conversation_id": ask_res.conversation_id,
                "turn_number": ask_res.turn_number,
                "citations_count": len(ask_res.references),
            }
        )
    elif args.command == "preview":
        plan = await service.preview(
            advisor_id=args.advisor_id,
            run_id=args.run_id,
            work_directory=args.work_directory,
            timeout=args.timeout,
        )
        _print(
            {
                "research_task_id": plan.research_task_id,
                "proposed_additions": len(plan.proposed_additions),
                "preview": str(args.work_directory / "preview.json"),
            }
        )
    elif args.command == "plan-apply":
        profile, _, sources = store.load(args.advisor_id)
        preview = read_preview_plan(args.preview)
        if preview.advisor_id != profile.advisor_id:
            raise ValueError("Preview belongs to a different Advisor")
        plan = build_apply_plan(
            plan_id=args.plan_id,
            preview=preview,
            sources=sources,
            retirement_requests=_retirement_requests(args.retirements),
            selected_urls=_selected_urls(args.selection),
        )
        paths = write_apply_plan(plan, args.output_directory)
        _print({"plan_digest": plan.digest, "paths": [str(path) for path in paths]})
    elif args.command == "apply":
        result = await service.apply(
            advisor_id=args.advisor_id,
            run_id=args.run_id,
            plan_path=args.plan,
            approved_digest=args.approved_digest,
            evidence_directory=args.evidence_directory,
        )
        _print(result.to_dict())
    elif args.command == "refresh-plan":
        profile, _, sources = store.load(args.advisor_id)
        plan = await RefreshPlanner(backend).build(
            plan_id=args.plan_id,
            advisor_id=args.advisor_id,
            notebook_id=profile.backend.notebook_id,
            registry=sources,
        )
        paths = write_refresh_plan(plan, args.output_directory)
        _print(
            {
                "plan_digest": plan.digest,
                "proposed_refresh_ids": list(plan.proposed_refresh_ids),
                "paths": [str(path) for path in paths],
            }
        )
    elif args.command == "refresh-apply":
        plan = read_refresh_plan(args.plan)
        result = await service.commit_native_refresh(
            advisor_id=args.advisor_id,
            run_id=args.run_id,
            plan=plan,
            plan_path=args.plan,
            approved_digest=args.approved_digest,
            work_directory=args.work_directory,
            research_summary=args.research_summary,
        )
        _print(result.to_dict())
    elif args.command == "export":
        result = await service.export_advisor(args.advisor_id, args.destination)
        _print({"advisor_id": args.advisor_id, **result})
    return 0


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
