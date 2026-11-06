"""Lớp LLM. HỢP ĐỒNG:
  classify_intent(question) -> IntentResult
  generate_answer(question, intent, context, order, ticket_id) -> str

Owner: A (Tech lead)
LLM_PROVIDER=stub dùng luật từ khóa, chạy offline, không tốn API.
TODO(A): cài nhánh gemini/openai với structured output (Pydantic) cho classify_intent.
"""
import re

from pydantic import BaseModel

from app import config
from app.state import Chunk, Intent


class IntentResult(BaseModel):
    intent: Intent
    order_id: str | None = None
    phone_last4: str | None = None


# ---------- trích xuất ----------
_ORDER_RE = re.compile(r"(?:#|đơn(?: hàng)?\s*(?:số\s*)?)(\d{2,})", re.IGNORECASE)
_PHONE4_RE = re.compile(r"(?:sđt|số điện thoại|sdt|4 số cuối)[^\d]{0,20}(\d{4})(?!\d)", re.IGNORECASE)

_COMPLAINT_KW = ("khiếu nại", "phàn nàn", "giao sai", "hàng lỗi", "bị hỏng", "không hài lòng", "thiếu hàng")
_ORDER_KW = ("đang ở đâu", "trạng thái", "khi nào giao", "bao giờ giao", "tra đơn", "đơn hàng")
_POLICY_KW = ("đổi", "trả", "hoàn tiền", "bảo hành", "size", "vận chuyển", "giao hàng", "phí", "giặt", "chính sách")


def _stub_classify(question: str) -> IntentResult:
    q = question.lower()
    m = _ORDER_RE.search(question)
    p = _PHONE4_RE.search(question)
    order_id = m.group(1) if m else None
    phone4 = p.group(1) if p else None

    if any(k in q for k in _COMPLAINT_KW):
        intent: Intent = "complaint"
    elif order_id or any(k in q for k in _ORDER_KW):
        intent = "order"
    elif any(k in q for k in _POLICY_KW):
        intent = "policy"
    else:
        intent = "other"
    return IntentResult(intent=intent, order_id=order_id, phone_last4=phone4)


def classify_intent(question: str) -> IntentResult:
    if config.LLM_PROVIDER == "stub":
        return _stub_classify(question)
    raise NotImplementedError("TODO(A): classify_intent bằng LLM + structured output")


def generate_answer(
    question: str,
    intent: Intent,
    context: list[Chunk] | None = None,
    order: dict | None = None,
    ticket_id: str | None = None,
) -> str:
    if config.LLM_PROVIDER != "stub":
        raise NotImplementedError("TODO(A): generate_answer bằng LLM, prompt chỉ dựa trên context/order")

    if intent == "policy" and context:
        c = context[0]
        return f"{c['text']} (nguồn: {c['source']})"
    if intent == "order" and order:
        items = ", ".join(order["items"])
        return f"Đơn #{order['order_id']} ({items}) đang ở trạng thái: {order['status']}. Dự kiến: {order['eta']}."
    if intent == "complaint" and ticket_id:
        return f"Mình đã ghi nhận khiếu nại của bạn (mã ticket {ticket_id}). Nhân viên sẽ liên hệ trong 24 giờ."
    return config.MSG_NO_INFO
