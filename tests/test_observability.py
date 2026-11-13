
from types import SimpleNamespace

import pytest

from app.observability import (
    build_observation_metadata, extract_token_usage, measure_latency,
)


def test_extract_token_usage_from_langchain_usage_metadata():
    response = SimpleNamespace(usage_metadata={
        "input_tokens": 12, "output_tokens": 7, "total_tokens": 19
    })
    assert extract_token_usage(response) == {
        "input_tokens": 12, "output_tokens": 7, "total_tokens": 19
    }


def test_extract_token_usage_from_openai_response_metadata():
    response = SimpleNamespace(response_metadata={
        "token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    })
    assert extract_token_usage(response) == {
        "input_tokens": 10, "output_tokens": 5, "total_tokens": 15
    }


def test_extract_token_usage_returns_none_when_unavailable():
    assert extract_token_usage(object()) is None


def test_measure_latency_records_nonnegative_value():
    with measure_latency() as metrics:
        sum(range(100))
    assert metrics["latency_ms"] >= 0


def test_build_observation_metadata_only_includes_real_values():
    result = build_observation_metadata(
        step_index=2, latency_ms=15.5,
        token_usage={"input_tokens": 10, "output_tokens": 4},
    )
    assert result["step_index"] == 2
    assert result["latency_ms"] == 15.5
    assert result["token_usage"]["input_tokens"] == 10


def test_build_observation_metadata_rejects_invalid_step():
    with pytest.raises(ValueError):
        build_observation_metadata(step_index=-1)
