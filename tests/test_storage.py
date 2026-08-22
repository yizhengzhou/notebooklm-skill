import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from notebooklm_skill.models import AdvisorProfile
from notebooklm_skill.storage import AdvisorStore
from tests.sample_data import sample_profile, sample_run, sample_sources, sample_watchlist


def test_advisor_state_round_trip_uses_only_injected_temp_root(tmp_path: Path) -> None:
    root = tmp_path / "state" / "advisors"
    store = AdvisorStore(root)
    profile = sample_profile()
    watchlist = sample_watchlist()
    sources = sample_sources()

    directory = store.create(profile, watchlist=watchlist, sources=sources)
    store.save_refresh_run(sample_run())

    assert directory.parent == root
    assert store.load(profile.advisor_id) == (profile, watchlist, sources)
    assert store.load_refresh_runs(profile.advisor_id) == (sample_run(),)
    assert (directory / "profile.json").is_file()
    assert (directory / "persona.md").is_file()


def test_store_rejects_path_traversal_advisor_id(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "advisors")

    with pytest.raises(ValueError, match="advisor_id"):
        store.advisor_directory("../escape")


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_state_directories_and_files_are_private(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "advisors")
    directory = store.create(sample_profile())

    assert store.root.stat().st_mode & 0o777 == 0o700
    assert directory.stat().st_mode & 0o777 == 0o700
    assert (directory / "profile.json").stat().st_mode & 0o777 == 0o600
    assert (directory / "persona.md").stat().st_mode & 0o777 == 0o600


def test_commit_refresh_updates_registry_and_writes_immutable_run(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "advisors")
    profile = sample_profile()
    store.create(profile)
    sources = sample_sources()
    run = sample_run()

    store.commit_refresh(profile.advisor_id, sources=sources, run=run)

    assert store.load(profile.advisor_id)[2] == sources
    assert store.load_refresh_runs(profile.advisor_id) == (run,)
    with pytest.raises(FileExistsError, match="immutable"):
        store.commit_refresh(profile.advisor_id, sources=(), run=run)
    assert store.load(profile.advisor_id)[2] == sources


def test_commit_refresh_rejects_cross_advisor_run(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "advisors")
    profile = sample_profile()
    store.create(profile)
    other = sample_run()
    other = type(other)(**{**other.__dict__, "advisor_id": "other-advisor"})

    with pytest.raises(ValueError, match="different Advisor"):
        store.commit_refresh(profile.advisor_id, sources=(), run=other)


def test_refresh_run_is_immutable(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "advisors")
    profile = sample_profile()
    store.create(profile)
    store.save_refresh_run(sample_run())

    with pytest.raises(FileExistsError, match="immutable"):
        store.save_refresh_run(sample_run())


def test_corrupt_schema_fails_closed(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "advisors")
    profile = sample_profile()
    directory = store.create(profile)
    profile_path = directory / "profile.json"
    data = json.loads(profile_path.read_text())
    data["schema_version"] = 999
    profile_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported profile schema"):
        store.load(profile.advisor_id)


def test_concurrent_profile_writes_remain_valid_json(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "advisors")
    original = sample_profile()
    store.create(original)

    def save(index: int) -> None:
        base = sample_profile(title=f"Advisor {index}")
        profile = AdvisorProfile(
            advisor_id=base.advisor_id,
            title=base.title,
            backend=base.backend,
            persona=base.persona,
            research=base.research,
            schedule=base.schedule,
        )
        store.save_profile(profile)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(save, range(24)))

    profile, _, _ = store.load(original.advisor_id)
    assert profile.title in {f"Advisor {index}" for index in range(24)}
    json.loads((store.advisor_directory(original.advisor_id) / "profile.json").read_text())
