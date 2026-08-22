"""Portable JSON + Markdown export bundles for Evergreen Advisors."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from notebooklm_skill.models import (
    SCHEMA_VERSION,
    AdvisorProfile,
    BackendRef,
    PersonaProfile,
    RefreshRun,
    ResearchProfile,
    ScheduleProfile,
    SourceRecord,
    WatchItem,
)
from notebooklm_skill.storage import AdvisorStore, _atomic_write, _read_json, _write_json

EXPORT_VERSION = 1
_FORBIDDEN_KEYS = {
    "access_token",
    "auth_json",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "master_token",
    "password",
    "refresh_token",
    "storage_path",
    "token",
}


@dataclass(frozen=True)
class ExportBundle:
    profile: AdvisorProfile
    watchlist: tuple[WatchItem, ...]
    sources: tuple[SourceRecord, ...]
    refresh_runs: tuple[RefreshRun, ...]


def _assert_no_credential_keys(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in _FORBIDDEN_KEYS:
                raise ValueError(f"Credential-like key is forbidden in export: {path}.{key}")
            _assert_no_credential_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_credential_keys(child, f"{path}[{index}]")


def export_bundle(store: AdvisorStore, advisor_id: str, destination: Path) -> Path:
    profile, watchlist, sources, runs = store.load_snapshot(advisor_id)
    destination = destination.expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Export destination already exists: {destination}")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "export_version": EXPORT_VERSION,
        "advisor_id": profile.advisor_id,
        "title": profile.title,
        "backend": profile.backend.to_dict(),
        "persona": {
            "instructions_file": "persona.md",
            "response_length": profile.persona.response_length,
        },
        "schedule": profile.schedule.to_dict(),
    }
    watch_document = {
        "schema_version": SCHEMA_VERSION,
        "items": [item.to_dict() for item in watchlist],
    }
    source_document = {
        "schema_version": SCHEMA_VERSION,
        "items": [item.to_dict() for item in sources],
    }
    for document in (manifest, profile.research.to_dict(), watch_document, source_document):
        _assert_no_credential_keys(document)
    for run in runs:
        _assert_no_credential_keys(run.to_dict())

    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        _write_json(temporary / "manifest.json", manifest)
        _atomic_write(
            temporary / "persona.md", (profile.persona.instructions.strip() + "\n").encode()
        )
        _write_json(temporary / "research-profile.json", profile.research.to_dict())
        _write_json(temporary / "watchlist.json", watch_document)
        _write_json(temporary / "sources.json", source_document)
        (temporary / "source-content").mkdir()
        run_directory = temporary / "refresh-runs"
        run_directory.mkdir()
        for run in runs:
            _write_json(run_directory / f"{run.run_id}.json", run.to_dict())
        _atomic_write(
            temporary / "README.md",
            (
                f"# {profile.title}\n\n"
                "Portable Evergreen Advisor export. Provider credentials are intentionally excluded.\n"
            ).encode(),
        )
        os.replace(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return destination


def read_export_bundle(directory: Path) -> ExportBundle:
    manifest = _read_json(directory / "manifest.json")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version: {manifest.get('schema_version')!r}")
    if manifest.get("export_version") != EXPORT_VERSION:
        raise ValueError(f"Unsupported export_version: {manifest.get('export_version')!r}")
    persona_data = manifest["persona"]
    if persona_data.get("instructions_file") != "persona.md":
        raise ValueError("Unsupported persona instructions file")

    research = ResearchProfile.from_dict(_read_json(directory / "research-profile.json"))
    watch_data = _read_json(directory / "watchlist.json")
    source_data = _read_json(directory / "sources.json")
    if watch_data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported watchlist schema")
    if source_data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported source schema")

    profile = AdvisorProfile(
        advisor_id=str(manifest["advisor_id"]),
        title=str(manifest["title"]),
        backend=BackendRef.from_dict(manifest["backend"]),
        persona=PersonaProfile(
            instructions=(directory / "persona.md").read_text(encoding="utf-8").strip(),
            response_length=persona_data["response_length"],
        ),
        research=research,
        schedule=ScheduleProfile.from_dict(manifest["schedule"]),
    )
    runs = tuple(
        RefreshRun.from_dict(_read_json(path))
        for path in sorted((directory / "refresh-runs").glob("*.json"))
    )
    bundle = ExportBundle(
        profile=profile,
        watchlist=tuple(WatchItem.from_dict(item) for item in watch_data["items"]),
        sources=tuple(SourceRecord.from_dict(item) for item in source_data["items"]),
        refresh_runs=runs,
    )
    for path in directory.rglob("*.json"):
        _assert_no_credential_keys(_read_json(path), path.name)
    return bundle
