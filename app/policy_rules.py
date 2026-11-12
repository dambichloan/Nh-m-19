"""Bộ luật quyết định cho yêu cầu đổi trả / khiếu nại. Cố ý viết bằng CODE, không để LLM quyết định:
dễ kiểm thử, dễ giải thích với giám khảo, và không bị prompt injection thao túng.

Số liệu lấy từ app/config.py, phải khớp data/rules.md.
Kết quả của mỗi hàm là Decision(outcome, reasons):
  auto_approve   -> agent tự tạo phiếu
  needs_approval -> rủi ro / ngoại lệ, dừng chờ nhân viên duyệt
  reject         -> không đủ điều kiện, giải thích lý do cho khách
"""
import re
from dataclasses import dataclass, field
from datetime import date

from app import config

AUTO, NEEDS_APPROVAL, REJECT = "auto_approve", "needs_approval", "reject"

_DEFECT_KW = ("lỗi", "rách", "hỏng", "sai hàng", "giao sai", "thiếu hàng", "bung chỉ", "phai màu", "không đúng mô tả")
_USED_KW = (
    "đã giặt", "đã mặc", "đã sử dụng", "đã dùng", "đã qua sử dụng",
    "giặt rồi", "mặc rồi", "dùng rồi", "cắt tag", "cắt mác",
)
# Không dùng "kiện" trần vì khớp nhầm "điều kiện", "kiện hàng".
_RISK_KW = (
    "khởi kiện", "sẽ kiện", "kiện ra", "ra tòa", "báo chí", "tố cáo", "công an",
    "bóc phốt", "đăng facebook", "luật sư", "bồi thường", "bắt đền", "đền bù",
)
# Cụm phủ định cần bỏ trước khi tìm từ "lỗi": "không lỗi", "chưa bị hỏng", "xin lỗi"
_NEGATED_DEFECT = re.compile(r"(không|chưa|chẳng)\s+(bị\s+)?(lỗi|hỏng|rách)|xin lỗi")
# Nhóm không đổi trả (khớp theo tên sản phẩm)
_NO_RETURN_NAME = re.compile(r"\b(đồ lót|quần lót|áo lót|tất|vớ|quà tặng)\b")


@dataclass
class Decision:
    outcome: str
    reasons: list[str] = field(default_factory=list)


def _has(text: str, words: tuple[str, ...]) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def _has_defect(text: str) -> bool:
    t = _NEGATED_DEFECT.sub(" ", text.lower())
    return any(w in t for w in _DEFECT_KW)


def days_since(iso_date: str | None, today: date) -> int | None:
    if not iso_date:
        return None
    return (today - date.fromisoformat(iso_date)).days


_days_since = days_since  # tên cũ, giữ để không vỡ code/test đang gọi


def _non_returnable_items(order: dict) -> list[str]:
    """Tên sản phẩm thuộc nhóm không đổi trả. items có thể là chuỗi (stub) hoặc dict (bản SQLite)."""
    bad = []
    for it in order.get("items", []):
        if isinstance(it, dict):
            name = str(it.get("name", ""))
            discount = it.get("discount_percent") or 0
        else:
            name, discount = str(it), 0
        if _NO_RETURN_NAME.search(name.lower()) or discount >= 50:
            bad.append(name)
    return bad


def decide_return(order: dict, text: str, today: date, duplicate_ticket: str | None = None) -> Decision:
    """Quyết định cho yêu cầu đổi trả đã xác minh đơn."""
    if duplicate_ticket:
        return Decision(REJECT, [f"đơn này đã có yêu cầu đổi trả đang xử lý ({duplicate_ticket})"])

    status = order.get("status")
    if status == "Đã hủy":
        return Decision(REJECT, ["đơn đã bị hủy"])
    if status != "Đã giao":
        return Decision(REJECT, [f"đơn đang ở trạng thái '{status}', chỉ đổi trả sau khi đã nhận hàng"])

    defect = _has_defect(text)
    used = _has(text, _USED_KW)
    days = days_since(order.get("delivered_at"), today)
    expired = days is not None and days > config.RETURN_WINDOW_DAYS
    no_return = _non_returnable_items(order)

    reasons: list[str] = []
    if no_return:
        if not defect:
            return Decision(REJECT, [f"sản phẩm thuộc nhóm không đổi trả ({', '.join(no_return)})"])
        reasons.append("sản phẩm thuộc nhóm không đổi trả nhưng khách báo lỗi, cần nhân viên kiểm tra")
    if expired:
        if not defect:
            return Decision(REJECT, [f"đã quá {config.RETURN_WINDOW_DAYS} ngày kể từ ngày giao hàng ({days} ngày)"])
        reasons.append(f"quá {config.RETURN_WINDOW_DAYS} ngày ({days} ngày) nhưng khách báo lỗi, cần xem xét ngoại lệ")
    if used:
        if not defect:
            return Decision(REJECT, ["hàng đã giặt hoặc đã qua sử dụng không được đổi trả"])
        reasons.append("khách nói đã giặt/sử dụng nhưng báo lỗi sản phẩm, cần nhân viên kiểm tra")
    if order.get("total_vnd", 0) > config.APPROVAL_THRESHOLD_VND:
        reasons.append(f"đơn giá trị cao ({order['total_vnd']:,}đ), cần nhân viên duyệt")

    return Decision(NEEDS_APPROVAL, reasons) if reasons else Decision(AUTO, ["đủ điều kiện đổi trả"])


def decide_complaint(order: dict | None, text: str) -> Decision:
    """Khiếu nại thường thì tạo phiếu luôn; có dấu hiệu rủi ro thì chờ người duyệt."""
    reasons: list[str] = []
    if _has(text, _RISK_KW):
        reasons.append("nội dung có yêu cầu bồi thường hoặc đe dọa pháp lý/truyền thông")
    if order and order.get("total_vnd", 0) > config.APPROVAL_THRESHOLD_VND:
        reasons.append(f"đơn giá trị cao ({order['total_vnd']:,}đ)")
    return Decision(NEEDS_APPROVAL, reasons) if reasons else Decision(AUTO, ["khiếu nại thông thường"])
