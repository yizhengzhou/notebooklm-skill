"""Thin orchestration layer for evergreen Gemini Notebooks."""

from notebooklm_skill.advisor import AdvisorService, PersonaSetupError
from notebooklm_skill.apply_executor import ApplyExecutor, ApplyResult
from notebooklm_skill.apply_plan import ApplyPlan, build_apply_plan, verify_apply_plan, write_apply_plan
from notebooklm_skill.backend import BackendCapabilities, ChatConfig, NotebookBackend, NotebookRef
from notebooklm_skill.evergreen import (
    AdvisorPersistenceError,
    BackendCapabilityError,
    EvergreenService,
    SourceRegistrationError,
    compose_research_query,
)
from notebooklm_skill.export import ExportBundle, export_bundle, read_export_bundle
from notebooklm_skill.gemini_backend import GeminiNotebookBackend
from notebooklm_skill.models import AdvisorProfile, RefreshRun, SourceRecord, WatchItem
from notebooklm_skill.preview import PreviewEngine, PreviewPlan, canonicalize_url, read_preview_plan
from notebooklm_skill.refresh import (
    RefreshExecutionResult,
    RefreshExecutor,
    RefreshPlan,
    RefreshPlanner,
    read_refresh_plan,
    update_registry_verification,
    verify_refresh_plan,
    write_refresh_plan,
)
from notebooklm_skill.storage import AdvisorStore

__all__ = [
    "AdvisorPersistenceError",
    "AdvisorProfile",
    "AdvisorService",
    "ApplyPlan",
    "AdvisorStore",
    "ApplyExecutor",
    "ApplyResult",
    "BackendCapabilities",
    "BackendCapabilityError",
    "ChatConfig",
    "EvergreenService",
    "ExportBundle",
    "GeminiNotebookBackend",
    "NotebookBackend",
    "NotebookRef",
    "PersonaSetupError",
    "PreviewEngine",
    "PreviewPlan",
    "RefreshExecutionResult",
    "RefreshExecutor",
    "RefreshPlan",
    "RefreshPlanner",
    "RefreshRun",
    "SourceRecord",
    "SourceRegistrationError",
    "WatchItem",
    "build_apply_plan",
    "canonicalize_url",
    "compose_research_query",
    "export_bundle",
    "read_export_bundle",
    "read_preview_plan",
    "read_refresh_plan",
    "update_registry_verification",
    "verify_apply_plan",
    "verify_refresh_plan",
    "write_apply_plan",
    "write_refresh_plan",
]
