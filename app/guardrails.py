
"""Guardrails: kiểm soát đầu vào và bảo vệ thông tin cá nhân đầu ra.

Contract:
    input_guard(text: str) -> GuardResult
    output_guard(text: str) -> tuple[str, bool]

Owner: D - Guardrails + Observability

input_guard chuẩn hóa văn bản tiếng Việt trước khi nhận diện
các mẫu prompt injection và lạm dụng mã giảm giá.

output_guard che số điện thoại, email và địa chỉ phổ biến tại Việt Nam.
Đây là cơ chế nhận diện theo mẫu, không đảm bảo phát hiện mọi dạng PII.
"""

import re
import unicodedata
from typing import NamedTuple


class GuardResult(NamedTuple):
    blocked: bool
    reason: str = ""


def _norm(text: str) -> str:
    """Chuyển chữ thường và loại bỏ dấu tiếng Việt."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )
    return text.replace("đ", "d")


# Các mẫu nhận diện đầu vào không an toàn.
# Các mẫu được so khớp trên văn bản đã chuẩn hóa.
_ATTACK_PATTERNS = [
    # Lạm dụng mã giảm giá.
    (
        r"\b(?:ma|code|voucher|coupon)\b"
        r".{0,30}\bgiam gia\b.{0,30}"
        r"(?:100\s*%?|mien phi|free)(?=$|\W)",
        "coupon_abuse",
    ),
    (
        r"\bgiam gia\s*100\s*%",
        "coupon_abuse",
    ),
    (
        r"\b(?:cap|tang|cho)\b"
        r".{0,15}\b(?:ma|code)\b"
        r".{0,15}\bgiam gia\b",
        "coupon_abuse",
    ),

    # Prompt injection bằng tiếng Anh.
    (
        r"\bignore\b.{0,40}"
        r"\b(?:all|the|your|previous|above|prior)\b"
        r".{0,20}\b(?:instructions?|rules)\b",
        "prompt_injection",
    ),
    (
        r"\bdisregard\b.{0,30}\b(?:instructions?|rules)\b",
        "prompt_injection",
    ),
    (
        r"\bforget\b.{0,20}\b(?:all|everything|your)\b",
        "prompt_injection",
    ),
    (
        r"\byou are now\b",
        "prompt_injection",
    ),

    # Prompt injection bằng tiếng Việt.
    (
        r"\bbo qua\b.{0,30}"
        r"\b(?:cac|moi|toan bo)?\s*"
        r"(?:huong dan|chi dan|quy tac|quy dinh)\b",
        "prompt_injection",
    ),
    (
        r"\b(?:reveal|show|print|expose|tiet lo|in ra)\b"
        r".{0,30}"
        r"\b(?:system prompt|prompt he thong|instructions?|hidden instructions)\b",
        "prompt_injection",
    ),
    (
        r"\b(?:system prompt|prompt he thong)\b",
        "prompt_injection",
    ),
    (
        r"\b(?:dong vai|gia vo|act as)\b"
        r".{0,25}"
        r"\b(?:admin|quan tri|nhan vien|developer)\b",
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
# 0xxxxxxxxx hoặc +84xxxxxxxxx, cho phép dấu cách, dấu chấm, dấu gạch nối.
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+84|0)(?:[\s.\-]?\d){9}(?!\d)"
)

# Nhận diện email thông dụng.
_EMAIL_RE = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.-]+"
)

# Nhận diện địa chỉ đường/phố/ngõ phổ biến tại Việt Nam.
_STREET_RE = re.compile(
    r"(?:số\s*)?\d+[A-Za-z]?(?:/\d+)*\s*"
    r"(?:đường|phố|ngõ|ngách|hẻm|đ\.)\s+[^,.;\n]{1,40}"
    r"(?:,\s*(?:phường|xã|quận|huyện|thành phố|tp\.?|tỉnh|p\.|q\.)"
    r"\s*[^,.;\n]{1,30}){0,3}",
    re.IGNORECASE,
)

# Nhận diện tên đơn vị hành chính khi xuất hiện độc lập.
_ADMIN_RE = re.compile(
    r"(?:phường|xã|quận|huyện)\s+[^,.;\n]{1,30}"
    r"(?:,\s*(?:quận|huyện|thành phố|tp\.?|tỉnh)"
    r"\s*[^,.;\n]{1,30}){0,2}",
    re.IGNORECASE,
)


def output_guard(text: str) -> tuple[str, bool]:
    """Che thông tin cá nhân trước khi trả kết quả cho người dùng."""

    if not isinstance(text, str):
        return "", False

    masked, n_phone = _PHONE_RE.subn(
        "[SĐT đã ẩn]",
        text,
    )

    masked, n_email = _EMAIL_RE.subn(
        "[email đã ẩn]",
        masked,
    )

    masked, n_street = _STREET_RE.subn(
        "[địa chỉ đã ẩn]",
        masked,
    )

    masked, n_admin = _ADMIN_RE.subn(
        "[địa chỉ đã ẩn]",
        masked,
    )

    pii_found = (
        n_phone + n_email + n_street + n_admin
    ) > 0

    return masked, pii_found
