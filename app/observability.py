
"""Observability: cấu hình Langfuse cho LangGraph.

Contract:
    get_run_config(
        session_id: str | None = None,
        tags: list[str] | None = None
    ) -> dict

Owner: D - Guardrails + Observability

Khi Langfuse chưa được cấu hình hoặc khởi tạo thất bại,
ứng dụng vẫn chạy bình thường mà không bật tracing.
"""

from app import config


def get_run_config(
    session_id: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Tạo cấu hình callback và metadata cho graph.invoke()."""

    if not config.LANGFUSE_ENABLED:
        return {}

    try:
        from langfuse.langchain import CallbackHandler

        handler = CallbackHandler()

    except Exception:
        return {}

    metadata = {}

    if session_id:
        metadata["langfuse_session_id"] = session_id

    if tags:
        metadata["langfuse_tags"] = tags

    return {
        "callbacks": [handler],
        "metadata": metadata,
    }
