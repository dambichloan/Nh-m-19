"""RAG. HỢP ĐỒNG: retrieve(query, k) -> list[Chunk].

Owner: B (Data + RAG)
Bản hiện tại là STUB: trả đoạn chính sách cố định theo từ khóa, chạy offline.
B thay phần thân bằng Chroma thật nhưng GIỮ NGUYÊN chữ ký hàm.
"""
from app.state import Chunk

_STUB_KB: list[tuple[tuple[str, ...], Chunk]] = [
    (
        ("giặt", "đổi", "trả", "tag", "hoàn"),
        {
            "text": "Đổi trả trong 7 ngày kể từ khi nhận hàng. Sản phẩm phải chưa qua sử dụng, chưa giặt, còn nguyên tag. Hàng đã giặt không được đổi trả, trừ lỗi từ nhà sản xuất.",
            "source": "doi_tra.md",
        },
    ),
    (
        ("size", "kích cỡ", "chọn size"),
        {
            "text": "Bảng size: S (45-52kg), M (53-60kg), L (61-68kg), XL (69-76kg). Nếu phân vân giữa hai size, nên chọn size lớn hơn.",
            "source": "size_guide.md",
        },
    ),
    (
        ("ship", "vận chuyển", "giao hàng", "phí"),
        {
            "text": "Giao hàng 2-4 ngày làm việc. Miễn phí vận chuyển cho đơn từ 500.000đ.",
            "source": "van_chuyen.md",
        },
    ),
]


def retrieve(query: str, k: int = 4) -> list[Chunk]:
    q = query.lower()
    hits = [chunk for keywords, chunk in _STUB_KB if any(kw in q for kw in keywords)]
    return hits[:k]
