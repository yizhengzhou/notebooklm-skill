"""Platform-aware paths for persistent Advisor state."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_HOME_ENV = "NOTEBOOKLM_SKILL_HOME"


def app_data_root(
    *,
    environ: dict[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Path:
    env = os.environ if environ is None else environ
    override = env.get(_HOME_ENV)
    if override:
        return Path(override).expanduser()

    current_platform = sys.platform if platform is None else platform
    user_home = Path.home() if home is None else home
    if current_platform == "darwin":
        return user_home / "Library" / "Application Support" / "notebooklm-skill"
    if current_platform == "win32":
        local_app_data = env.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "notebooklm-skill"
        return user_home / "AppData" / "Local" / "notebooklm-skill"

    xdg_data_home = env.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else user_home / ".local" / "share"
    return base / "notebooklm-skill"


def advisors_root(**kwargs: object) -> Path:
    return app_data_root(**kwargs) / "advisors"
