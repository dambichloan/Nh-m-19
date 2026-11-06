"""Lắp graph. Cấu trúc graph khai báo MỘT chỗ (NODES / EDGES / CONDITIONAL), dùng cho
cả LangGraph lẫn bộ chạy dự phòng (khi chưa cài langgraph, dùng để test hợp đồng).

Owner: A (Tech lead)
"""
import uuid

from app import nodes
from app.observability import get_run_config
from app.state import AgentState

END = "__end__"

NODES = {
    "input_guard": nodes.input_guard_node,
    "blocked": nodes.blocked_node,
    "classify": nodes.classify_node,
    "policy_rag": nodes.policy_node,
    "order_lookup": nodes.order_node,
    "complaint": nodes.complaint_node,
    "respond": nodes.respond_node,
    "output_guard": nodes.output_guard_node,
}
ENTRY = "input_guard"

EDGES = {  # cạnh cố định
    "blocked": "output_guard",
    "policy_rag": "respond",
    "order_lookup": "respond",
    "complaint": "respond",
    "respond": "output_guard",
    "output_guard": END,
}

CONDITIONAL = {  # node -> (hàm rẽ nhánh, các đích có thể)
    "input_guard": (nodes.route_after_input_guard, ["blocked", "classify"]),
    "classify": (nodes.route_by_intent, ["policy_rag", "order_lookup", "complaint", "respond"]),
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


def run(question: str, session_id: str | None = None) -> AgentState:
    """Điểm vào duy nhất cho CLI, UI và evals."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    sid = session_id or str(uuid.uuid4())
    state: AgentState = {"question": question, "session_id": sid, "trace": []}
    return _graph.invoke(state, config=get_run_config(session_id=sid))
