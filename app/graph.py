"""Lắp graph. Cấu trúc graph khai báo MỘT chỗ (NODES / EDGES / CONDITIONAL), dùng cho
cả LangGraph lẫn bộ chạy dự phòng (khi chưa cài langgraph, dùng để test hợp đồng).

Hai điểm vào:
  run(question)                                   khách gửi yêu cầu
  resolve_approval(approval_id, approve, ...)     nhân viên duyệt / từ chối ca đang chờ

Owner: A (Tech lead)
"""
import uuid

from app import config, guardrails, nodes, tools
from app.observability import get_run_config
from app.state import AgentState

END = "__end__"

NODES = {
    "input_guard": nodes.input_guard_node,
    "blocked": nodes.blocked_node,
    "classify": nodes.classify_node,
    "policy_rag": nodes.policy_node,
    "order_lookup": nodes.order_node,
    "gather": nodes.gather_node,
    "decide": nodes.decide_node,
    "execute": nodes.execute_node,
    "request_approval": nodes.request_approval_node,
    "respond": nodes.respond_node,
    "output_guard": nodes.output_guard_node,
}
ENTRY = "input_guard"

EDGES = {  # cạnh cố định
    "blocked": "output_guard",
    "policy_rag": "respond",
    "order_lookup": "respond",
    "execute": "respond",
    "request_approval": "respond",
    "respond": "output_guard",
    "output_guard": END,
}

CONDITIONAL = {  # node -> (hàm rẽ nhánh, các đích có thể)
    "input_guard": (nodes.route_after_input_guard, ["blocked", "classify"]),
    "classify": (nodes.route_by_intent, ["policy_rag", "order_lookup", "gather", "respond"]),
    "gather": (nodes.route_after_gather, ["decide", "respond"]),
    "decide": (nodes.route_after_decide, ["execute", "request_approval", "respond"]),
}


def build_langgraph():
    from langgraph.graph import END as LG_END
    from langgraph.graph import StateGraph

    g = StateGraph(AgentState)
    for name, fn in NODES.items():
        g.add_node(name, fn)
    g.set_entry_point(ENTRY)
    for src, dst in EDGES.items():
        g.add_edge(src, LG_END if dst == END else dst)
    for src, (router, targets) in CONDITIONAL.items():
        g.add_conditional_edges(src, router, {t: t for t in targets})
    return g.compile()


class _FallbackGraph:
    """Bộ chạy tuần tự có cùng topology, chỉ dùng khi chưa cài langgraph."""

    def invoke(self, state: AgentState, config: dict | None = None) -> AgentState:
        state = dict(state)
        node = ENTRY
        while node != END:
            state.update(NODES[node](state))
            if node in CONDITIONAL:
                node = CONDITIONAL[node][0](state)
            else:
                node = EDGES[node]
        return state  # type: ignore[return-value]


def build_graph():
    try:
        return build_langgraph()
    except ImportError:
        return _FallbackGraph()


_graph = None
_SESSIONS: dict[str, dict] = {}  # session_id -> yêu cầu đang dở (đang chờ khách bổ sung mã đơn / SĐT)
_RESUMABLE = ("return", "order", "complaint")


def reset_sessions() -> None:
    _SESSIONS.clear()


def _remember(sid: str, final: AgentState) -> None:
    """Chỉ nhớ khi agent đang hỏi lại khách; xong việc hoặc khách chuyển chủ đề thì quên."""
    if final.get("status") == "need_info" and final.get("intent") in _RESUMABLE:
        _SESSIONS[sid] = {
            "intent": final["intent"],
            "order_id": final.get("order_id"),
            # Còn thiếu thông tin thì giữ phần đã có; sai SĐT thì bỏ SĐT cũ để khách nhập lại.
            "phone_last4": final.get("phone_last4") if final.get("need_verify") else None,
            "question": final.get("request_text") or final["question"],
        }
    else:
        _SESSIONS.pop(sid, None)


def run(question: str, session_id: str | None = None) -> AgentState:
    """Điểm vào cho khách: CLI, UI và evals đều gọi qua đây.

    Truyền cùng `session_id` cho các lượt của một cuộc chat để agent hỏi lại khi thiếu thông tin
    (khách trả lời "SĐT cuối 1111" thì tiếp tục yêu cầu đang dở).
    """
    global _graph
    if _graph is None:
        _graph = build_graph()
    sid = session_id or str(uuid.uuid4())
    state: AgentState = {"question": question, "session_id": sid, "trace": []}
    if sid in _SESSIONS:
        state["memory"] = dict(_SESSIONS[sid])
    final = _graph.invoke(state, config=get_run_config(session_id=sid))
    _remember(sid, final)
    return final


def resolve_approval(approval_id: str, approve: bool, reviewer: str, note: str = "") -> dict:
    """Điểm vào cho nhân viên: duyệt thì tạo phiếu, từ chối thì đóng yêu cầu.

    Trả về {approval, status, ticket_id, message}; message là thông báo gửi lại cho khách
    (đã qua output_guard vì ghi chú của nhân viên có thể chứa SĐT).
    """
    a = tools.resolve_approval(approval_id, approve, reviewer, note)
    if approve:
        msg = config.MSG_APPROVED_NOTIFY.format(approval_id=approval_id, ticket_id=a["ticket_id"], note=note)
    else:
        msg = config.MSG_DENIED_NOTIFY.format(approval_id=approval_id, note=note)
    msg, _ = guardrails.output_guard(msg.strip())
    return {"approval": a, "status": "completed" if approve else "rejected",
            "ticket_id": a["ticket_id"], "message": msg}
