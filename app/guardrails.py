
"""Guardrails: kiểm soát đầu vào, dữ liệu không đáng tin cậy và PII đầu ra.

Contract giữ nguyên:
    input_guard(text: str) -> GuardResult
    output_guard(text: str) -> tuple[str, bool]

Các hàm bổ sung:
    untrusted_text_guard(text) -> GuardResult
    prepare_untrusted_text(text) -> tuple[str, bool]

Lưu ý: nhận diện theo mẫu là lớp phòng vệ bổ sung, không thay thế phân quyền,
prompt separation, kiểm tra nguồn dữ liệu hoặc human approval.
"""
from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple


class GuardResult(NamedTuple):
    blocked: bool
    reason: str = ""


def _norm(text: str) -> str:
    """Chuẩn hóa chữ thường, dấu tiếng Việt và ký tự Unicode tổ hợp."""
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace("đ", "d")


# Dùng các pattern có khoảng cách linh hoạt để nhận diện câu lệnh tấn công.
_ATTACK_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:ma|code|voucher|coupon)\b.{0,40}\b(?:giam gia|discount)\b.{0,30}(?:100\s*%?|mien phi|free)", "coupon_abuse"),
    (r"\bgiam gia\s*100\s*%", "coupon_abuse"),
    (r"\b(?:cap|tang|cho)\b.{0,20}\b(?:ma|code|voucher)\b.{0,20}\b(?:giam gia|discount)\b", "coupon_abuse"),

    (r"\bignore\b.{0,60}\b(?:all|the|your|previous|above|prior)\b.{0,30}\b(?:instructions?|rules|prompts?)\b", "prompt_injection"),
    (r"\bdisregard\b.{0,40}\b(?:all\s+)?(?:instructions?|rules|policies|prompts?)\b", "prompt_injection"),
    (r"\bforget\b.{0,30}\b(?:all|everything|your|previous)\b", "prompt_injection"),
    (r"\byou are now\b|\bact as\b.{0,40}\b(?:admin|developer|system|root)\b", "prompt_injection"),
    (r"\b(?:reveal|show|print|expose|output)\b.{0,40}\b(?:system prompt|hidden prompt|instructions?)\b", "prompt_injection"),
    (r"\b(?:system prompt|hidden instructions|developer message)\b", "prompt_injection"),

    (r"\bbo qua\b.{0,50}\b(?:huong dan|chi dan|quy tac|quy dinh|lenh he thong)\b", "prompt_injection"),
    (r"\b(?:tiet lo|in ra|hien thi|trich xuat)\b.{0,40}\b(?:system prompt|prompt he thong|huong dan an|chi dan he thong)\b", "prompt_injection"),
    (r"\b(?:dong vai|gia vo)\b.{0,35}\b(?:admin|quan tri|developer|he thong|nhan vien)\b", "prompt_injection"),
    (r"\b(?:tu bay gio|ke tu bay gio)\b.{0,40}\b(?:bo qua|khong can tuan theo|vo hieu)\b", "prompt_injection"),
)


def _detect_attack(text: str) -> str | None:
    normalized = _norm(text)
    for pattern, reason in _ATTACK_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE | re.DOTALL):
            return reason
    # Bắt một số biến thể chèn dấu phân cách giữa các từ khóa.
    compact = re.sub(r"[\W_]+", " ", normalized)
    compact = re.sub(r"\s+", " ", compact).strip()
    if re.search(r"\bignore all previous instructions\b", compact):
        return "prompt_injection"
    if re.search(r"\bbo qua tat ca huong dan\b", compact):
        return "prompt_injection"
    return None


def input_guard(text: str) -> GuardResult:
    """Chặn đầu vào rỗng, sai kiểu hoặc có dấu hiệu tấn công đã biết."""
    if not isinstance(text, str):
        return GuardResult(True, "invalid_input")
    if not text.strip():
        return GuardResult(True, "empty_input")
    reason = _detect_attack(text)
    return GuardResult(True, reason) if reason else GuardResult(False, "")


def untrusted_text_guard(text: str) -> GuardResult:
    """Kiểm tra văn bản lấy từ đơn hàng/RAG/ticket trước khi đưa vào ngữ cảnh LLM."""
    if not isinstance(text, str):
        return GuardResult(True, "invalid_untrusted_text")
    if not text.strip():
        return GuardResult(False, "")
    reason = _detect_attack(text)
    return GuardResult(True, reason) if reason else GuardResult(False, "")


def prepare_untrusted_text(text: str) -> tuple[str, bool]:
    """Không xóa dữ liệu gốc; đánh dấu rõ văn bản nghi vấn để tầng gọi quyết định loại bỏ."""
    result = untrusted_text_guard(text)
    if result.blocked:
        return "[NỘI DUNG KHÔNG ĐƯỢC TIN CẬY ĐÃ BỊ LOẠI BỎ]", True
    # Rào delimiter đơn giản để nội dung không tự đóng thẻ dữ liệu.
    safe = text.replace("</untrusted_data>", "&lt;/untrusted_data&gt;")
    return f"<untrusted_data>\n{safe}\n</untrusted_data>", False


# PII: số điện thoại Việt Nam, email, địa chỉ đường và đơn vị hành chính.
_PHONE_RE = re.compile(r"(?<!\d)(?:\+84|0)(?:[\s.\-]?\d){9}(?!\d)")
_EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])", re.IGNORECASE)
_STREET_RE = re.compile(
    r"\b(?:số\s*)?\d+[A-Za-z]?(?:/\d+)*\s*"
    r"(?:đường|phố|ngõ|ngách|hẻm|đ\.)\s*[^,;.\n]{1,45}"
    r"(?:,\s*(?:phường|xã|quận|huyện|thành phố|tp\.?|tỉnh|p\.|q\.)\s*[^,;.\n]{1,30}){0,3}",
    re.IGNORECASE,
)
_ADMIN_RE = re.compile(
    r"\b(?:phường|xã|quận|huyện)\s+[^,;.\n]{1,30}"
    r"(?:,\s*(?:quận|huyện|thành phố|tp\.?|tỉnh)\s*[^,;.\n]{1,30}){0,2}",
    re.IGNORECASE,
)


def output_guard(text: str) -> tuple[str, bool]:
    """Che PII phổ biến trước khi hiển thị; trả về (văn bản đã che, có_PII)."""
    if not isinstance(text, str):
        return "", False

    masked = text
    found = False
    for pattern, replacement in (
        (_PHONE_RE, "[SĐT đã ẩn]"),
        (_EMAIL_RE, "[email đã ẩn]"),
        (_STREET_RE, "[địa chỉ đã ẩn]"),
        (_ADMIN_RE, "[địa chỉ đã ẩn]"),
    ):
        masked, count = pattern.subn(replacement, masked)
        found = found or count > 0
    return masked, found

def sanitize_untrusted_fields(data: dict | None) -> tuple[dict, bool]:
    """Lọc nội dung văn bản, giữ nguyên các trường định danh và trạng thái."""
    if not isinstance(data, dict):
        return {}, False

    safe_fields = {"order_id", "ticket_id", "status", "eta"}
    cleaned = {}
    flagged = False

    for key, value in data.items():
        if key in safe_fields:
            cleaned[key] = value

        elif isinstance(value, str):
            safe, blocked = prepare_untrusted_text(value)
            cleaned[key] = safe
            flagged = flagged or blocked

        elif isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, str):
                    safe, blocked = prepare_untrusted_text(item)
                    items.append(safe)
                    flagged = flagged or blocked
                else:
                    items.append(item)
            cleaned[key] = items

        else:
            cleaned[key] = value

    return cleaned, flagged
