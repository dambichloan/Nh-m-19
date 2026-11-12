"""
Module: contracts.py
Mô tả: Hợp đồng giao diện và kiểu dữ liệu dùng chung giữa các module trong Agent.
"""

from typing import Optional, TypedDict


class Chunk(TypedDict):
    text: str
    source: str


class GuardResult(TypedDict):
    blocked: bool
    reason: Optional[str]  # "prompt_injection" | "promo_code_abuse" | None


class Order(TypedDict):
    order_id: str
    status: str            # 'processing' | 'shipping' | 'delivered' | 'cancelled'
    items: list[str]       # Danh sách sản phẩm kèm size
    carrier: Optional[str]
    eta: Optional[str]
    total_vnd: int