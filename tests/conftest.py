import pytest

from app import graph, tools


@pytest.fixture(autouse=True)
def _fixed_world(monkeypatch):
    """Mỗi test bắt đầu với: hôm nay = 2026-11-08, chưa có phiếu nào, chạy stub offline."""
    monkeypatch.setenv("FAKE_TODAY", "2026-11-08")
    tools.reset_state()
    graph.reset_sessions()
    yield
    tools.reset_state()
    graph.reset_sessions()
