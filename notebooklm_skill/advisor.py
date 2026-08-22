"""Create or adopt a notebook and apply its persona as one user operation."""

from __future__ import annotations

from dataclasses import dataclass

from notebooklm_skill.backend import ChatConfig, NotebookBackend, NotebookRef, ResponseLength


class PersonaSetupError(RuntimeError):
    """Persona setup failed after the notebook identity became known."""

    def __init__(self, notebook_id: str, message: str) -> None:
        super().__init__(message)
        self.notebook_id = notebook_id


@dataclass(frozen=True)
class AdvisorSetup:
    notebook: NotebookRef
    chat_config: ChatConfig


class AdvisorService:
    def __init__(self, backend: NotebookBackend) -> None:
        self.backend = backend

    async def create(
        self,
        title: str,
        persona: str,
        response_length: ResponseLength = "default",
    ) -> AdvisorSetup:
        notebook = await self.backend.create_notebook(title)
        return await self._configure(notebook, persona, response_length)

    async def adopt(
        self,
        notebook_id: str,
        persona: str,
        response_length: ResponseLength = "default",
    ) -> AdvisorSetup:
        notebook = await self.backend.get_notebook(notebook_id)
        return await self._configure(notebook, persona, response_length)

    async def _configure(
        self,
        notebook: NotebookRef,
        persona: str,
        response_length: ResponseLength,
    ) -> AdvisorSetup:
        try:
            config = await self.backend.configure_chat(
                notebook.notebook_id,
                persona,
                response_length,
            )
        except Exception as exc:
            raise PersonaSetupError(
                notebook.notebook_id,
                f"Notebook exists, but persona setup failed: {exc}",
            ) from exc
        return AdvisorSetup(notebook=notebook, chat_config=config)
