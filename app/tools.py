"""Công cụ nghiệp vụ. HỢP ĐỒNG:
  get_order(order_id, phone_last4) -> dict | None
  create_complaint(order_id, content) -> str   (ticket_id)

Owner: C (Tools + UI)
Bản hiện tại là STUB dùng dict trong bộ nhớ. C thay bằng SQLite (câu lệnh tham số hóa).

Quy tắc bảo mật: get_order trả None cả khi "không có đơn" lẫn khi "sai 4 số cuối SĐT",
để không lộ việc mã đơn đó có tồn tại hay không.
"""
import itertools

from app import config

_STUB_ORDERS = {
    "123": {
        "order_id": "123",
        "phone_last4": "5678",
        "status": "Đang giao",
        "items": ["Áo thun basic (M)"],
        "eta": "2026-11-08",
    },
    "124": {
        "order_id": "124",
        "phone_last4": "1111",
        "status": "Đã giao",
        "items": ["Quần jeans (L)"],
        "eta": "2026-11-01",
    },
}
_ticket_counter = itertools.count(1)


def get_order(order_id: str, phone_last4: str | None) -> dict | None:
    order = _STUB_ORDERS.get(str(order_id).lstrip("#"))
    if order is None:
        return None
    if config.REQUIRE_PHONE_VERIFY and order["phone_last4"] != phone_last4:
        return None
    # Không trả phone_last4 ra ngoài
    return {k: v for k, v in order.items() if k != "phone_last4"}


def create_complaint(order_id: str | None, content: str) -> str:
    return f"TK-{next(_ticket_counter):04d}"
