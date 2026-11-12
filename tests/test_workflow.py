"""Test luồng xử lý yêu cầu: tra đơn -> đối chiếu chính sách -> quyết định -> hành động / chờ duyệt."""
import pytest

from app import tools
from app.graph import resolve_approval, run


# ---------- tự xử lý xong ----------
def test_return_auto_approved_creates_ticket():
    s = run("Tôi muốn đổi size áo, đơn #124, SĐT cuối 1111")
    assert s["intent"] == "return" and s["status"] == "completed"
    assert s["ticket_id"].startswith("RT-") and s["ticket_id"] in s["answer"]
    assert s["trace"][-5:] == ["gather", "decide(auto_approve)", "execute", "respond", "output_guard"]
    assert tools.find_open_request("124", "return") == s["ticket_id"]


def test_complaint_normal_creates_ticket_without_approval():
    s = run("Tôi muốn khiếu nại thái độ nhân viên")
    assert s["status"] == "completed" and s["ticket_id"].startswith("TK-")


# ---------- từ chối theo chính sách ----------
@pytest.mark.parametrize("q,reason", [
    ("Tôi muốn trả hàng đơn #125 SĐT cuối 2222", "quá 7 ngày"),
    ("Tôi muốn trả hàng đơn #127 SĐT cuối 4444", "đã bị hủy"),
    ("Tôi muốn trả hàng đơn #123 SĐT cuối 5678", "Đang giao"),
    ("Tôi muốn trả áo đã giặt, đơn #124 SĐT cuối 1111", "đã giặt"),
])
def test_return_rejected_with_reason_and_no_ticket(q, reason):
    s = run(q)
    assert s["status"] == "rejected" and reason in s["answer"]
    assert not s.get("ticket_id") and not tools.list_pending_approvals()


# ---------- rủi ro: dừng chờ nhân viên ----------
def test_high_value_return_waits_for_staff():
    s = run("Tôi muốn trả áo khoác đơn #126 SĐT cuối 3333, size không vừa")
    assert s["status"] == "pending_approval" and s["approval_id"].startswith("AP-")
    assert not s.get("ticket_id")  # chưa tạo phiếu
    assert tools.find_open_request("126", "return") == s["approval_id"]
    assert len(tools.list_pending_approvals()) == 1


def test_expired_but_defective_is_exception_for_staff():
    s = run("Tôi muốn trả hàng đơn #125 SĐT cuối 2222, áo bị rách")
    assert s["status"] == "pending_approval"


def test_legal_threat_complaint_waits_for_staff():
    s = run("Tôi sẽ kiện và báo chí vì đơn #124 giao sai hàng")
    assert s["intent"] == "complaint" and s["status"] == "pending_approval"


def test_staff_approves_then_ticket_created():
    s = run("Tôi muốn trả áo khoác đơn #126 SĐT cuối 3333, size không vừa")
    r = resolve_approval(s["approval_id"], True, reviewer="nv01", note="Liên hệ 0912345678 để nhận hàng.")
    assert r["status"] == "completed" and r["ticket_id"].startswith("RT-")
    assert "0912345678" not in r["message"]  # ghi chú của nhân viên cũng qua output_guard
    assert not tools.list_pending_approvals()


def test_staff_rejects_then_no_ticket():
    s = run("Tôi muốn trả áo khoác đơn #126 SĐT cuối 3333, size không vừa")
    r = resolve_approval(s["approval_id"], False, reviewer="nv01", note="Hàng có dấu hiệu đã dùng.")
    assert r["status"] == "rejected" and r["ticket_id"] is None


def test_cannot_resolve_twice():
    s = run("Tôi muốn trả áo khoác đơn #126 SĐT cuối 3333")
    resolve_approval(s["approval_id"], True, "nv01")
    with pytest.raises(ValueError):
        resolve_approval(s["approval_id"], True, "nv02")


# ---------- an toàn ----------
def test_return_without_phone_asks_for_verification():
    s = run("Tôi muốn đổi hàng đơn #124")
    assert s["status"] == "need_info" and "4 số cuối" in s["answer"]
    assert "decide(auto_approve)" not in s["trace"] and not s.get("ticket_id")


def test_return_wrong_phone_does_not_leak_order():
    s = run("Tôi muốn trả hàng đơn #124 SĐT cuối 9999")
    assert s["status"] == "need_info" and "Quần jeans" not in s["answer"] and not s.get("ticket_id")


def test_duplicate_return_is_rejected():
    run("Tôi muốn đổi size áo, đơn #124, SĐT cuối 1111")
    s = run("Tôi muốn đổi size áo, đơn #124, SĐT cuối 1111")
    assert s["status"] == "rejected" and "đang xử lý" in s["answer"]


def test_information_questions_do_not_create_anything():
    for q in ["Áo đã giặt có đổi được không?", "Đơn #123 đang ở đâu? SĐT cuối 5678"]:
        s = run(q)
        assert s["status"] == "answered" and not s.get("ticket_id") and not s.get("approval_id")
    assert not tools.list_pending_approvals()
