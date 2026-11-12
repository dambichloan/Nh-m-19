"""Hỏi lại khi thiếu thông tin (nhiều lượt), nhận biết không đủ chính sách, chế độ strict."""
import pytest

from app import config, llm, nodes, tools
from app.graph import run


def test_missing_phone_then_followup_completes_same_request():
    a = run("Tôi muốn đổi size áo, đơn #124", "s1")
    assert a["status"] == "need_info" and "4 số cuối" in a["answer"]
    b = run("SĐT cuối 1111", "s1")
    assert b["intent"] == "return" and b["status"] == "completed" and b["ticket_id"].startswith("RT-")
    assert "classify_intent(resume)" in b["trace"]


def test_bare_digits_answer_works():
    run("Tôi muốn đổi size áo, đơn #124", "s1")
    assert run("1111", "s1")["status"] == "completed"


def test_reason_from_first_message_is_kept():
    run("Tôi muốn trả hàng đơn #125, áo bị rách", "s1")  # thiếu SĐT
    b = run("2222", "s1")  # quá hạn nhưng báo lỗi ở lượt đầu => ngoại lệ chờ duyệt
    assert b["status"] == "pending_approval"


def test_order_lookup_followup():
    run("Đơn #123 đang ở đâu?", "s1")
    b = run("SĐT cuối 5678", "s1")
    assert b["intent"] == "order" and b["status"] == "answered" and "Đang giao" in b["answer"]


def test_wrong_phone_then_correct_phone():
    a = run("Tôi muốn trả hàng đơn #124 SĐT cuối 9999", "s1")
    assert a["status"] == "need_info" and not a.get("ticket_id")
    b = run("SĐT cuối 1111", "s1")
    assert b["status"] == "completed"


def test_topic_change_clears_pending_request():
    run("Tôi muốn đổi hàng đơn #124", "s1")
    p = run("Áo đã giặt có đổi được không?", "s1")
    assert p["intent"] == "policy"
    c = run("1111", "s1")  # không còn yêu cầu dở để tiếp tục
    assert c["intent"] == "other" and not c.get("ticket_id")


def test_sessions_are_isolated():
    run("Tôi muốn đổi size áo, đơn #124", "alice")
    b = run("SĐT cuối 1111", "bob")
    assert b["intent"] == "other" and not b.get("ticket_id")


def test_no_followup_state_leaks_after_completion():
    run("Tôi muốn đổi size áo, đơn #124, SĐT cuối 1111", "s1")
    assert run("1111", "s1")["intent"] == "other"


# ---------- A5: không đủ chính sách thì chuyển nhân viên ----------
def test_low_relevance_chunks_trigger_handoff(monkeypatch):
    monkeypatch.setattr(config, "RAG_MIN_SCORE", 0.5)
    monkeypatch.setattr(nodes.rag, "retrieve", lambda q, k=4: [{"text": "x", "source": "faq.md", "score": 0.2}])
    s = nodes.policy_node({"question": "câu lạ", "trace": []})
    assert s["context"] == [] and s["handoff"] is True


def test_relevant_chunks_kept(monkeypatch):
    monkeypatch.setattr(config, "RAG_MIN_SCORE", 0.5)
    monkeypatch.setattr(nodes.rag, "retrieve", lambda q, k=4: [{"text": "x", "source": "a.md", "score": 0.9}])
    s = nodes.policy_node({"question": "q", "trace": []})
    assert len(s["context"]) == 1 and s["handoff"] is False


def test_unknown_question_marks_handoff():
    s = run("Hôm nay thời tiết thế nào?")
    assert s["handoff"] is True and "nhân viên" in s["answer"]


# ---------- LLM_STRICT ----------
def test_strict_mode_raises_instead_of_falling_back(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "LLM_STRICT", True)

    class Boom:
        def with_structured_output(self, schema):
            raise RuntimeError("quota")

    monkeypatch.setattr(llm, "_get_llm", lambda: Boom())
    with pytest.raises(RuntimeError):
        llm.classify_intent("Đơn #123 đang ở đâu?")
