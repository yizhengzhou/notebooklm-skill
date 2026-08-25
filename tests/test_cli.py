import asyncio
import json
from pathlib import Path

from notebooklm_skill.cli import build_parser, run
from notebooklm_skill.evergreen import load_setup_document
from notebooklm_skill.storage import AdvisorStore
from tests.sample_data import sample_profile, sample_sources, sample_watchlist


def test_cli_exposes_complete_manual_evergreen_workflow() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    for command in (
        "setup",
        "show",
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
            }
        ],
        "refresh_runs": 0,
    }
