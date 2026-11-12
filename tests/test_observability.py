
import langfuse.langchain

from app import config
from app.observability import get_run_config


def test_langfuse_disabled_returns_empty_config(monkeypatch):
    monkeypatch.setattr(config, "LANGFUSE_ENABLED", False)

    result = get_run_config(
        session_id="test-session",
        tags=["test"],
    )

    assert result == {}


def test_langfuse_enabled_returns_callback_and_metadata(monkeypatch):
    class FakeCallbackHandler:
        pass

    monkeypatch.setattr(config, "LANGFUSE_ENABLED", True)
    monkeypatch.setattr(
        langfuse.langchain,
        "CallbackHandler",
        FakeCallbackHandler,
    )

    result = get_run_config(
        session_id="test-session",
        tags=["test", "guardrails"],
    )

    assert len(result["callbacks"]) == 1
    assert isinstance(
        result["callbacks"][0],
        FakeCallbackHandler,
    )

    assert result["metadata"] == {
        "langfuse_session_id": "test-session",
        "langfuse_tags": ["test", "guardrails"],
    }


def test_langfuse_enabled_without_optional_metadata(monkeypatch):
    class FakeCallbackHandler:
        pass

    monkeypatch.setattr(config, "LANGFUSE_ENABLED", True)
    monkeypatch.setattr(
        langfuse.langchain,
        "CallbackHandler",
        FakeCallbackHandler,
    )

    result = get_run_config()

    assert len(result["callbacks"]) == 1
    assert result["metadata"] == {}
