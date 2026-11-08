
"""Observability: Langfuse tracing for LangGraph."""

from app import config


def get_run_config(
    session_id: str | None = None,
    tags: list[str] | None = None
) -> dict:
    if not config.LANGFUSE_ENABLED:
        print("[Langfuse] Disabled: kiểm tra API keys và config.")
        return {}

    try:
        from langfuse.langchain import CallbackHandler

        handler = CallbackHandler()

        print("[Langfuse] CallbackHandler initialized successfully.")

        return {
            "callbacks": [handler],
            "metadata": {
                "langfuse_session_id": session_id,
                "langfuse_tags": tags or [],
            },
        }

    except Exception as e:
        print(f"[Langfuse ERROR] {type(e).__name__}: {e}")
        raise
