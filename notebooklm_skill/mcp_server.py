"""Project Brain MCP server with project-local Notebook binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP

from notebooklm_skill.backend import NotebookBackend
from notebooklm_skill.evergreen import EvergreenService, format_answer_with_citations
from notebooklm_skill.gemini_backend import GeminiNotebookBackend
from notebooklm_skill.grounding import GroundingReport, assess_project_grounding
from notebooklm_skill.onboarding import build_onboarding_plan
from notebooklm_skill.project_brain import (
    ProjectBrainManifest,
    discover_project_brain,
)
from notebooklm_skill.storage import AdvisorStore

SERVER_INSTRUCTIONS = """
Use the nearest project-local .notebooklm/brain.json. Never guess a Notebook.
NotebookLM is advisory: local code, Git, tests, and runtime evidence remain authoritative.
For project explanations, require grounding.status=project_ready. research_only,
project_partial, project_stale, and unknown must fail closed and recommend onboarding.
These tools do not add, replace, delete, or generate Notebook content.
""".strip()


def create_project_brain_server(
    *,
    backend: NotebookBackend | None = None,
    state_root: Path | None = None,
) -> FastMCP:
    backend = backend or GeminiNotebookBackend()
    store = AdvisorStore(state_root)
    service = EvergreenService(backend, store)
    mcp = FastMCP(
        name="notebooklm-project-brain",
        instructions=SERVER_INSTRUCTIONS,
    )

    def load_context(
        project_path: str,
    ) -> tuple[Path, Path, ProjectBrainManifest, tuple[Any, ...]]:
        project_root, manifest_path, manifest = discover_project_brain(Path(project_path))
        profile, _, sources = store.load(manifest.advisor_id)
        if (
            profile.backend.type != manifest.backend_type
            or profile.backend.notebook_id != manifest.notebook_id
        ):
            raise RuntimeError("PROJECT_BRAIN_BINDING_MISMATCH")
        return project_root, manifest_path, manifest, sources

    def grounding_for(
        project_root: Path,
        manifest: ProjectBrainManifest,
        sources: tuple[Any, ...],
    ) -> GroundingReport:
        return assess_project_grounding(manifest, sources, project_root)

    @mcp.tool(
        name="brain_discover",
        description="Discover the nearest project-local Project Brain without guessing.",
        annotations={"readOnlyHint": True},
    )
    def brain_discover(project_path: str = ".") -> dict[str, Any]:
        project_root, manifest_path, manifest = discover_project_brain(Path(project_path))
        return {
            "configured": True,
            "project_root": str(project_root),
            "manifest_path": str(manifest_path),
            "manifest": manifest.to_dict(),
        }

    @mcp.tool(
        name="brain_capabilities",
        description="Describe Project Brain features currently available through this MCP.",
        annotations={"readOnlyHint": True},
    )
    def brain_capabilities() -> dict[str, Any]:
        return {
            "project_binding": True,
            "health": True,
            "grounding_check": True,
            "onboarding_plan": True,
            "source_capacity": True,
            "grounded_ask": True,
            "context_recovery": True,
            "source_mutation": False,
            "artifact_generation": False,
            "note": (
                "Source mutation and NotebookLM Studio artifacts are intentionally "
                "outside this read-only Project Brain MCP batch."
            ),
        }

    @mcp.tool(
        name="brain_grounding_check",
        description="Check required project-source roles and local content freshness.",
        annotations={"readOnlyHint": True},
    )
    def brain_grounding_check(project_path: str = ".") -> dict[str, Any]:
        project_root, manifest_path, manifest, sources = load_context(project_path)
        report = grounding_for(project_root, manifest, sources)
        return {
            "project_root": str(project_root),
            "manifest_path": str(manifest_path),
            "advisor_id": manifest.advisor_id,
            "grounding": report.to_dict(),
        }

    @mcp.tool(
        name="brain_onboarding_plan",
        description=(
            "Return review-only canonical-document candidates. The responsible project "
            "Agent must read and approve them; this tool never uploads."
        ),
        annotations={"readOnlyHint": True},
    )
    def brain_onboarding_plan(project_path: str = ".") -> dict[str, Any]:
        project_root, _, manifest, sources = load_context(project_path)
        report = grounding_for(project_root, manifest, sources)
        plan = build_onboarding_plan(project_root, manifest, report)
        return {**plan.to_dict(), "plan_digest": plan.digest}

    @mcp.tool(
        name="brain_health",
        description="Validate binding, Notebook access, source drift, capacity, and grounding.",
        annotations={"readOnlyHint": True},
    )
    async def brain_health(project_path: str = ".") -> dict[str, Any]:
        project_root, manifest_path, manifest, sources = load_context(project_path)
        notebook = await backend.get_notebook(manifest.notebook_id)
        capacity = await service.source_capacity(manifest.advisor_id)
        report = grounding_for(project_root, manifest, sources)
        registry_count = sum(source.state != "deleted" for source in sources)
        return {
            "healthy": True,
            "project_root": str(project_root),
            "manifest_path": str(manifest_path),
            "advisor_id": manifest.advisor_id,
            "notebook_id": manifest.notebook_id,
            "notebook_title": notebook.title,
            "registry_source_count": registry_count,
            "backend_source_count": capacity.used,
            "registry_backend_drift": registry_count != capacity.used,
            "source_capacity": capacity.to_dict(),
            "grounding": report.to_dict(),
        }

    @mcp.tool(
        name="brain_ask",
        description="Ask the bound Notebook with grounding readiness attached.",
        annotations={"readOnlyHint": True},
    )
    async def brain_ask(
        question: str,
        project_path: str = ".",
        purpose: Literal["general", "project_explanation", "external_research"] = "project_explanation",
        fresh: bool = False,
    ) -> dict[str, Any]:
        if not question.strip():
            raise ValueError("question is required")
        project_root, _, manifest, sources = load_context(project_path)
        report = grounding_for(project_root, manifest, sources)
        if purpose == "project_explanation" and not report.can_explain_project:
            raise RuntimeError(
                "PROJECT_GROUNDING_INSUFFICIENT: project explanation requires "
                f"project_ready; current status is {report.status}"
            )
        response = await service.ask(manifest.advisor_id, question, fresh=fresh)
        return {
            "advisor_id": manifest.advisor_id,
            "notebook_id": manifest.notebook_id,
            "purpose": purpose,
            "grounding": report.to_dict(),
            "answer": response.answer,
            "formatted_answer": format_answer_with_citations(response, sources),
            "conversation_id": response.conversation_id,
            "citations_count": len(response.references),
            "advisory_only": True,
        }

    @mcp.tool(
        name="brain_recover",
        description="Recover project context from a project_ready Notebook; fail closed otherwise.",
        annotations={"readOnlyHint": True},
    )
    async def brain_recover(project_path: str = ".", fresh: bool = True) -> dict[str, Any]:
        project_root, _, manifest, sources = load_context(project_path)
        report = grounding_for(project_root, manifest, sources)
        if not report.can_explain_project:
            raise RuntimeError(
                "PROJECT_GROUNDING_INSUFFICIENT: context recovery requires project_ready; "
                f"current status is {report.status}"
            )
        question = (
            "Recover the current project context. Summarize the project purpose, architecture, "
            "current status, active decisions, unresolved risks, and the next concrete work. "
            "Distinguish source-backed facts from uncertainty and cite every material claim."
        )
        response = await service.ask(manifest.advisor_id, question, fresh=fresh)
        return {
            "advisor_id": manifest.advisor_id,
            "notebook_id": manifest.notebook_id,
            "grounding": report.to_dict(),
            "answer": response.answer,
            "formatted_answer": format_answer_with_citations(response, sources),
            "conversation_id": response.conversation_id,
            "citations_count": len(response.references),
            "advisory_only": True,
        }

    return mcp


def main() -> None:
    create_project_brain_server().run(transport="stdio")


if __name__ == "__main__":
    main()
