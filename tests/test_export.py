import json
from pathlib import Path

import pytest

from notebooklm_skill.export import export_bundle, read_export_bundle
from notebooklm_skill.storage import AdvisorStore
from tests.sample_data import sample_profile, sample_run, sample_sources, sample_watchlist


def test_export_bundle_round_trips_without_credentials(tmp_path: Path, monkeypatch) -> None:
    store = AdvisorStore(tmp_path / "state" / "advisors")
    profile = sample_profile()
    watchlist = sample_watchlist()
    sources = sample_sources()
    run = sample_run()
    store.create(profile, watchlist=watchlist, sources=sources)
    store.save_refresh_run(run)
    monkeypatch.setenv("NOTEBOOKLM_AUTH_JSON", "DO-NOT-EXPORT-THIS-SECRET")

    destination = export_bundle(store, profile.advisor_id, tmp_path / "portable-export")
    bundle = read_export_bundle(destination)

    assert bundle.profile == profile
    assert bundle.watchlist == watchlist
    assert bundle.sources == sources
    assert bundle.refresh_runs == (run,)
    assert "DO-NOT-EXPORT-THIS-SECRET" not in "".join(
        path.read_text(encoding="utf-8")
        for path in destination.rglob("*")
        if path.is_file()
    )
    assert (destination / "source-content").is_dir()


def test_export_refuses_to_overwrite_existing_destination(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "state" / "advisors")
    profile = sample_profile()
    store.create(profile)
    destination = tmp_path / "existing"
    destination.mkdir()

    with pytest.raises(FileExistsError):
        export_bundle(store, profile.advisor_id, destination)


def test_reader_rejects_injected_credential_key(tmp_path: Path) -> None:
    store = AdvisorStore(tmp_path / "state" / "advisors")
    profile = sample_profile()
    store.create(profile)
    destination = export_bundle(store, profile.advisor_id, tmp_path / "portable-export")
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["token"] = "secret"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="Credential-like key"):
        read_export_bundle(destination)
