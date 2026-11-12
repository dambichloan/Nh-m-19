
"""Execution Rail: validation, approval gate và giới hạn thao tác ghi.

Module này chỉ cấp quyền/đếm quota, không tự thực hiện thao tác DB.
Khi tích hợp production, approval_status phải lấy từ bản ghi duyệt đã xác thực,
không được tin trực tiếp dữ liệu do khách hàng hoặc client gửi lên.
"""
from __future__ import annotations

from threading import Lock
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ExecutionRailError(PermissionError):
    """Lỗi khi thao tác ghi không được Execution Rail cho phép."""


class WriteIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    session_id: str = Field(min_length=1, max_length=128)
    kind: Literal["return", "complaint"]
    order_id: str | None = Field(default=None, max_length=64)
    content: str = Field(min_length=1, max_length=5000)
    action: Literal["create_ticket", "submit_for_approval"]
    decision: Literal["auto_approve", "needs_approval", "reject"]
    approval_status: Literal["pending", "approved", "rejected"] | None = None
    reviewer: str | None = Field(default=None, max_length=128)
    # Mã phê duyệt dùng để đối chiếu với DB/hệ thống duyệt thực tế.
    approval_id: str | None = Field(default=None, max_length=128)

    @field_validator("session_id", "content")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Không được để trống.")
        return value.strip()

    @field_validator("order_id", "reviewer", "approval_id")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_approval_flow(self) -> "WriteIntent":
        if self.action == "submit_for_approval":
            if self.decision != "needs_approval":
                raise ValueError("Chỉ yêu cầu needs_approval mới được đưa vào hàng chờ.")
            if any((self.approval_status, self.reviewer, self.approval_id)):
                raise ValueError("Không truyền thông tin duyệt khi mới gửi yêu cầu.")
            return self

        if self.decision == "reject":
            raise ValueError("Yêu cầu bị từ chối không được tạo phiếu.")

        if self.decision == "auto_approve":
            if any((self.approval_status, self.reviewer, self.approval_id)):
                raise ValueError("Yêu cầu tự động duyệt không cần thông tin duyệt thủ công.")
            return self

        if self.approval_status != "approved":
            raise ValueError("Yêu cầu cần nhân viên duyệt; chưa có trạng thái approved.")
        if not self.reviewer or not self.approval_id:
            raise ValueError("Thiếu reviewer hoặc approval_id để đối chiếu phê duyệt.")
        return self


class SessionWriteLimiter:
    """Giới hạn số thao tác ghi theo session, an toàn khi nhiều luồng cùng truy cập."""

    def __init__(self, max_writes: int = 3) -> None:
        if not isinstance(max_writes, int) or isinstance(max_writes, bool):
            raise TypeError("max_writes phải là số nguyên.")
        if max_writes < 1:
            raise ValueError("max_writes phải lớn hơn hoặc bằng 1.")
        self.max_writes = max_writes
        self._counts: dict[str, int] = {}
        self._lock = Lock()

    def consume(self, session_id: str) -> int:
        if not isinstance(session_id, str) or not session_id.strip():
            raise ExecutionRailError("session_id không hợp lệ.")
        key = session_id.strip()
        with self._lock:
            current = self._counts.get(key, 0)
            if current >= self.max_writes:
                raise ExecutionRailError(
                    f"Phiên {key} đã vượt giới hạn {self.max_writes} thao tác ghi."
                )
            self._counts[key] = current + 1
            return current + 1

    def get_count(self, session_id: str) -> int:
        with self._lock:
            return self._counts.get(session_id, 0)

    def remaining(self, session_id: str) -> int:
        return max(0, self.max_writes - self.get_count(session_id))

    def reset(self, session_id: str | None = None) -> None:
        with self._lock:
            if session_id is None:
                self._counts.clear()
            else:
                self._counts.pop(session_id, None)


DEFAULT_WRITE_LIMIT = 3
_write_limiter = SessionWriteLimiter(DEFAULT_WRITE_LIMIT)


def authorize_write(
    payload: WriteIntent | dict,
    limiter: SessionWriteLimiter | None = None,
    approval_verifier: Callable[[str, str], bool] | None = None,
) -> WriteIntent:
    """Validate payload, xác minh phê duyệt thủ công (nếu có), rồi tiêu quota.

    approval_verifier nhận (approval_id, reviewer), phải truy vấn nguồn dữ liệu
    đáng tin cậy. Không cung cấp verifier thì không cấp quyền cho ca duyệt thủ công.
    """
    intent = payload if isinstance(payload, WriteIntent) else WriteIntent.model_validate(payload)

    if intent.decision == "needs_approval" and intent.action == "create_ticket":
        if approval_verifier is None:
            raise ExecutionRailError("Không có bộ xác minh phê duyệt đáng tin cậy.")
        try:
            verified = approval_verifier(intent.approval_id, intent.reviewer)  # type: ignore[arg-type]
        except Exception as exc:
            raise ExecutionRailError("Không xác minh được trạng thái phê duyệt.") from exc
        if verified is not True:
            raise ExecutionRailError("Phê duyệt không hợp lệ hoặc không tồn tại.")

    (limiter or _write_limiter).consume(intent.session_id)
    return intent


def reset_write_limits(session_id: str | None = None) -> None:
    _write_limiter.reset(session_id)
