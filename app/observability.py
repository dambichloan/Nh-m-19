
"""Langfuse observability và tiện ích đo lường độc lập với graph/LLM."""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Any, Iterator

from app import config

PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")


def _get_model_name() -> str:
    provider = str(config.LLM_PROVIDER).lower()
    return "stub" if provider == "stub" else str(config.LLM_MODEL)


def get_run_config(session_id=None, tags=None):
    """Tạo LangGraph config; giữ tương thích với lời gọi hiện tại."""
    if not config.LANGFUSE_ENABLED:
        return {}
    try:
        from langfuse.langchain import CallbackHandler
        handler = CallbackHandler()
    except Exception:
        return {}

    metadata = {
        "prompt_version": PROMPT_VERSION,
        "model_name": _get_model_name(),
    }
    if session_id:
        metadata["langfuse_session_id"] = str(session_id)
    if tags:
        metadata["langfuse_tags"] = list(tags) if not isinstance(tags, str) else [tags]
    return {"callbacks": [handler], "metadata": metadata}


def extract_token_usage(response: Any) -> dict[str, int] | None:
    """Lấy token usage từ các cấu trúc thường gặp của LangChain/OpenAI/Gemini."""
    if response is None:
        return None

    candidates = [
        getattr(response, "usage_metadata", None),
        getattr(response, "response_metadata", {}).get("token_usage")
        if isinstance(getattr(response, "response_metadata", None), dict) else None,
        getattr(response, "response_metadata", {}).get("usage")
        if isinstance(getattr(response, "response_metadata", None), dict) else None,
    ]
    for usage in candidates:
        if not isinstance(usage, dict):
            continue
        input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
        output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
        total_tokens = usage.get("total_tokens")
        if input_tokens is None and output_tokens is None and total_tokens is None:
            continue
        result: dict[str, int] = {}
        if input_tokens is not None:
            result["input_tokens"] = int(input_tokens)
        if output_tokens is not None:
            result["output_tokens"] = int(output_tokens)
        if total_tokens is not None:
            result["total_tokens"] = int(total_tokens)
        elif "input_tokens" in result and "output_tokens" in result:
            result["total_tokens"] = result["input_tokens"] + result["output_tokens"]
        return result
    return None


@contextmanager
def measure_latency() -> Iterator[dict[str, float]]:
    """Đo thời gian thực thi; dùng: with measure_latency() as metrics: ..."""
    metrics: dict[str, float] = {}
    started = time.perf_counter()
    try:
        yield metrics
    finally:
        metrics["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)


def build_observation_metadata(
    *,
    step_index: int | None = None,
    latency_ms: float | None = None,
    token_usage: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Chuẩn hóa metadata quan sát; chỉ thêm số liệu thực sự được cung cấp."""
    metadata: dict[str, Any] = {}
    if step_index is not None:
        if not isinstance(step_index, int) or isinstance(step_index, bool) or step_index < 0:
            raise ValueError("step_index phải là số nguyên không âm.")
        metadata["step_index"] = step_index
    if latency_ms is not None:
        if latency_ms < 0:
            raise ValueError("latency_ms không được âm.")
        metadata["latency_ms"] = float(latency_ms)
    if token_usage is not None:
        metadata["token_usage"] = {
            str(key): int(value) for key, value in token_usage.items()
            if value is not None and int(value) >= 0
        }
    return metadata
