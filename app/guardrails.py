"""Guardrails. HỢP ĐỒNG:
  input_guard(text) -> GuardResult(blocked, reason)
  output_guard(text) -> (text_đã_xử_lý, pii_found)

Owner: D (Guardrails + Observability)
input_guard so khớp trên bản đã bỏ dấu tiếng Việt, nên bắt được cả "bo qua huong dan".
output_guard che SĐT, email và địa chỉ (theo mẫu "số + đường/phố/ngõ..." và "phường/quận/xã...").
"""
import re
import unicodedata
from typing import NamedTuple


class GuardResult(NamedTuple):
    blocked: bool
    reason: str = ""


def _strip_accents(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# Mẫu viết cho văn bản đã bỏ dấu và hạ chữ thường
_ATTACK_PATTERNS = [
    (r"(ma|code|voucher|coupon).{0,20}giam gia.{0,20}(100|mien phi|free)", "coupon_abuse"),
    (r"giam gia\s*100\s*%", "coupon_abuse"),
    (r"(cap|tang|cho).{0,15}(ma|code).{0,15}giam gia", "coupon_abuse"),
    (r"ignore (all |the |your )?(previous|above|prior) (instructions|rules)", "prompt_injection"),
    (r"disregard .{0,20}(instructions|rules)", "prompt_injection"),
    (r"forget (all|everything|your) ", "prompt_injection"),
    (r"you are now ", "prompt_injection"),
    (r"(reveal|show|print|tiet lo|in ra).{0,20}(system prompt|prompt he thong|instructions)", "prompt_injection"),
    (r"bo qua (cac |moi |toan bo )?(huong dan|chi dan|quy tac|quy dinh)", "prompt_injection"),
    (r"(system prompt|prompt he thong)", "prompt_injection"),
    (r"(dong vai|gia vo|act as).{0,25}(admin|quan tri|nhan vien|developer)", "prompt_injection"),
]


def input_guard(text: str) -> GuardResult:
    t = _strip_accents(text)
    for pattern, reason in _ATTACK_PATTERNS:
        if re.search(pattern, t):
            return GuardResult(True, reason)
    return GuardResult(False)


_PHONE_RE = re.compile(r"(?<!\d)(?:\+84|0)(?:[\s.\-]?\d){9}(?!\d)")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# "số 12 đường Láng, phường Láng Thượng, quận Đống Đa" / "12/3 ngõ 5 Chùa Bộc"
_STREET_RE = re.compile(
    r"(?:số\s*)?\d+[A-Za-z]?(?:/\d+)*\s*(?:đường|phố|ngõ|ngách|hẻm|đ\.)\s+[^,.;\n]{1,40}"
    r"(?:,\s*(?:phường|xã|quận|huyện|thành phố|tp\.?|tỉnh|p\.|q\.)\s*[^,.;\n]{1,30}){0,3}",
    re.IGNORECASE,
)
_ADMIN_RE = re.compile(
    r"(?:phường|xã|quận|huyện)\s+[^,.;\n]{1,30}(?:,\s*(?:quận|huyện|thành phố|tp\.?|tỉnh)\s*[^,.;\n]{1,30}){0,2}",
    re.IGNORECASE,
)


def output_guard(text: str) -> tuple[str, bool]:
    masked, n_phone = _PHONE_RE.subn("[SĐT đã ẩn]", text)
    masked, n_mail = _EMAIL_RE.subn("[email đã ẩn]", masked)
    masked, n_street = _STREET_RE.subn("[địa chỉ đã ẩn]", masked)
    masked, n_admin = _ADMIN_RE.subn("[địa chỉ đã ẩn]", masked)
    return masked, (n_phone + n_mail + n_street + n_admin) > 0
