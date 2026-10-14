"""Post-install diagnostics for Project Brain integrations."""

from __future__ import annotations

from typing import Any

from notebooklm_skill.backend import NotebookBackend
from notebooklm_skill.capacity import inspect_source_capacity
from notebooklm_skill.grounding import assess_project_grounding
from notebooklm_skill.installer import InstallTarget, build_install_plan
from notebooklm_skill.mcp_server import create_project_brain_server
from notebooklm_skill.project_brain import (
    ProjectBrainNotConfiguredError,
    discover_project_brain,
)
from notebooklm_skill.storage import AdvisorStore

EXPECTED_MCP_TOOLS = {
    "brain_discover",
    "brain_capabilities",
    "brain_grounding_check",
    "brain_onboarding_plan",
    "brain_health",
    "brain_ask",
    "brain_recover",
}


async def diagnose_project_brain(
    target: InstallTarget,
    backend: NotebookBackend,
    store: AdvisorStore,
) -> dict[str, Any]:
    plan = build_install_plan(target)
    integration_installed = (
        plan.can_install
        and plan.mcp_action == "unchanged"
        and plan.skill_action == "unchanged"
    )

    server = create_project_brain_server(backend=backend, state_root=store.root)
    tools = {tool.name for tool in await server.list_tools()}
    tools_ok = tools == EXPECTED_MCP_TOOLS

    binding: dict[str, Any]
    live_ok = False
    grounding_ready = False
    try:
        project_root, manifest_path, manifest = discover_project_brain(
            target.project_root
        )
        profile, _, sources = store.load(manifest.advisor_id)
        if (
            profile.backend.type != manifest.backend_type
            or profile.backend.notebook_id != manifest.notebook_id
        ):
            raise RuntimeError("PROJECT_BRAIN_BINDING_MISMATCH")
        notebook = await backend.get_notebook(manifest.notebook_id)
        capacity = await inspect_source_capacity(backend, manifest.notebook_id)
        grounding = assess_project_grounding(manifest, sources, project_root)
        live_ok = True
        grounding_ready = grounding.can_explain_project
        binding = {
            "status": "configured",
            "project_root": str(project_root),
            "manifest_path": str(manifest_path),
            "advisor_id": manifest.advisor_id,
            "notebook_id": manifest.notebook_id,
            "notebook_title": notebook.title,
            "source_capacity": capacity.to_dict(),
            "grounding": grounding.to_dict(),
        }
    except ProjectBrainNotConfiguredError:
        binding = {
            "status": "needs_brain_init",
            "next_step": (
                "Run brain-init --project-root PROJECT --advisor-id ADVISOR_ID "
                "after selecting an existing Advisor."
            ),
        }
    except Exception as exc:
        binding = {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "status": (
            "ready"
            if integration_installed and tools_ok and live_ok
            else "needs_attention"
        ),
        "client": target.client,
        "installation_ok": integration_installed,
        "install_plan": plan.to_dict(),
        "mcp_tools_ok": tools_ok,
        "mcp_tools": sorted(tools),
        "client_connection_verified": False,
        "client_verification_step": (
            "After client reload, call brain_capabilities and brain_health through MCP."
        ),
        "binding": binding,
        "project_explanation_ready": grounding_ready,
    }
