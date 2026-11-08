"""HỢP ĐỒNG DỮ LIỆU GIỮA CÁC MODULE. Sửa file này phải báo cả nhóm và tạo PR riêng.

Owner: A (Tech lead)
"""
from typing import Literal, NotRequired, TypedDict

# policy = hỏi thông tin chính sách (không hành động)
# order = hỏi trạng thái đơn (không hành động)
# return / complaint = YÊU CẦU cần xử lý: agent quyết định và thực hiện hành động
Intent = Literal["policy", "order", "return", "complaint", "other"]

# Kết quả xử lý của một lượt
Status = Literal[
    "answered",           # đã trả lời thông tin (policy / order / other)
    "completed",          # đã thực hiện hành động, có mã phiếu
    "pending_approval",   # rủi ro: dừng, chờ nhân viên duyệt
    "rejected",           # không đủ điều kiện theo chính sách
    "need_info",          # thiếu mã đơn / 4 số cuối SĐT, hoặc không xác minh được
    "blocked",            # bị input_guard chặn
]


class Chunk(TypedDict):
    text: str
    source: str  # tên file chính sách, dùng để trích dẫn
    score: NotRequired[float]  # độ liên quan 0-1 (B trả nếu có); thấp hơn RAG_MIN_SCORE thì bị loại


class AgentState(TypedDict, total=False):
    # --- đầu vào ---
    question: str
    session_id: str
    memory: dict  # yêu cầu đang dở của phiên (do graph.run nạp), dùng để hỏi lại thiếu thông tin
    request_text: str  # nội dung yêu cầu đầy đủ (gộp các lượt bổ sung thông tin)

    # --- guard đầu vào ---
    blocked: bool
    block_reason: str

    # --- phân loại ---
    intent: Intent
    order_id: str | None
    phone_last4: str | None

    # --- dữ liệu thu thập ---
    context: list[Chunk]  # kết quả RAG
    order: dict | None  # kết quả get_order
    need_verify: bool  # thiếu mã đơn / 4 số cuối SĐT

    # --- quyết định và hành động (yêu cầu đổi trả / khiếu nại) ---
    decision: str  # auto_approve | needs_approval | reject
    decision_reasons: list[str]  # lý do, dùng để giải thích cho khách và cho nhân viên duyệt
    action: str | None  # return_created | complaint_created | approval_requested
    ticket_id: str | None  # mã phiếu đã tạo (RT-xxxx đổi trả, TK-xxxx khiếu nại)
    approval_id: str | None  # mã chờ duyệt (AP-xxxx)

    # --- đầu ra ---
    status: Status
    answer: str
    pii_found: bool
    handoff: bool  # True nếu không đủ thông tin và chuyển nhân viên
    trace: list[str]  # vết các node đã chạy, tiện debug và demo
