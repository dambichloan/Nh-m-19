"""RAG. HỢP ĐỒNG: retrieve(query, k) -> list[Chunk].

Owner: B (Data + RAG)
retrieve() đọc từ Chroma (nạp bằng: python -m app.ingest).
Nếu chưa nạp Chroma, chưa có key, hoặc FAKE_LLM=1 thì dùng STUB offline.
"""
import os

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


def _retrieve_stub(query: str, k: int = 4) -> list[Chunk]:
    q = query.lower()
    hits = [chunk for keywords, chunk in _STUB_KB if any(kw in q for kw in keywords)]
    return hits[:k]


def _retrieve_chroma(query: str, k: int) -> list[Chunk]:
    import chromadb
    from app.ingest import get_embedder

    client = chromadb.PersistentClient(path="data/chroma")
    col = client.get_collection("policies")
    vec = get_embedder().embed_query(query)
    res = col.query(query_embeddings=[vec], n_results=k)
    return [
        {"text": doc, "source": meta["source"]}
        for doc, meta in zip(res["documents"][0], res["metadatas"][0])
    ]


def retrieve(query: str, k: int = 4) -> list[Chunk]:
    if os.getenv("FAKE_LLM") != "1":
        try:
            return _retrieve_chroma(query, k)
        except Exception as e:
            print(f"[rag] Chroma lỗi, dùng stub: {e}")
    return _retrieve_stub(query, k)