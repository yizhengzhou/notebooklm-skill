import asyncio
import json
from pathlib import Path

import pytest

from notebooklm_skill.backend import SourceSnapshot
from notebooklm_skill.cli import build_parser, run
from notebooklm_skill.evergreen import load_setup_document
from notebooklm_skill.storage import AdvisorStore
from tests.fake_backend import FakeNotebook, FakeNotebookBackend
from tests.sample_data import sample_profile, sample_sources, sample_watchlist


def test_cli_exposes_complete_manual_evergreen_workflow() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    for command in (
        "setup",
        "show",
        "brain-install-plan",
        "brain-install",
        "brain-doctor",
        "brain-uninstall",
        "brain-init",
        "brain-discover",
        "brain-status",
        "brain-grounding-check",
        "brain-onboarding-plan",
        "source-capacity",
        "source-add-url",
        "source-add-file",
        "source-state",
        "ask",
        "preview",
        "plan-apply",
        "apply",
        "refresh-plan",
        "refresh-apply",
        "export",
        "list-advisors",
        "update-config",
    ):
        assert command in help_text


def test_source_add_url_parser_accepts_pinned_seed() -> None:
    args = build_parser().parse_args(
        [
            "source-add-url",
            "--advisor-id",
            "gauntlet-lab",
            "--url",
            "https://github.com/robonuggets/gauntlet-loop",
            "--state",
            "pinned",
        ]
    )

    assert args.command == "source-add-url"
    assert args.state == "pinned"


def test_source_add_file_parser_defaults_title_to_file_name(tmp_path: Path) -> None:
    local_file = tmp_path / "ARCHITECTURE.md"
    args = build_parser().parse_args(
        [
            "source-add-file",
            "--advisor-id",
            "verifyai",
            "--file",
            str(local_file),
            "--state",
            "pinned",
        ]
    )

    assert args.command == "source-add-file"
    assert args.file == local_file
    assert args.title is None
    assert args.state == "pinned"


def test_ask_parser_accepts_question_file(tmp_path: Path) -> None:
    question = tmp_path / "question.md"
    question.write_text("What should we test?", encoding="utf-8")
    args = build_parser().parse_args(
        [
            "ask",
            "--advisor-id",
            "gauntlet-lab",
            "--question-file",
            str(question),
        ]
    )

    assert args.command == "ask"
    assert args.question_file == question
    assert args.fresh is False
    assert args.conversation_id is None


def test_ask_parser_accepts_fresh_flag() -> None:
    args = build_parser().parse_args(
        ["ask", "--advisor-id", "gauntlet-lab", "--question", "Q", "--fresh"]
    )

    assert args.fresh is True
    assert args.conversation_id is None


def test_ask_parser_accepts_conversation_id() -> None:
    args = build_parser().parse_args(
        [
            "ask",
            "--advisor-id",
            "gauntlet-lab",
            "--question",
            "Q",
            "--conversation-id",
            "conv-123",
        ]
    )

    assert args.fresh is False
    assert args.conversation_id == "conv-123"


def test_ask_parser_rejects_fresh_with_conversation_id() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "ask",
                "--advisor-id",
                "gauntlet-lab",
                "--question",
                "Q",
                "--fresh",
                "--conversation-id",
                "conv-123",
            ]
        )


def test_setup_document_loads_cross_domain_profile(tmp_path: Path) -> None:
    path = tmp_path / "advisor.json"
    path.write_text(
        json.dumps(
            {
                "advisor_id": "market-watch",
                "title": "Market Watch",
                "persona": {
                    "instructions": "Act as a cross-domain evidence advisor.",
                    "response_length": "longer",
                },
                "research": {
                    "brief": "Track market changes.",
                    "queries": ["What changed?"],
                    "mode": "deep",
                    "language": "zh-Hant",
                    "recency_days": 90,
                    "max_new_sources_per_run": 5,
                    "preferred_domains": ["example.com"],
                    "update_mode": "review",
                    "deletion_mode": "confirm",
                    "enabled": True,
                },
                "watchlist": [
                    {
                        "watch_id": "watch-market",
                        "kind": "trend",
                        "statement": "Market conditions may change.",
                    }
                ],
            }
        )
    )

    advisor_id, title, persona, research, watchlist = load_setup_document(path)

    assert advisor_id == "market-watch"
    assert title == "Market Watch"
    assert persona.response_length == "longer"
    assert research.queries == ("What changed?",)
    assert watchlist[0].kind == "trend"


def test_show_command_reads_local_state_without_backend_access(
    tmp_path: Path, capsys
) -> None:
    root = tmp_path / "advisors"
    store = AdvisorStore(root)
    profile = sample_profile()
    store.create(profile, watchlist=sample_watchlist(), sources=sample_sources())
    args = build_parser().parse_args(
        ["--state-root", str(root), "show", "--advisor-id", profile.advisor_id]
    )

    assert asyncio.run(run(args)) == 0

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "advisor_id": profile.advisor_id,
        "title": profile.title,
        "backend": profile.backend.to_dict(),
        "watch_items": 1,
        "source_count": 1,
        "sources": [
            {
                "local_id": "src-001",
                "title": "Canonical source",
                "state": "pinned",
                "backend_source_id": "backend-source-1",
                "roles": [],
                "project_path": None,
                "content_sha256": None,
                "git_commit": None,
            }
        ],
        "refresh_runs": 0,
    }


def test_list_advisors_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "advisors"
    store = AdvisorStore(root)
    profile = sample_profile()
    store.create(profile)

    # Test JSON mode
    args_json = build_parser().parse_args(["--state-root", str(root), "list-advisors", "--json"])
    assert asyncio.run(run(args_json)) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["count"] == 1
    assert data["advisors"][0]["advisor_id"] == profile.advisor_id

    # Test Table mode
    args_table = build_parser().parse_args(["--state-root", str(root), "list-advisors"])
    assert asyncio.run(run(args_table)) == 0
    text = capsys.readouterr().out
    assert profile.advisor_id in text
    assert profile.title in text


def test_preview_parser_accepts_ad_hoc_query() -> None:
    args = build_parser().parse_args(
        [
            "preview",
            "--advisor-id",
            "market-watch",
            "--run-id",
            "preview-01",
            "--work-directory",
            "./runs/preview-01",
            "--query",
            "specific custom research topic",
        ]
    )
    assert args.command == "preview"
    assert args.query == "specific custom research topic"


def test_setup_collision_shows_hint(tmp_path: Path) -> None:
    root = tmp_path / "advisors"
    store = AdvisorStore(root)
    profile = sample_profile()
    store.create(profile)

    config_path = tmp_path / "advisor.json"
    config_path.write_text(
        json.dumps(
            {
                "advisor_id": profile.advisor_id,
                "title": profile.title,
                "persona": {"instructions": "Instructions"},
                "research": {"enabled": False},
            }
        ),
        encoding="utf-8",
    )

    args = build_parser().parse_args(
        ["--state-root", str(root), "setup", "--config", str(config_path)]
    )

    with pytest.raises(SystemExit) as exc_info:
        asyncio.run(run(args))
    assert "Advisor already exists" in str(exc_info.value)
    assert "Hint:" in str(exc_info.value)


def test_update_config_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "advisors"
    store = AdvisorStore(root)
    profile = sample_profile()
    store.create(profile)

    fake_backend = FakeNotebookBackend()
    fake_backend.notebooks[profile.backend.notebook_id] = FakeNotebook(
        notebook_id=profile.backend.notebook_id,
        title=profile.title,
    )

    config_path = tmp_path / "updated_advisor.json"
    config_path.write_text(
        json.dumps(
            {
                "advisor_id": profile.advisor_id,
                "title": "Updated Title",
                "persona": {"instructions": "Updated Persona"},
                "research": {"enabled": False},
            }
        ),
        encoding="utf-8",
    )

    args = build_parser().parse_args(
        ["--state-root", str(root), "update-config", "--config", str(config_path)]
    )
    assert asyncio.run(run(args, backend=fake_backend)) == 0

    updated_profile, _, _ = store.load(profile.advisor_id)
    assert updated_profile.title == "Updated Title"
    assert updated_profile.persona.instructions == "Updated Persona"
    assert updated_profile.research.enabled is False
    assert fake_backend.notebooks[profile.backend.notebook_id].persona == "Updated Persona"


def test_update_config_cli_preserves_unspecified_research_and_watchlist(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "advisors"
    store = AdvisorStore(root)
    profile = sample_profile()
    watchlist = sample_watchlist()
    store.create(profile, watchlist=watchlist)

    fake_backend = FakeNotebookBackend()
    fake_backend.notebooks[profile.backend.notebook_id] = FakeNotebook(
        notebook_id=profile.backend.notebook_id,
        title=profile.title,
    )

    # Config omits title, research, and watchlist — only updates persona
    config_path = tmp_path / "partial_update.json"
    config_path.write_text(
        json.dumps(
            {
                "advisor_id": profile.advisor_id,
                "persona": {"instructions": "Updated Persona Without Touching Research"},
            }
        ),
        encoding="utf-8",
    )

    args = build_parser().parse_args(
        ["--state-root", str(root), "update-config", "--config", str(config_path)]
    )
    assert asyncio.run(run(args, backend=fake_backend)) == 0

    updated_profile, updated_watchlist, _ = store.load(profile.advisor_id)
    # Persona updated
    assert updated_profile.persona.instructions == "Updated Persona Without Touching Research"
    # Title preserved
    assert updated_profile.title == profile.title
    # Research preserved exactly as original (enabled=True, original brief/queries)
    assert updated_profile.research.enabled == profile.research.enabled
    assert updated_profile.research.brief == profile.research.brief
    assert updated_profile.research.queries == profile.research.queries
    # Watchlist NOT wiped
    assert len(updated_watchlist) == len(watchlist)
    assert updated_watchlist[0].watch_id == watchlist[0].watch_id


def test_brain_init_discover_and_status_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "advisors"
    project = tmp_path / "project"
    nested = project / "src"
    nested.mkdir(parents=True)
    store = AdvisorStore(root)
    profile = sample_profile(advisor_id="project-brain")
    store.create(profile, sources=sample_sources())

    backend = FakeNotebookBackend()
    backend.notebooks[profile.backend.notebook_id] = FakeNotebook(
        notebook_id=profile.backend.notebook_id,
        title=profile.title,
    )
    # Deliberately use one backend row to prove drift is visible.
    backend.sources[profile.backend.notebook_id] = (
        SourceSnapshot(source_id="backend-only-1", title="Backend only 1"),
        SourceSnapshot(source_id="backend-only-2", title="Backend only 2"),
    )

    init_args = build_parser().parse_args(
        [
            "--state-root",
            str(root),
            "brain-init",
            "--project-root",
            str(project),
            "--advisor-id",
            profile.advisor_id,
        ]
    )
    assert asyncio.run(run(init_args, backend=backend)) == 0
    init_output = json.loads(capsys.readouterr().out)
    assert init_output["status"] == "bound"

    discover_args = build_parser().parse_args(
        ["brain-discover", "--project-root", str(nested)]
    )
    assert asyncio.run(run(discover_args, backend=backend)) == 0
    discover_output = json.loads(capsys.readouterr().out)
    assert discover_output["manifest"]["advisor_id"] == profile.advisor_id

    status_args = build_parser().parse_args(
        ["--state-root", str(root), "brain-status", "--project-root", str(nested)]
    )
    assert asyncio.run(run(status_args, backend=backend)) == 0
    status_output = json.loads(capsys.readouterr().out)
    assert status_output["grounding"]["status"] == "unknown"
    assert status_output["registry_source_count"] == len(sample_sources())
    assert status_output["backend_source_count"] == 2
    assert status_output["registry_backend_drift"] is True


def test_project_source_roles_drive_grounding_ready_and_stale(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "advisors"
    project = tmp_path / "project"
    docs = project / "docs"
    docs.mkdir(parents=True)
    files = {
        "README.md": ("project_overview", "overview"),
        "docs/architecture.md": ("architecture", "architecture"),
        "docs/current-status.md": ("current_status", "status"),
        "docs/decisions.md": ("decisions", "decisions"),
    }
    for relative, (_, content) in files.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    store = AdvisorStore(root)
    profile = sample_profile(advisor_id="project-brain")
    store.create(profile)
    backend = FakeNotebookBackend()
    backend.notebooks[profile.backend.notebook_id] = FakeNotebook(
        notebook_id=profile.backend.notebook_id,
        title=profile.title,
    )
    backend.sources[profile.backend.notebook_id] = ()

    init_args = build_parser().parse_args(
        [
            "--state-root",
            str(root),
            "brain-init",
            "--project-root",
            str(project),
            "--advisor-id",
            profile.advisor_id,
        ]
    )
    asyncio.run(run(init_args, backend=backend))
    capsys.readouterr()

    for relative, (role, _) in files.items():
        add_args = build_parser().parse_args(
            [
                "--state-root",
                str(root),
                "source-add-file",
                "--advisor-id",
                profile.advisor_id,
                "--file",
                str(project / relative),
                "--role",
                role,
            ]
        )
        assert asyncio.run(run(add_args, backend=backend)) == 0
        capsys.readouterr()

    check_args = build_parser().parse_args(
        [
            "--state-root",
            str(root),
            "brain-grounding-check",
            "--project-root",
            str(docs),
        ]
    )
    assert asyncio.run(run(check_args, backend=backend)) == 0
    ready = json.loads(capsys.readouterr().out)
    assert ready["grounding"]["status"] == "project_ready"
    assert ready["grounding"]["can_explain_project"] is True

    (docs / "current-status.md").write_text("changed", encoding="utf-8")
    assert asyncio.run(run(check_args, backend=backend)) == 0
    stale = json.loads(capsys.readouterr().out)
    assert stale["grounding"]["status"] == "project_stale"
    assert stale["grounding"]["stale_roles"] == ["current_status"]


def test_brain_onboarding_plan_cli_writes_review_only_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "advisors"
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("overview", encoding="utf-8")
    store = AdvisorStore(root)
    profile = sample_profile(advisor_id="project-brain")
    store.create(profile)
    backend = FakeNotebookBackend()
    backend.notebooks[profile.backend.notebook_id] = FakeNotebook(
        notebook_id=profile.backend.notebook_id,
        title=profile.title,
    )
    backend.sources[profile.backend.notebook_id] = ()

    init_args = build_parser().parse_args(
        [
            "--state-root",
            str(root),
            "brain-init",
            "--project-root",
            str(project),
            "--advisor-id",
            profile.advisor_id,
        ]
    )
    asyncio.run(run(init_args, backend=backend))
    capsys.readouterr()

    plan_args = build_parser().parse_args(
        [
            "--state-root",
            str(root),
            "brain-onboarding-plan",
            "--project-root",
            str(project),
        ]
    )
    assert asyncio.run(run(plan_args, backend=backend)) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "awaiting_review"
    assert output["candidate_count"] == 1
    assert Path(output["json_path"]).is_file()
    assert Path(output["markdown_path"]).is_file()


def test_source_capacity_cli_reports_planned_peak(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "advisors"
    store = AdvisorStore(root)
    profile = sample_profile()
    store.create(profile)
    backend = FakeNotebookBackend()
    backend.sources[profile.backend.notebook_id] = ()
    backend.source_limit = 10

    args = build_parser().parse_args(
        [
            "--state-root",
            str(root),
            "source-capacity",
            "--advisor-id",
            profile.advisor_id,
            "--planned-additions",
            "3",
        ]
    )
    assert asyncio.run(run(args, backend=backend)) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["source_capacity"]["limit"] == 10
    assert output["source_capacity"]["peak_used"] == 3
