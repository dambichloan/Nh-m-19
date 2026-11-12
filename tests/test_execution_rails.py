
import pytest
from pydantic import ValidationError

from app.execution_rails import (
    ExecutionRailError,
    SessionWriteLimiter,
    WriteIntent,
    authorize_write,
    reset_write_limits,
)


@pytest.fixture(autouse=True)
def reset_default_limiter():
    """Đảm bảo mỗi test bắt đầu với bộ đếm mặc định sạch."""
    reset_write_limits()
    yield
    reset_write_limits()


def make_payload(**overrides):
    payload = {
        "session_id": "session-001",
        "kind": "return",
        "order_id": "124",
        "content": "Khách yêu cầu đổi trả sản phẩm.",
        "action": "create_ticket",
        "decision": "auto_approve",
    }
    payload.update(overrides)
    return payload


# =========================================================
# 1. KIỂM TRA CÁC TRƯỜNG HỢP TẠO PHIẾU HỢP LỆ
# =========================================================

def test_auto_approved_return_can_create_ticket():
    intent = authorize_write(make_payload())

    assert intent.kind == "return"
    assert intent.action == "create_ticket"
    assert intent.decision == "auto_approve"


def test_normal_complaint_can_create_ticket():
    intent = authorize_write(
        make_payload(
            kind="complaint",
            order_id=None,
            action="create_ticket",
            decision="auto_approve",
        )
    )

    assert intent.kind == "complaint"


def test_high_risk_request_can_enter_approval_queue():
    intent = authorize_write(
        make_payload(
            action="submit_for_approval",
            decision="needs_approval",
        )
    )

    assert intent.action == "submit_for_approval"
    assert intent.decision == "needs_approval"


# =========================================================
# 2. KIỂM TRA QUY TRÌNH PHÊ DUYỆT
# =========================================================

def test_high_risk_request_cannot_create_ticket_before_approval():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(decision="needs_approval")
        )


def test_manually_approved_request_can_create_ticket():
    payload = make_payload(
        decision="needs_approval",
        approval_status="approved",
        reviewer="staff-01",
        approval_id="AP-0001",
    )

    intent = authorize_write(
        payload,
        approval_verifier=lambda approval_id, reviewer: (
            approval_id == "AP-0001"
            and reviewer == "staff-01"
        ),
    )

    assert intent.approval_status == "approved"
    assert intent.reviewer == "staff-01"
    assert intent.approval_id == "AP-0001"


def test_manually_approved_request_requires_reviewer():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(
                decision="needs_approval",
                approval_status="approved",
                approval_id="AP-0001",
            )
        )


def test_manually_approved_request_requires_approval_id():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(
                decision="needs_approval",
                approval_status="approved",
                reviewer="staff-01",
            )
        )


def test_manual_approval_requires_trusted_verifier():
    with pytest.raises(ExecutionRailError):
        authorize_write(
            make_payload(
                decision="needs_approval",
                approval_status="approved",
                reviewer="staff-01",
                approval_id="AP-0001",
            )
        )


def test_invalid_approval_is_rejected():
    with pytest.raises(ExecutionRailError):
        authorize_write(
            make_payload(
                decision="needs_approval",
                approval_status="approved",
                reviewer="staff-01",
                approval_id="AP-9999",
            ),
            approval_verifier=lambda *_: False,
        )


def test_rejected_request_cannot_create_ticket():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(decision="reject")
        )


def test_rejected_request_cannot_enter_approval_queue():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(
                action="submit_for_approval",
                decision="reject",
            )
        )


def test_pending_request_cannot_create_ticket():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(
                decision="needs_approval",
                approval_status="pending",
            )
        )


def test_approval_verifier_exception_is_rejected():
    def broken_verifier(*_):
        raise RuntimeError("Approval database unavailable")

    with pytest.raises(ExecutionRailError):
        authorize_write(
            make_payload(
                decision="needs_approval",
                approval_status="approved",
                reviewer="staff-01",
                approval_id="AP-0001",
            ),
            approval_verifier=broken_verifier,
        )


# =========================================================
# 3. KIỂM TRA VALIDATION DỮ LIỆU
# =========================================================

def test_blank_content_is_rejected():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(content="   ")
        )


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(is_admin=True)
        )


def test_missing_session_id_is_rejected():
    payload = make_payload()
    payload.pop("session_id")

    with pytest.raises(ValidationError):
        authorize_write(payload)


def test_invalid_kind_is_rejected():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(kind="delete_order")
        )


def test_invalid_action_is_rejected():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(action="delete")
        )


def test_invalid_decision_is_rejected():
    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(decision="allow_everything")
        )


def test_empty_content_does_not_consume_write_limit():
    limiter = SessionWriteLimiter(max_writes=1)

    with pytest.raises(ValidationError):
        authorize_write(
            make_payload(content=""),
            limiter=limiter,
        )

    assert limiter.get_count("session-001") == 0


# =========================================================
# 4. KIỂM TRA GIỚI HẠN THAO TÁC GHI
# =========================================================

def test_write_limit_blocks_fourth_write_in_same_session():
    limiter = SessionWriteLimiter(max_writes=3)

    for _ in range(3):
        authorize_write(
            make_payload(),
            limiter=limiter,
        )

    with pytest.raises(ExecutionRailError):
        authorize_write(
            make_payload(),
            limiter=limiter,
        )

    assert limiter.get_count("session-001") == 3


def test_different_sessions_have_independent_limits():
    limiter = SessionWriteLimiter(max_writes=1)

    authorize_write(
        make_payload(session_id="session-A"),
        limiter=limiter,
    )

    authorize_write(
        make_payload(session_id="session-B"),
        limiter=limiter,
    )

    assert limiter.get_count("session-A") == 1
    assert limiter.get_count("session-B") == 1


def test_invalid_approval_does_not_consume_write_limit():
    limiter = SessionWriteLimiter(max_writes=1)

    with pytest.raises(ExecutionRailError):
        authorize_write(
            make_payload(
                decision="needs_approval",
                approval_status="approved",
                reviewer="staff-01",
                approval_id="AP-9999",
            ),
            limiter=limiter,
            approval_verifier=lambda *_: False,
        )

    assert limiter.get_count("session-001") == 0


def test_invalid_write_limit_is_rejected():
    with pytest.raises(ValueError):
        SessionWriteLimiter(max_writes=0)


def test_negative_write_limit_is_rejected():
    with pytest.raises(ValueError):
        SessionWriteLimiter(max_writes=-1)


def test_write_limit_remaining():
    limiter = SessionWriteLimiter(max_writes=3)

    assert limiter.remaining("session-001") == 3

    authorize_write(
        make_payload(),
        limiter=limiter,
    )

    assert limiter.remaining("session-001") == 2


# =========================================================
# 5. KIỂM TRA RESET BỘ ĐẾM
# =========================================================

def test_reset_one_session_does_not_reset_other_sessions():
    limiter = SessionWriteLimiter(max_writes=2)

    authorize_write(
        make_payload(session_id="session-A"),
        limiter=limiter,
    )

    authorize_write(
        make_payload(session_id="session-B"),
        limiter=limiter,
    )

    limiter.reset("session-A")

    assert limiter.get_count("session-A") == 0
    assert limiter.get_count("session-B") == 1


def test_reset_all_sessions():
    limiter = SessionWriteLimiter(max_writes=2)

    authorize_write(
        make_payload(session_id="session-A"),
        limiter=limiter,
    )

    authorize_write(
        make_payload(session_id="session-B"),
        limiter=limiter,
    )

    limiter.reset()

    assert limiter.get_count("session-A") == 0
    assert limiter.get_count("session-B") == 0


def test_reset_default_write_limits():
    authorize_write(make_payload())

    assert reset_write_limits() is None

    # Sau reset, session có thể thực hiện thao tác tiếp theo.
    intent = authorize_write(make_payload())
    assert intent.session_id == "session-001"


def test_write_limiter_rejects_invalid_max_writes_type():
    with pytest.raises(TypeError):
        SessionWriteLimiter(max_writes=1.5)
