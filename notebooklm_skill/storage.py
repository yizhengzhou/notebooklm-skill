"""Atomic local persistence for Evergreen Advisor state."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

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
    _validate_id,
)
from notebooklm_skill.paths import advisors_root

_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path.parent, 0o700)
    key = str(path.resolve())
    with _LOCKS_GUARD:
        thread_lock = _LOCKS.setdefault(key, threading.Lock())
    with thread_lock:
        with path.open("a+b") as handle:
            if os.name != "nt":
                os.chmod(path, 0o600)
            if os.name == "nt":
                import msvcrt

                if path.stat().st_size == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        if os.name != "nt":
            os.chmod(temporary_path, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        if os.name != "nt":
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _write_json(path: Path, data: dict[str, Any]) -> None:
    content = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
    _atomic_write(path, content)


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


def _profile_document(profile: AdvisorProfile) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "advisor_id": profile.advisor_id,
        "title": profile.title,
        "backend": profile.backend.to_dict(),
        "persona": {
            "instructions_file": "persona.md",
            "response_length": profile.persona.response_length,
        },
        "research": profile.research.to_dict(),
        "schedule": profile.schedule.to_dict(),
    }


def _load_profile(directory: Path) -> AdvisorProfile:
    data = _read_json(directory / "profile.json")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported profile schema: {data.get('schema_version')!r}")
    persona_data = data["persona"]
    if persona_data.get("instructions_file") != "persona.md":
        raise ValueError("Unsupported persona instructions file")
    instructions = (directory / "persona.md").read_text(encoding="utf-8").strip()
    return AdvisorProfile(
        advisor_id=str(data["advisor_id"]),
        title=str(data["title"]),
        backend=BackendRef.from_dict(data["backend"]),
        persona=PersonaProfile(
            instructions=instructions,
            response_length=persona_data["response_length"],
        ),
        research=ResearchProfile.from_dict(data["research"]),
        schedule=ScheduleProfile.from_dict(data["schedule"]),
    )


def _watchlist_document(items: tuple[WatchItem, ...]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "items": [item.to_dict() for item in items]}


def _sources_document(items: tuple[SourceRecord, ...]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "items": [item.to_dict() for item in items]}


class AdvisorStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else advisors_root()

    def advisor_directory(self, advisor_id: str) -> Path:
        _validate_id(advisor_id, "advisor_id")
        return self.root / advisor_id

    def _lock_path(self, advisor_id: str) -> Path:
        return self.root / f".{advisor_id}.lock"

    def create(
        self,
        profile: AdvisorProfile,
        *,
        watchlist: tuple[WatchItem, ...] = (),
        sources: tuple[SourceRecord, ...] = (),
    ) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        destination = self.advisor_directory(profile.advisor_id)
        with _file_lock(self._lock_path(profile.advisor_id)):
            if destination.exists():
                raise FileExistsError(f"Advisor already exists: {profile.advisor_id}")
            temporary = Path(tempfile.mkdtemp(prefix=f".{profile.advisor_id}.", dir=self.root))
            try:
                self._write_profile_files(temporary, profile)
                _write_json(temporary / "watchlist.json", _watchlist_document(watchlist))
                _write_json(temporary / "sources.json", _sources_document(sources))
                (temporary / "refresh-runs").mkdir()
                os.replace(temporary, destination)
            except Exception:
                shutil.rmtree(temporary, ignore_errors=True)
                raise
        return destination

    def save_profile(self, profile: AdvisorProfile) -> None:
        directory = self.advisor_directory(profile.advisor_id)
        with _file_lock(self._lock_path(profile.advisor_id)):
            self._require_existing(directory)
            self._write_profile_files(directory, profile)

    def save_watchlist(self, advisor_id: str, items: tuple[WatchItem, ...]) -> None:
        directory = self.advisor_directory(advisor_id)
        with _file_lock(self._lock_path(advisor_id)):
            self._require_existing(directory)
            _write_json(directory / "watchlist.json", _watchlist_document(items))

    def save_sources(self, advisor_id: str, items: tuple[SourceRecord, ...]) -> None:
        directory = self.advisor_directory(advisor_id)
        with _file_lock(self._lock_path(advisor_id)):
            self._require_existing(directory)
            _write_json(directory / "sources.json", _sources_document(items))

    def save_refresh_run(self, run: RefreshRun) -> None:
        directory = self.advisor_directory(run.advisor_id)
        with _file_lock(self._lock_path(run.advisor_id)):
            self._require_existing(directory)
            path = directory / "refresh-runs" / f"{run.run_id}.json"
            if path.exists():
                raise FileExistsError(f"Refresh run is immutable: {run.run_id}")
            _write_json(path, run.to_dict())

    def commit_refresh(
        self,
        advisor_id: str,
        *,
        sources: tuple[SourceRecord, ...],
        run: RefreshRun,
    ) -> None:
        if run.advisor_id != advisor_id:
            raise ValueError("Refresh run belongs to a different Advisor")
        directory = self.advisor_directory(advisor_id)
        with _file_lock(self._lock_path(advisor_id)):
            self._require_existing(directory)
            run_path = directory / "refresh-runs" / f"{run.run_id}.json"
            if run_path.exists():
                raise FileExistsError(f"Refresh run is immutable: {run.run_id}")
            _write_json(directory / "sources.json", _sources_document(sources))
            _write_json(run_path, run.to_dict())

    def load(
        self, advisor_id: str
    ) -> tuple[AdvisorProfile, tuple[WatchItem, ...], tuple[SourceRecord, ...]]:
        profile, watchlist, sources, _ = self.load_snapshot(advisor_id)
        return profile, watchlist, sources

    def load_refresh_runs(self, advisor_id: str) -> tuple[RefreshRun, ...]:
        return self.load_snapshot(advisor_id)[3]

    def load_snapshot(
        self, advisor_id: str
    ) -> tuple[
        AdvisorProfile,
        tuple[WatchItem, ...],
        tuple[SourceRecord, ...],
        tuple[RefreshRun, ...],
    ]:
        directory = self.advisor_directory(advisor_id)
        with _file_lock(self._lock_path(advisor_id)):
            self._require_existing(directory)
            profile = _load_profile(directory)
            watch_data = _read_json(directory / "watchlist.json")
            source_data = _read_json(directory / "sources.json")
            run_documents = [
                _read_json(path) for path in sorted((directory / "refresh-runs").glob("*.json"))
            ]
        self._require_schema(watch_data)
        self._require_schema(source_data)
        return (
            profile,
            tuple(WatchItem.from_dict(item) for item in watch_data["items"]),
            tuple(SourceRecord.from_dict(item) for item in source_data["items"]),
            tuple(RefreshRun.from_dict(document) for document in run_documents),
        )

    @staticmethod
    def _write_profile_files(directory: Path, profile: AdvisorProfile) -> None:
        _write_json(directory / "profile.json", _profile_document(profile))
        _atomic_write(directory / "persona.md", (profile.persona.instructions.strip() + "\n").encode())

    @staticmethod
    def _require_existing(directory: Path) -> None:
        if not (directory / "profile.json").is_file():
            raise FileNotFoundError(f"Advisor does not exist: {directory.name}")

    @staticmethod
    def _require_schema(data: dict[str, Any]) -> None:
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version: {data.get('schema_version')!r}")
