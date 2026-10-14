import asyncio
from pathlib import Path

import pytest

from notebooklm_skill.capacity import (
    SourceAddNotCommittedError,
    SourceCapacityExceededError,
    inspect_source_capacity,
)
from notebooklm_skill.evergreen import EvergreenService
from notebooklm_skill.storage import AdvisorStore
from notebooklm_skill.backend import SourceSnapshot
from tests.fake_backend import FakeNotebookBackend
from tests.sample_data import sample_profile


def _service(tmp_path: Path, backend: FakeNotebookBackend) -> tuple[EvergreenService, str]:
    profile = sample_profile()
    store = AdvisorStore(tmp_path / "advisors")
    store.create(profile)
    backend.sources[profile.backend.notebook_id] = ()
    return EvergreenService(backend, store), profile.advisor_id


def test_source_capacity_uses_live_limit_and_counts_all_backend_rows() -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Capacity")
        backend.source_limit = 10
        backend.tier = 4
        backend.sources[notebook.notebook_id] = tuple(
            SourceSnapshot(
                source_id=f"source-{index}",
                title=f"Source {index}",
                status="preparing" if index == 1 else "ready",
            )
            for index in range(1, 9)
        )

        capacity = await inspect_source_capacity(backend, notebook.notebook_id)

        assert capacity.used == 8
        assert capacity.limit == 10
        assert capacity.remaining == 2
        assert capacity.status == "warning"
        assert capacity.limit_source == "live_server"
        assert capacity.tier == 4
        assert capacity.preparing_orphans == 1

    asyncio.run(scenario())


def test_source_capacity_falls_back_to_standard_limit_not_unlimited() -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Fallback")
        backend.fail_account_limits = True

        capacity = await inspect_source_capacity(
            backend,
            notebook.notebook_id,
            planned_additions=1,
        )

        assert capacity.limit == 50
        assert capacity.limit_source == "official_standard_fallback"
        assert capacity.peak_used == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("kind", ["url", "text"])
def test_service_blocks_source_add_before_rpc_when_capacity_is_full(
    tmp_path: Path, kind: str
) -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        service, advisor_id = _service(tmp_path, backend)
        profile, _, _ = service.store.load(advisor_id)
        backend.source_limit = 1
        backend.sources[profile.backend.notebook_id] = (
            SourceSnapshot(source_id="existing", title="Existing"),
        )

        with pytest.raises(SourceCapacityExceededError) as exc_info:
            if kind == "url":
                await service.add_url_source(
                    advisor_id=advisor_id,
                    url="https://example.com/new",
                )
            else:
                await service.add_text_source(
                    advisor_id=advisor_id,
                    title="New",
                    content="New content",
                )

        assert exc_info.value.capacity.used == 1
        assert exc_info.value.capacity.limit == 1
        assert exc_info.value.capacity.status == "blocked_capacity"
        assert not any(event.startswith(("add_url:", "add_text:")) for event in backend.events)

    asyncio.run(scenario())


def test_service_rejects_apparent_add_when_backend_snapshot_has_no_source(
    tmp_path: Path,
) -> None:
    class NonCommittingBackend(FakeNotebookBackend):
        async def add_text_source(
            self, notebook_id: str, title: str, content: str
        ) -> SourceSnapshot:
            return SourceSnapshot(source_id="phantom", title=title, status="ready")

        async def wait_source_ready(self, notebook_id: str, source_id: str) -> SourceSnapshot:
            return SourceSnapshot(source_id=source_id, title="Phantom", status="ready")

    async def scenario() -> None:
        backend = NonCommittingBackend()
        service, advisor_id = _service(tmp_path, backend)

        with pytest.raises(SourceAddNotCommittedError, match="not committed exactly once"):
            await service.add_text_source(
                advisor_id=advisor_id,
                title="Phantom",
                content="This never reaches the backend list.",
            )

        _, _, registry = service.store.load(advisor_id)
        assert registry == ()

    asyncio.run(scenario())
