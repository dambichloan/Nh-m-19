"""Guardrails. HỢP ĐỒNG:
  input_guard(text) -> GuardResult(blocked, reason)
  output_guard(text) -> (text_đã_xử_lý, pii_found)

Owner: D (Guardrails + Observability)
Bản hiện tại là STUB tối thiểu để demo chạy được. D mở rộng (nhiều mẫu tấn công,
tiếng Việt không dấu, LLM phân loại, kiểm tra format đầu ra bằng Pydantic).
"""
import re
import unicodedata
from typing import NamedTuple


class GuardResult(NamedTuple):
    blocked: bool
    reason: str = ""


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower()


_ATTACK_PATTERNS = [
    (r"(mã|code).{0,20}giảm giá.{0,20}(100|miễn phí|free)", "coupon_abuse"),
    (r"giảm giá\s*100\s*%", "coupon_abuse"),
    (r"ignore (all |the )?(previous|above) instructions", "prompt_injection"),
    (r"bỏ qua (các |mọi )?(hướng dẫn|chỉ dẫn)", "prompt_injection"),
    (r"(system prompt|prompt hệ thống)", "prompt_injection"),
]


def input_guard(text: str) -> GuardResult:
    t = _norm(text)
    for pattern, reason in _ATTACK_PATTERNS:
        if re.search(pattern, t):
            return GuardResult(True, reason)
    return GuardResult(False)


_PHONE_RE = re.compile(r"(?<!\d)(?:\+84|0)(?:[\s.\-]?\d){9}(?!\d)")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def output_guard(text: str) -> tuple[str, bool]:
    masked, n_phone = _PHONE_RE.subn("[SĐT đã ẩn]", text)
    masked, n_mail = _EMAIL_RE.subn("[email đã ẩn]", masked)
    return masked, (n_phone + n_mail) > 0
