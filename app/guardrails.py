
"""Guardrails: kiểm soát đầu vào và bảo vệ thông tin cá nhân đầu ra.

Contract:
    input_guard(text: str) -> GuardResult
    output_guard(text: str) -> tuple[str, bool]

Owner: D - Guardrails + Observability
"""

import re
import unicodedata
from typing import NamedTuple


class GuardResult(NamedTuple):
    blocked: bool
    reason: str = ""


def _norm(text: str) -> str:
    """Chuẩn hóa chữ thường, bỏ dấu tiếng Việt để nhận diện nội dung."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )
    return text.replace("đ", "d")


# Các mẫu nhận diện đầu vào không an toàn.
# Đây là bộ lọc theo mẫu, không phải cơ chế phát hiện mọi kiểu tấn công.
_ATTACK_PATTERNS = [
    (
        r"\b(?:ma|code)\b.{0,30}\bgiam gia\b.{0,30}"
        r"(?:100\s*%?|mien phi|free)(?=$|\W)",
        "coupon_abuse",
    ),
    (
        r"\bgiam gia\s*100\s*%",
        "coupon_abuse",
    ),
    (
        r"\bignore\b.{0,40}\b(?:all|previous|above)\b"
        r".{0,20}\binstructions?\b",
        "prompt_injection",
    ),
    (
        r"\bbo qua\b.{0,30}\b(?:cac|moi|toan bo)\b"
        r".{0,20}\b(?:huong dan|chi dan|quy tac)\b",
        "prompt_injection",
    ),
    (
        r"\bbo qua\b.{0,20}\b(?:huong dan|chi dan|quy tac)\b",
        "prompt_injection",
    ),
    (
        r"\b(?:system prompt|prompt he thong)\b",
        "prompt_injection",
    ),
    (
        r"\b(?:reveal|show|print|expose)\b.{0,30}"
        r"\b(?:system prompt|hidden instructions)\b",
        "prompt_injection",
    ),
]


def input_guard(text: str) -> GuardResult:
    """Kiểm tra đầu vào trước khi chuyển sang node phân loại."""
    if not isinstance(text, str):
        return GuardResult(True, "invalid_input")

    if not text.strip():
        return GuardResult(True, "empty_input")

    normalized_text = _norm(text)

    for pattern, reason in _ATTACK_PATTERNS:
        if re.search(pattern, normalized_text):
            return GuardResult(True, reason)

    return GuardResult(False, "")


# Nhận diện số điện thoại Việt Nam:
# 0xxxxxxxxx hoặc +84xxxxxxxxx, cho phép dấu cách/dấu chấm/dấu gạch nối.
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+84|0)(?:[\s.-]?\d){9}(?!\d)"
)

# Nhận diện email thông dụng.
_EMAIL_RE = re.compile(
    r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
)


def output_guard(text: str) -> tuple[str, bool]:
    """Che số điện thoại và email trước khi trả kết quả."""
    if not isinstance(text, str):
        return "", False

    masked, phone_count = _PHONE_RE.subn(
        "[SĐT đã ẩn]",
        text,
    )

    masked, email_count = _EMAIL_RE.subn(
        "[email đã ẩn]",
        masked,
    )

    pii_found = (phone_count + email_count) > 0

    return masked, pii_found
