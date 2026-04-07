"""Shared notebook naming validation logic.

Used by create_notebook.py, notebook_manager.py, and the PreToolUse hook
(scripts/validate_notebook_name.sh) to enforce consistent naming rules.
"""

import re

GENERIC_NAMES = frozenset({
    "test", "testing", "notebook", "untitled", "new", "temp", "tmp",
    "draft", "sample", "example", "筆記本", "新增", "測試", "未命名",
})

_PREFIX_RE = re.compile(r"^\[(?:Research|Project)\]\s*")


def validate_notebook_name(name: str) -> str:
    """Validate notebook name quality.

    Returns:
        Empty string if valid, error message string if invalid.
    """
    if not name or not name.strip():
        return "Notebook name cannot be empty"
    core_name = _PREFIX_RE.sub("", name.strip())
    if len(core_name) < 3:
        return f"Notebook name too short ({len(core_name)} chars, minimum 3): '{name.strip()}'"
    if core_name.lower() in GENERIC_NAMES:
        return f"Generic notebook name rejected: '{core_name}'. Use a descriptive name (e.g., project name, topic, purpose)"
    return ""
