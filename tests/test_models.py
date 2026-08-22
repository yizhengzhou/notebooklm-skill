import pytest

from notebooklm_skill.models import PersonaProfile, ResearchProfile, SourceRecord, WatchItem


def test_models_reject_invalid_ids_and_empty_research() -> None:
    with pytest.raises(ValueError, match="watch_id"):
        WatchItem(watch_id="../escape", kind="question", statement="Unsafe ID")

    with pytest.raises(ValueError, match="Research brief"):
        ResearchProfile(brief="", queries=())


def test_models_reject_unsupported_persona_length_and_source_state() -> None:
    with pytest.raises(ValueError, match="Unsupported response length"):
        PersonaProfile(instructions="Persona", response_length="verbose")

    with pytest.raises(ValueError, match="Unsupported source state"):
        SourceRecord(
            local_id="src-001",
            backend_source_id="backend-1",
            title="Source",
            state="unknown",
            origin="manual",
        )
