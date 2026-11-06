"""HỢP ĐỒNG DỮ LIỆU GIỮA CÁC MODULE. Sửa file này phải báo cả nhóm và tạo PR riêng.

Owner: A (Tech lead)
"""
from typing import Literal, TypedDict

Intent = Literal["policy", "order", "complaint", "other"]


class Chunk(TypedDict):
    text: str
    source: str  # tên file chính sách, dùng để trích dẫn


class AgentState(TypedDict, total=False):
    # --- đầu vào ---
    question: str
    session_id: str

    # --- guard đầu vào ---
    blocked: bool
    block_reason: str

    # --- phân loại ---
    intent: Intent
    order_id: str | None
    phone_last4: str | None

    # --- dữ liệu thu thập ---
    context: list[Chunk]  # kết quả RAG (nhánh policy)
    order: dict | None  # kết quả get_order (nhánh order)
    ticket_id: str | None  # kết quả create_complaint (nhánh complaint)
    need_verify: bool  # thiếu mã đơn / 4 số cuối SĐT

    # --- đầu ra ---
    answer: str
    pii_found: bool
    trace: list[str]  # vết các node đã chạy, tiện debug và demo
