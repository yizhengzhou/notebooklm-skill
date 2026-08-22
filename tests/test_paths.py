from pathlib import Path

from notebooklm_skill.paths import advisors_root, app_data_root


def test_platform_default_paths() -> None:
    home = Path("/Users/example")
    assert app_data_root(platform="darwin", home=home, environ={}) == (
        home / "Library" / "Application Support" / "notebooklm-skill"
    )
    assert app_data_root(platform="linux", home=home, environ={}) == (
        home / ".local" / "share" / "notebooklm-skill"
    )
    assert app_data_root(
        platform="win32",
        home=home,
        environ={"LOCALAPPDATA": "C:/Users/example/AppData/Local"},
    ) == Path("C:/Users/example/AppData/Local/notebooklm-skill")


def test_home_override_wins_and_advisors_are_nested() -> None:
    assert advisors_root(
        platform="darwin",
        home=Path("/ignored"),
        environ={"NOTEBOOKLM_SKILL_HOME": "/custom/state"},
    ) == Path("/custom/state/advisors")
