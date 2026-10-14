"""Command-line entry point for the thin Evergreen Notebook skill."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from notebooklm_skill.apply_plan import build_apply_plan, write_apply_plan
from notebooklm_skill.doctor import diagnose_project_brain
from notebooklm_skill.evergreen import (
    EvergreenService,
    format_answer_with_citations,
    load_setup_document,
    load_update_document,
)
from notebooklm_skill.backend import NotebookBackend
from notebooklm_skill.gemini_backend import GeminiNotebookBackend
from notebooklm_skill.grounding import assess_project_grounding
from notebooklm_skill.installer import (
    apply_install_plan,
    build_install_plan,
    resolve_install_target,
    uninstall_project_integration,
)
from notebooklm_skill.models import SOURCE_ROLES
from notebooklm_skill.onboarding import (
    build_onboarding_plan,
    current_git_commit,
    write_onboarding_plan,
)
from notebooklm_skill.preview import read_preview_plan
from notebooklm_skill.project_brain import bind_project, discover_project_brain
from notebooklm_skill.refresh import RefreshPlanner, read_refresh_plan, write_refresh_plan
from notebooklm_skill.storage import AdvisorStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notebooklm-evergreen")
    parser.add_argument("--state-root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)

    setup = commands.add_parser("setup", help="Create or adopt an Evergreen Advisor")
    setup.add_argument("--config", type=Path, required=True)
    setup.add_argument("--adopt-notebook-id")

    list_advisors = commands.add_parser("list-advisors", help="List all registered Advisors")
    list_advisors.add_argument("--json", action="store_true", help="Output as JSON")

    update_config = commands.add_parser("update-config", help="Update configuration of an existing Advisor")
    update_config.add_argument("--config", type=Path, required=True)

    install_plan = commands.add_parser(
        "brain-install-plan",
        help="Preview no-clobber project-local MCP and Skill installation",
    )
    install_plan.add_argument("--project-root", type=Path, default=Path("."))
    install_plan.add_argument(
        "--client", choices=("auto", "pi", "claude", "generic"), default="auto"
    )

    brain_install = commands.add_parser(
        "brain-install",
        help="Install project-local MCP and Skill after explicit confirmation",
    )
    brain_install.add_argument("--project-root", type=Path, default=Path("."))
    brain_install.add_argument(
        "--client", choices=("auto", "pi", "claude", "generic"), default="auto"
    )
    brain_install.add_argument("--confirm", action="store_true")

    brain_doctor = commands.add_parser(
        "brain-doctor",
        help="Verify installation, tools, binding, backend access, and grounding",
    )
    brain_doctor.add_argument("--project-root", type=Path, default=Path("."))
    brain_doctor.add_argument(
        "--client", choices=("auto", "pi", "claude", "generic"), default="auto"
    )

    brain_uninstall = commands.add_parser(
        "brain-uninstall",
        help="Remove only the managed project-local MCP and Skill integration",
    )
    brain_uninstall.add_argument("--project-root", type=Path, default=Path("."))
    brain_uninstall.add_argument(
        "--client", choices=("auto", "pi", "claude", "generic"), default="auto"
    )
    brain_uninstall.add_argument("--confirm", action="store_true")

    brain_init = commands.add_parser(
        "brain-init", help="Bind this project to an existing registered Advisor"
    )
    brain_init.add_argument("--project-root", type=Path, default=Path("."))
    brain_init.add_argument("--advisor-id", required=True)

    brain_discover = commands.add_parser(
        "brain-discover", help="Discover the nearest project-local Project Brain"
    )
    brain_discover.add_argument("--project-root", type=Path, default=Path("."))

    brain_status = commands.add_parser(
        "brain-status", help="Validate Project Brain binding and live backend state"
    )
    brain_status.add_argument("--project-root", type=Path, default=Path("."))

    grounding_check = commands.add_parser(
        "brain-grounding-check",
        help="Check canonical project-source coverage and local freshness",
    )
    grounding_check.add_argument("--project-root", type=Path, default=Path("."))

    onboarding_plan = commands.add_parser(
        "brain-onboarding-plan",
        help="Generate a review-only plan of likely canonical project documents",
    )
    onboarding_plan.add_argument("--project-root", type=Path, default=Path("."))
    onboarding_plan.add_argument("--output-directory", type=Path)

    show = commands.add_parser("show", help="Show local Advisor state")
    show.add_argument("--advisor-id", required=True)

    source_capacity = commands.add_parser(
        "source-capacity", help="Show live backend source usage and effective limit"
    )
    source_capacity.add_argument("--advisor-id", required=True)
    source_capacity.add_argument("--planned-additions", type=int, default=0)

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
    source_add_file.add_argument(
        "--role",
        action="append",
        choices=tuple(sorted(SOURCE_ROLES)),
        default=[],
        help="Explicit source role; repeat for multiple roles",
    )
    source_add_file.add_argument(
        "--project-root",
        type=Path,
        help="Project root; otherwise discovered upward from --file when --role is used",
    )

    source_state = commands.add_parser("source-state", help="Pin or classify a registered source")
    source_state.add_argument("--advisor-id", required=True)
    source_state.add_argument("--local-id", required=True)
    source_state.add_argument("--state", choices=("active", "pinned", "broken"), required=True)

    ask = commands.add_parser("ask", help="Ask the source-grounded Advisor")
    ask.add_argument("--advisor-id", required=True)
    question = ask.add_mutually_exclusive_group(required=True)
    question.add_argument("--question")
    question.add_argument("--question-file", type=Path)
    conversation = ask.add_mutually_exclusive_group()
    conversation.add_argument(
        "--fresh",
        action="store_true",
        help="Delete any existing conversation on this notebook first, guaranteeing an independent turn",
    )
    conversation.add_argument(
        "--conversation-id",
        help="Continue this specific prior conversation instead of the server's default 'most recent' one",
    )

    preview = commands.add_parser("preview", help="Run resumable Deep Research preview")
    preview.add_argument("--advisor-id", required=True)
    preview.add_argument("--run-id", required=True)
    preview.add_argument("--work-directory", type=Path, required=True)
    preview.add_argument("--timeout", type=float, default=1800)
    preview.add_argument("--query", help="Ad-hoc research query overriding default profile queries")

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


async def run(args: argparse.Namespace, backend: NotebookBackend | None = None) -> int:
    store = AdvisorStore(args.state_root)
    backend = backend or GeminiNotebookBackend()
    service = EvergreenService(backend, store)

    if args.command == "setup":
        advisor_id, title, persona, research, watchlist = load_setup_document(args.config)
        try:
            result = await service.setup(
                advisor_id=advisor_id,
                title=title,
                persona=persona,
                research=research,
                watchlist=watchlist,
                notebook_id=args.adopt_notebook_id,
            )
        except FileExistsError as exc:
            raise SystemExit(
                f"Error: Advisor already exists: {advisor_id!r}\n"
                f"Hint: Use 'show --advisor-id {advisor_id}' to inspect it, "
                f"or 'update-config --config <file>' to update its configuration."
            ) from exc
        _print(
            {
                "advisor_id": advisor_id,
                "notebook_id": result.notebook.notebook_id,
                "persona_verified": True,
            }
        )
    elif args.command == "list-advisors":
        advisors = store.list_advisors()
        if args.json:
            _print({"advisors": [a.to_dict() for a in advisors], "count": len(advisors)})
        else:
            if not advisors:
                print("No registered Advisors found.")
            else:
                print(f"Found {len(advisors)} registered Advisor(s):")
                print(f"{'ID':<28} {'TITLE':<32} {'RESEARCH':<10} {'SOURCES':<8} {'NOTEBOOK ID'}")
                print("-" * 110)
                for a in advisors:
                    res_status = "enabled" if a.research_enabled else "disabled"
                    print(f"{a.advisor_id:<28} {a.title[:30]:<32} {res_status:<10} {a.source_count:<8} {a.notebook_id}")
    elif args.command == "update-config":
        advisor_id, title, persona, research, watchlist = load_update_document(args.config)
        updated = await service.update_advisor(
            advisor_id=advisor_id,
            title=title,
            persona=persona,
            research=research,
            watchlist=watchlist,
        )
        _print(
            {
                "advisor_id": updated.advisor_id,
                "title": updated.title,
                "updated": True,
                "research_enabled": updated.research.enabled,
            }
        )
    elif args.command == "brain-install-plan":
        target = resolve_install_target(args.project_root, args.client)
        _print(build_install_plan(target).to_dict())
    elif args.command == "brain-install":
        target = resolve_install_target(args.project_root, args.client)
        plan = build_install_plan(target)
        _print(apply_install_plan(plan, confirm=args.confirm))
    elif args.command == "brain-doctor":
        target = resolve_install_target(args.project_root, args.client)
        _print(await diagnose_project_brain(target, backend, store))
    elif args.command == "brain-uninstall":
        target = resolve_install_target(args.project_root, args.client)
        _print(uninstall_project_integration(target, confirm=args.confirm))
    elif args.command == "brain-init":
        profile, _, _ = store.load(args.advisor_id)
        notebook = await backend.get_notebook(profile.backend.notebook_id)
        if notebook.notebook_id != profile.backend.notebook_id:
            raise RuntimeError("Backend returned a different Notebook ID during binding")
        path = bind_project(args.project_root, profile)
        _print(
            {
                "status": "bound",
                "project_root": str(args.project_root.resolve()),
                "manifest_path": str(path),
                "advisor_id": profile.advisor_id,
                "notebook_id": profile.backend.notebook_id,
            }
        )
    elif args.command == "brain-discover":
        project_root, path, manifest = discover_project_brain(args.project_root)
        _print(
            {
                "configured": True,
                "project_root": str(project_root),
                "manifest_path": str(path),
                "manifest": manifest.to_dict(),
            }
        )
    elif args.command == "brain-status":
        project_root, path, manifest = discover_project_brain(args.project_root)
        profile, _, sources = store.load(manifest.advisor_id)
        if (
            profile.backend.type != manifest.backend_type
            or profile.backend.notebook_id != manifest.notebook_id
        ):
            raise RuntimeError("Project Brain manifest and local Advisor state disagree")
        notebook = await backend.get_notebook(manifest.notebook_id)
        capacity = await service.source_capacity(manifest.advisor_id)
        registry_count = sum(source.state != "deleted" for source in sources)
        grounding = assess_project_grounding(manifest, sources, project_root)
        _print(
            {
                "configured": True,
                "project_root": str(project_root),
                "manifest_path": str(path),
                "advisor_id": manifest.advisor_id,
                "notebook_id": manifest.notebook_id,
                "notebook_title": notebook.title,
                "grounding": grounding.to_dict(),
                "registry_source_count": registry_count,
                "backend_source_count": capacity.used,
                "registry_backend_drift": registry_count != capacity.used,
                "source_capacity": capacity.to_dict(),
            }
        )
    elif args.command == "brain-grounding-check":
        project_root, path, manifest = discover_project_brain(args.project_root)
        _, _, sources = store.load(manifest.advisor_id)
        grounding = assess_project_grounding(manifest, sources, project_root)
        _print(
            {
                "project_root": str(project_root),
                "manifest_path": str(path),
                "advisor_id": manifest.advisor_id,
                "grounding": grounding.to_dict(),
            }
        )
    elif args.command == "brain-onboarding-plan":
        project_root, _, manifest = discover_project_brain(args.project_root)
        _, _, sources = store.load(manifest.advisor_id)
        grounding = assess_project_grounding(manifest, sources, project_root)
        plan = build_onboarding_plan(project_root, manifest, grounding)
        output_directory = args.output_directory or (
            project_root / ".notebooklm" / "plans"
        )
        json_path, markdown_path = write_onboarding_plan(plan, output_directory)
        _print(
            {
                "status": "awaiting_review",
                "plan_digest": plan.digest,
                "candidate_count": len(plan.candidates),
                "missing_roles": list(plan.missing_roles),
                "json_path": str(json_path),
                "markdown_path": str(markdown_path),
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
                        "roles": list(source.roles),
                        "project_path": source.project_path,
                        "content_sha256": source.content_sha256,
                        "git_commit": source.git_commit,
                    }
                    for source in sources
                ],
                "refresh_runs": len(runs),
            }
        )
    elif args.command == "source-capacity":
        capacity = await service.source_capacity(
            args.advisor_id,
            planned_additions=args.planned_additions,
        )
        _print({"advisor_id": args.advisor_id, "source_capacity": capacity.to_dict()})
    elif args.command == "source-add-url":
        source = await service.add_url_source(
            advisor_id=args.advisor_id,
            url=args.url,
            state=args.state,
        )
        capacity = await service.source_capacity(args.advisor_id)
        _print({**source.to_dict(), "source_capacity": capacity.to_dict()})
    elif args.command == "source-add-file":
        if not args.file.is_file():
            raise SystemExit(f"File not found: {args.file}")
        content = args.file.read_text(encoding="utf-8")
        title = args.title or args.file.name
        project_path = None
        git_commit = None
        if args.role or args.project_root is not None:
            discovery_start = args.project_root or args.file.parent
            project_root, _, manifest = discover_project_brain(discovery_start)
            if manifest.advisor_id != args.advisor_id:
                raise RuntimeError(
                    "Project Brain manifest is bound to a different Advisor: "
                    f"{manifest.advisor_id}"
                )
            resolved_file = args.file.resolve()
            if not resolved_file.is_relative_to(project_root):
                raise ValueError("Canonical project source must be inside project root")
            project_path = resolved_file.relative_to(project_root).as_posix()
            git_commit = current_git_commit(project_root)
        source = await service.add_text_source(
            advisor_id=args.advisor_id,
            title=title,
            content=content,
            state=args.state,
            roles=tuple(args.role),
            project_path=project_path,
            git_commit=git_commit,
        )
        capacity = await service.source_capacity(args.advisor_id)
        _print({**source.to_dict(), "source_capacity": capacity.to_dict()})
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
        ask_res = await service.ask(
            args.advisor_id,
            question,
            conversation_id=args.conversation_id,
            fresh=args.fresh,
        )
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
            query=args.query,
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
        capacity = await service.source_capacity(args.advisor_id)
        _print({**result.to_dict(), "source_capacity": capacity.to_dict()})
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
