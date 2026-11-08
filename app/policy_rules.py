"""Bộ luật quyết định cho yêu cầu đổi trả / khiếu nại. Cố ý viết bằng CODE, không để LLM quyết định:
dễ kiểm thử, dễ giải thích với giám khảo, và không bị prompt injection thao túng.

Owner: A (Tech lead) viết khung; B xác nhận số liệu khớp file chính sách.
Kết quả của mỗi hàm là Decision(outcome, reasons):
  auto_approve   -> agent tự tạo phiếu
  needs_approval -> rủi ro / ngoại lệ, dừng chờ nhân viên duyệt
  reject         -> không đủ điều kiện, giải thích lý do cho khách
"""
from dataclasses import dataclass, field
from datetime import date

from app import config

AUTO, NEEDS_APPROVAL, REJECT = "auto_approve", "needs_approval", "reject"

_DEFECT_KW = ("lỗi", "rách", "hỏng", "sai hàng", "giao sai", "thiếu hàng", "bung chỉ", "phai màu", "không đúng mô tả")
_USED_KW = ("đã giặt", "đã mặc", "đã sử dụng", "đã dùng", "đã qua sử dụng")
_RISK_KW = ("kiện", "báo chí", "tố cáo", "công an", "bóc phốt", "đăng facebook", "luật sư", "bồi thường", "đền")


@dataclass
class Decision:
    outcome: str
    reasons: list[str] = field(default_factory=list)


def _has(text: str, words: tuple[str, ...]) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def _days_since(iso_date: str | None, today: date) -> int | None:
    if not iso_date:
        return None
    return (today - date.fromisoformat(iso_date)).days


def decide_return(order: dict, text: str, today: date, duplicate_ticket: str | None = None) -> Decision:
    """Quyết định cho yêu cầu đổi trả đã xác minh đơn."""
    if duplicate_ticket:
        return Decision(REJECT, [f"đơn này đã có yêu cầu đổi trả đang xử lý ({duplicate_ticket})"])

    status = order.get("status")
    if status == "Đã hủy":
        return Decision(REJECT, ["đơn đã bị hủy"])
    if status != "Đã giao":
        return Decision(REJECT, [f"đơn đang ở trạng thái '{status}', chỉ đổi trả sau khi đã nhận hàng"])

    defect = _has(text, _DEFECT_KW)
    used = _has(text, _USED_KW)
    days = _days_since(order.get("delivered_at"), today)
    expired = days is not None and days > config.RETURN_WINDOW_DAYS

    reasons: list[str] = []
    if expired:
        if not defect:
            return Decision(REJECT, [f"đã quá {config.RETURN_WINDOW_DAYS} ngày kể từ khi nhận hàng ({days} ngày)"])
        reasons.append(f"quá {config.RETURN_WINDOW_DAYS} ngày ({days} ngày) nhưng khách báo lỗi, cần xem xét ngoại lệ")
    if used:
        if not defect:
            return Decision(REJECT, ["hàng đã giặt hoặc đã qua sử dụng không được đổi trả"])
        reasons.append("khách nói đã giặt/sử dụng nhưng báo lỗi sản phẩm, cần nhân viên kiểm tra")
    if order.get("total_vnd", 0) >= config.APPROVAL_THRESHOLD_VND:
        reasons.append(f"đơn giá trị cao ({order['total_vnd']:,}đ), cần nhân viên duyệt")

    return Decision(NEEDS_APPROVAL, reasons) if reasons else Decision(AUTO, ["đủ điều kiện đổi trả"])


def decide_complaint(order: dict | None, text: str) -> Decision:
    """Khiếu nại thường thì tạo phiếu luôn; có dấu hiệu rủi ro thì chờ người duyệt."""
    reasons: list[str] = []
    if _has(text, _RISK_KW):
        reasons.append("nội dung có yêu cầu bồi thường hoặc đe dọa pháp lý/truyền thông")
    if order and order.get("total_vnd", 0) >= config.APPROVAL_THRESHOLD_VND:
        reasons.append(f"đơn giá trị cao ({order['total_vnd']:,}đ)")
    return Decision(NEEDS_APPROVAL, reasons) if reasons else Decision(AUTO, ["khiếu nại thông thường"])
