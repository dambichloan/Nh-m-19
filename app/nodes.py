"""Các node của graph. Mỗi node nhận AgentState và trả về dict CẬP NHẬT một phần state
(đúng kiểu LangGraph), nên chạy được cả trong LangGraph lẫn bộ chạy dự phòng.

Luồng yêu cầu (return / complaint):
  classify -> gather (xác minh + tra đơn + RAG) -> decide (luật) -> execute | request_approval | respond

Owner: A (Tech lead)
"""
from app import config, guardrails, llm, policy_rules, rag, tools
from app.state import AgentState


def _trace(state: AgentState, name: str) -> list[str]:
    return [*state.get("trace", []), name]


# ---------- đầu vào ----------
def input_guard_node(state: AgentState) -> dict:
    result = guardrails.input_guard(state["question"])
    return {
        "blocked": result.blocked,
        "block_reason": result.reason,
        "trace": _trace(state, "input_guard"),
    }


def blocked_node(state: AgentState) -> dict:
    return {"answer": config.MSG_BLOCKED, "status": "blocked", "trace": _trace(state, "blocked")}


def classify_node(state: AgentState) -> dict:
    r = llm.classify_intent(state["question"])
    return {
        "intent": r.intent,
        "order_id": r.order_id,
        "phone_last4": r.phone_last4,
        "trace": _trace(state, "classify_intent"),
    }


# ---------- nhánh chỉ hỏi thông tin ----------
def policy_node(state: AgentState) -> dict:
    return {
        "context": rag.retrieve(state["question"], k=4),
        "status": "answered",
        "trace": _trace(state, "policy_rag"),
    }


def order_node(state: AgentState) -> dict:
    order_id = state.get("order_id")
    phone4 = state.get("phone_last4")
    if not order_id or (config.REQUIRE_PHONE_VERIFY and not phone4):
        return {"need_verify": True, "order": None, "status": "need_info",
                "trace": _trace(state, "order_lookup(need_verify)")}
    order = tools.get_order(order_id, phone4)
    return {
        "need_verify": False,
        "order": order,
        "status": "answered" if order else "need_info",
        "trace": _trace(state, "order_lookup"),
    }


# ---------- nhánh yêu cầu: đổi trả / khiếu nại ----------
def gather_node(state: AgentState) -> dict:
    """Thu thập dữ kiện: đối chiếu chính sách (RAG) và tra đơn đã xác minh."""
    intent = state["intent"]
    order_id, phone4 = state.get("order_id"), state.get("phone_last4")
    out: dict = {"context": rag.retrieve(state["question"], k=4), "trace": _trace(state, "gather")}

    if intent == "return":
        # Hành động thay đổi dữ liệu trên đơn => bắt buộc xác minh.
        if not order_id or (config.REQUIRE_PHONE_VERIFY and not phone4):
            return {**out, "need_verify": True, "order": None, "status": "need_info"}
        order = tools.get_order(order_id, phone4)
        if order is None:
            return {**out, "need_verify": False, "order": None, "status": "need_info"}
        return {**out, "need_verify": False, "order": order}

    # complaint: khiếu nại không bắt buộc xác minh (rủi ro thấp); có đủ thông tin thì đối chiếu thêm.
    order = tools.get_order(order_id, phone4) if order_id and phone4 else None
    return {**out, "need_verify": False, "order": order}


def decide_node(state: AgentState) -> dict:
    """Quyết định bằng luật (policy_rules), không dùng LLM."""
    if state["intent"] == "return":
        dup = tools.find_open_request(state.get("order_id"), "return")
        d = policy_rules.decide_return(state["order"], state["question"], config.today(), dup)
    else:
        d = policy_rules.decide_complaint(state.get("order"), state["question"])
    out = {"decision": d.outcome, "decision_reasons": d.reasons, "trace": _trace(state, f"decide({d.outcome})")}
    if d.outcome == policy_rules.REJECT:
        out["status"] = "rejected"
    return out


def execute_node(state: AgentState) -> dict:
    """Thực hiện hành động: tạo phiếu."""
    if state["intent"] == "return":
        tid, action = tools.create_return(state.get("order_id"), state["question"]), "return_created"
    else:
        tid, action = tools.create_complaint(state.get("order_id"), state["question"]), "complaint_created"
    return {"ticket_id": tid, "action": action, "status": "completed", "trace": _trace(state, "execute")}


def request_approval_node(state: AgentState) -> dict:
    """Ca rủi ro: KHÔNG tạo phiếu, đưa vào hàng chờ nhân viên duyệt rồi dừng."""
    aid = tools.submit_for_approval(
        state["intent"], state.get("order_id"), state["question"], state.get("decision_reasons", [])
    )
    return {"approval_id": aid, "action": "approval_requested", "status": "pending_approval",
            "trace": _trace(state, "request_approval")}


# ---------- trả lời ----------
def respond_node(state: AgentState) -> dict:
    intent = state.get("intent", "other")
    status = state.get("status")
    reasons = "; ".join(state.get("decision_reasons", []))

    if intent in ("return", "complaint"):
        if state.get("need_verify"):
            answer = config.MSG_NEED_VERIFY
        elif status == "need_info":  # có mã đơn + SĐT nhưng không khớp
            answer = config.MSG_ORDER_NOT_FOUND
        elif status == "rejected":
            answer = config.MSG_REJECTED.format(order_id=state.get("order_id"), reasons=reasons)
            if state.get("context"):
                answer += f" (nguồn: {state['context'][0]['source']})"
        elif status == "pending_approval":
            answer = config.MSG_PENDING.format(approval_id=state["approval_id"], reasons=reasons)
        elif intent == "return":
            answer = config.MSG_RETURN_DONE.format(order_id=state.get("order_id"), ticket_id=state["ticket_id"])
        else:
            answer = config.MSG_COMPLAINT_DONE.format(ticket_id=state["ticket_id"])
    elif intent == "order" and state.get("need_verify"):
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
    update = {"answer": answer, "trace": _trace(state, "respond")}
    if "status" not in state:  # nhánh other
        update["status"] = "answered"
    return update


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
        "return": "gather",
        "complaint": "gather",
    }.get(state.get("intent", "other"), "respond")


def route_after_gather(state: AgentState) -> str:
    # Thiếu xác minh hoặc không tìm thấy đơn đổi trả: dừng và hỏi lại, không quyết định.
    if state["intent"] == "return" and (state.get("need_verify") or not state.get("order")):
        return "respond"
    return "decide"


def route_after_decide(state: AgentState) -> str:
    return {
        policy_rules.AUTO: "execute",
        policy_rules.NEEDS_APPROVAL: "request_approval",
    }.get(state["decision"], "respond")
