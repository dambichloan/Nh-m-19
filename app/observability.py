"""Observability. HỢP ĐỒNG: get_run_config(session_id, tags) -> dict dùng làm `config` cho graph.invoke.

Owner: D (Guardrails + Observability)
Khi chưa cấu hình Langfuse thì trả config rỗng (tracing tự tắt, app vẫn chạy).
D kiểm tra lại cách truyền session_id/tags theo đúng phiên bản langfuse đã cài
(v2 và v3 khác nhau).
"""
from app import config


def get_run_config(session_id: str | None = None, tags: list[str] | None = None) -> dict:
    if not config.LANGFUSE_ENABLED:
        return {}
    try:
        try:
            from langfuse.langchain import CallbackHandler  # langfuse v3
        except ImportError:
            from langfuse.callback import CallbackHandler  # langfuse v2
        handler = CallbackHandler()
    except Exception:
        return {}
    return {
        "callbacks": [handler],
        "metadata": {
            "langfuse_session_id": session_id,
            "langfuse_tags": tags or [],
        },
    }
