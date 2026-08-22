import asyncio

import pytest

from tests.fake_backend import FakeNotebookBackend


def test_fake_backend_rejects_unknown_response_length() -> None:
    async def scenario() -> None:
        backend = FakeNotebookBackend()
        notebook = await backend.create_notebook("Advisor")

        with pytest.raises(ValueError, match="Unsupported response length"):
            await backend.configure_chat(notebook.notebook_id, "Any persona", "verbose")

    asyncio.run(scenario())
