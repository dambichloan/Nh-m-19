"""Các node của graph. Mỗi node nhận AgentState và trả về dict CẬP NHẬT một phần state
(đúng kiểu LangGraph), nên chạy được cả trong LangGraph lẫn bộ chạy dự phòng.

Owner: A (Tech lead)
"""
from app import config, guardrails, llm, rag, tools
from app.state import AgentState


def _trace(state: AgentState, name: str) -> list[str]:
    return [*state.get("trace", []), name]


def input_guard_node(state: AgentState) -> dict:
    result = guardrails.input_guard(state["question"])
    return {
        "blocked": result.blocked,
        "block_reason": result.reason,
        "trace": _trace(state, "input_guard"),
    }


def blocked_node(state: AgentState) -> dict:
    return {"answer": config.MSG_BLOCKED, "trace": _trace(state, "blocked")}


def classify_node(state: AgentState) -> dict:
    r = llm.classify_intent(state["question"])
    return {
        "intent": r.intent,
        "order_id": r.order_id,
        "phone_last4": r.phone_last4,
        "trace": _trace(state, "classify_intent"),
    }


def policy_node(state: AgentState) -> dict:
    return {
        "context": rag.retrieve(state["question"], k=4),
        "trace": _trace(state, "policy_rag"),
    }


def order_node(state: AgentState) -> dict:
    order_id = state.get("order_id")
    phone4 = state.get("phone_last4")
    if not order_id or (config.REQUIRE_PHONE_VERIFY and not phone4):
        return {"need_verify": True, "order": None, "trace": _trace(state, "order_lookup(need_verify)")}
    return {
        "need_verify": False,
        "order": tools.get_order(order_id, phone4),
        "trace": _trace(state, "order_lookup"),
    }


def complaint_node(state: AgentState) -> dict:
    ticket = tools.create_complaint(state.get("order_id"), state["question"])
    return {"ticket_id": ticket, "trace": _trace(state, "complaint")}


def respond_node(state: AgentState) -> dict:
    intent = state.get("intent", "other")

    if intent == "order" and state.get("need_verify"):
        answer = config.MSG_NEED_VERIFY
    elif intent == "order" and not state.get("order"):
        answer = config.MSG_ORDER_NOT_FOUND
    elif intent == "policy" and not state.get("context"):
        answer = config.MSG_NO_INFO  # không có context thì không để model bịa
    else:
        answer = llm.generate_answer(
            question=state["question"],
            intent=intent,
            context=state.get("context"),
            order=state.get("order"),
            ticket_id=state.get("ticket_id"),
        )
    return {"answer": answer, "trace": _trace(state, "respond")}


def output_guard_node(state: AgentState) -> dict:
    text, pii = guardrails.output_guard(state["answer"])
    return {"answer": text, "pii_found": pii, "trace": _trace(state, "output_guard")}


# ---------- hàm rẽ nhánh ----------
def route_after_input_guard(state: AgentState) -> str:
    return "blocked" if state.get("blocked") else "classify"


def route_by_intent(state: AgentState) -> str:
    return {
        "policy": "policy_rag",
        "order": "order_lookup",
        "complaint": "complaint",
    }.get(state.get("intent", "other"), "respond")
