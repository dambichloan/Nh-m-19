"""Công cụ nghiệp vụ. HỢP ĐỒNG:
  get_order(order_id, phone_last4) -> dict | None
  create_complaint(order_id, content) -> str          (ticket_id, dạng TK-0001)
  create_return(order_id, content) -> str             (ticket_id, dạng RT-0001)
  find_open_request(order_id, kind) -> str | None     (mã phiếu/duyệt đang mở, chống tạo trùng)
  submit_for_approval(kind, order_id, content, reasons) -> str   (approval_id, dạng AP-0001)
  list_pending_approvals() -> list[dict]
  resolve_approval(approval_id, approve, reviewer, note) -> dict (nếu duyệt thì TỰ tạo phiếu)

Owner: C (Tools + UI)
Bản hiện tại là STUB dùng dict trong bộ nhớ. C thay bằng SQLite (câu lệnh tham số hóa),
GIỮ NGUYÊN chữ ký, thêm bảng: orders, tickets, approvals. Tests gọi reset_state() trước mỗi test.

Quy tắc bảo mật: get_order trả None cả khi "không có đơn" lẫn khi "sai 4 số cuối SĐT",
để không lộ việc mã đơn đó có tồn tại hay không.
"""
import itertools

from app import config

# Đơn mẫu phủ các tình huống demo (hôm nay giả định 2026-11-08, hạn đổi trả 7 ngày):
#   123 đang giao | 124 mới giao, giá thấp | 125 giao quá 7 ngày | 126 mới giao, giá cao | 127 đã hủy
_STUB_ORDERS = {
    "123": {"order_id": "123", "phone_last4": "5678", "status": "Đang giao", "items": ["Áo thun basic (M)"],
            "eta": "2026-11-08", "delivered_at": None, "total_vnd": 199_000},
    "124": {"order_id": "124", "phone_last4": "1111", "status": "Đã giao", "items": ["Quần jeans (L)"],
            "eta": "2026-11-05", "delivered_at": "2026-11-05", "total_vnd": 450_000},
    "125": {"order_id": "125", "phone_last4": "2222", "status": "Đã giao", "items": ["Áo sơ mi (M)"],
            "eta": "2026-10-20", "delivered_at": "2026-10-20", "total_vnd": 350_000},
    "126": {"order_id": "126", "phone_last4": "3333", "status": "Đã giao", "items": ["Áo khoác da (L)"],
            "eta": "2026-11-06", "delivered_at": "2026-11-06", "total_vnd": 2_400_000},
    "127": {"order_id": "127", "phone_last4": "4444", "status": "Đã hủy", "items": ["Váy hoa (S)"],
            "eta": None, "delivered_at": None, "total_vnd": 520_000},
}

_TICKETS: dict[str, dict] = {}
_APPROVALS: dict[str, dict] = {}
_counters: dict[str, "itertools.count[int]"] = {}


def reset_state() -> None:
    """Xóa phiếu và hàng chờ duyệt (dùng cho test / eval)."""
    _TICKETS.clear()
    _APPROVALS.clear()
    _counters.clear()


def _next_id(prefix: str) -> str:
    c = _counters.setdefault(prefix, itertools.count(1))
    return f"{prefix}-{next(c):04d}"


# ---------- tra đơn ----------
def get_order(order_id: str, phone_last4: str | None) -> dict | None:
    order = _STUB_ORDERS.get(str(order_id).lstrip("#"))
    if order is None:
        return None
    if config.REQUIRE_PHONE_VERIFY and order["phone_last4"] != phone_last4:
        return None
    # Không trả phone_last4 ra ngoài
    return {k: v for k, v in order.items() if k != "phone_last4"}


# ---------- tạo phiếu ----------
def _create_ticket(prefix: str, kind: str, order_id: str | None, content: str) -> str:
    tid = _next_id(prefix)
    _TICKETS[tid] = {"id": tid, "kind": kind, "order_id": order_id, "content": content, "status": "open"}
    return tid


def create_complaint(order_id: str | None, content: str) -> str:
    return _create_ticket("TK", "complaint", order_id, content)


def create_return(order_id: str | None, content: str) -> str:
    return _create_ticket("RT", "return", order_id, content)


def find_open_request(order_id: str | None, kind: str) -> str | None:
    """Mã phiếu hoặc mã chờ duyệt đang mở cùng đơn, cùng loại. Dùng để không tạo trùng."""
    if not order_id:
        return None
    for t in _TICKETS.values():
        if t["kind"] == kind and t["order_id"] == order_id and t["status"] == "open":
            return t["id"]
    for a in _APPROVALS.values():
        if a["kind"] == kind and a["order_id"] == order_id and a["status"] == "pending":
            return a["id"]
    return None


# ---------- hàng chờ nhân viên duyệt ----------
def submit_for_approval(kind: str, order_id: str | None, content: str, reasons: list[str]) -> str:
    aid = _next_id("AP")
    _APPROVALS[aid] = {"id": aid, "kind": kind, "order_id": order_id, "content": content,
                       "reasons": list(reasons), "status": "pending",
                       "ticket_id": None, "reviewer": None, "note": ""}
    return aid


def list_pending_approvals() -> list[dict]:
    return [dict(a) for a in _APPROVALS.values() if a["status"] == "pending"]


def resolve_approval(approval_id: str, approve: bool, reviewer: str, note: str = "") -> dict:
    """Nhân viên duyệt hoặc từ chối. Duyệt thì tạo phiếu đúng loại. Không duyệt hai lần."""
    a = _APPROVALS.get(approval_id)
    if a is None:
        raise KeyError(f"Không có yêu cầu chờ duyệt {approval_id}")
    if a["status"] != "pending":
        raise ValueError(f"{approval_id} đã được xử lý ({a['status']})")
    if approve:
        creator = create_return if a["kind"] == "return" else create_complaint
        a["ticket_id"] = creator(a["order_id"], a["content"])
        a["status"] = "approved"
    else:
        a["status"] = "rejected"
    a["reviewer"], a["note"] = reviewer, note
    return dict(a)
