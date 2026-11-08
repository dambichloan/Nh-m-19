"""Các node của graph. Mỗi node nhận AgentState và trả về dict CẬP NHẬT một phần state
(đúng kiểu LangGraph), nên chạy được cả trong LangGraph lẫn bộ chạy dự phòng.

Luồng yêu cầu (return / complaint):
  classify -> gather (xác minh + tra đơn + RAG) -> decide (luật) -> execute | request_approval | respond

Owner: A (Tech lead)
"""
import re

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


def _text(state: AgentState) -> str:
    """Nội dung yêu cầu đầy đủ (gồm cả lượt đầu nếu khách bổ sung thông tin ở lượt sau)."""
    return state.get("request_text") or state["question"]


def _bare_slot(q: str, mem: dict) -> dict:
    """Khách chỉ gõ '1111' hoặc '#124' để trả lời câu hỏi lại."""
    s = q.strip()
    if mem.get("order_id") and re.fullmatch(r"\d{4}", s):
        return {"phone_last4": s}
    m = re.fullmatch(r"#?(\d{2,})", s)
    if m and not mem.get("order_id"):
        return {"order_id": m.group(1)}
    return {}


def classify_node(state: AgentState) -> dict:
    q = state["question"]
    r = llm.classify_intent(q)
    mem = state.get("memory") or {}
    bare = _bare_slot(q, mem) if mem else {}
    intent = r.intent
    order_id = r.order_id or bare.get("order_id")
    phone4 = r.phone_last4 or bare.get("phone_last4")
    name = "classify_intent"

    # Câu này chỉ bổ sung mã đơn / SĐT cho yêu cầu đang dở => quay lại yêu cầu đó, giữ nội dung lượt đầu.
    resumed = bool(mem) and bool(order_id or phone4) and intent in ("other", mem.get("intent"))
    if resumed:
        intent = mem["intent"]
        order_id = order_id or mem.get("order_id")
        phone4 = phone4 or mem.get("phone_last4")
        request_text = f'{mem.get("question", "")} {q}'.strip()
        name = "classify_intent(resume)"
    else:
        request_text = q
    return {
        "intent": intent,
        "order_id": order_id,
        "phone_last4": phone4,
        "request_text": request_text,
        "trace": _trace(state, name),
    }


def _retrieve(query: str, k: int = 4) -> list:
    """RAG + lọc đoạn kém liên quan (nếu B có trả score)."""
    chunks = rag.retrieve(query, k=k)
    if config.RAG_MIN_SCORE > 0:
        chunks = [c for c in chunks if c.get("score", 1.0) >= config.RAG_MIN_SCORE]
    return chunks


# ---------- nhánh chỉ hỏi thông tin ----------
def policy_node(state: AgentState) -> dict:
    chunks = _retrieve(state["question"])
    return {
        "context": chunks,
        "handoff": not chunks,  # không có đoạn nào đủ liên quan => chuyển nhân viên, không để model tự trả lời
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
    out: dict = {"context": _retrieve(_text(state)), "trace": _trace(state, "gather")}

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
        d = policy_rules.decide_return(state["order"], _text(state), config.today(), dup)
    else:
        d = policy_rules.decide_complaint(state.get("order"), _text(state))
    out = {"decision": d.outcome, "decision_reasons": d.reasons, "trace": _trace(state, f"decide({d.outcome})")}
    if d.outcome == policy_rules.REJECT:
        out["status"] = "rejected"
    return out


def execute_node(state: AgentState) -> dict:
    """Thực hiện hành động: tạo phiếu."""
    if state["intent"] == "return":
        tid, action = tools.create_return(state.get("order_id"), _text(state)), "return_created"
    else:
        tid, action = tools.create_complaint(state.get("order_id"), _text(state)), "complaint_created"
    return {"ticket_id": tid, "action": action, "status": "completed", "trace": _trace(state, "execute")}


def request_approval_node(state: AgentState) -> dict:
    """Ca rủi ro: KHÔNG tạo phiếu, đưa vào hàng chờ nhân viên duyệt rồi dừng."""
    aid = tools.submit_for_approval(
        state["intent"], state.get("order_id"), _text(state), state.get("decision_reasons", [])
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
    if answer == config.MSG_NO_INFO:
        update["handoff"] = True
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
