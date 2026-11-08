# Quy ước làm việc

Dự án do một người thực hiện; quy ước dưới đây giữ lịch sử Git sạch và code luôn chạy được.

## Git
- `main` luôn chạy được và `pytest -q` xanh.
- Việc lớn làm trên nhánh `feature/<việc>` (ví dụ `feature/rag-chroma`), xong thì merge vào `main`. Việc nhỏ commit thẳng cũng được.
- Commit nhỏ, một ý một commit, message dạng `rag: thêm ingest chroma`, `rules: đổi ngưỡng duyệt 500k`, `guard: chặn tiêm prompt không dấu`. Không dùng "update"/"replace project".
- Luôn `git pull` trước khi push. Không bao giờ `git push --force` lên `main`.

## Trước khi commit
```bash
pytest -q                                         # phải xanh
python cli.py "Áo đã giặt có đổi được không?"     # chạy thử bằng tay
```

## Quy tắc vàng
1. **Một nguồn số liệu:** `data/rules.md`. Sửa số (ngày, tiền, ngưỡng) thì sửa `rules.md`, `app/config.py`, file trong `data/policies/` và `.env.example` cùng lúc.
2. **Không đổi chữ ký hàm** trong `docs/ARCHITECTURE.md` nếu chưa cập nhật tài liệu và test.
3. **Không commit** `.env`, `chroma_db/`, `data/orders.db`, API key. Lỡ push key thì đổi key ngay.
4. Thêm tính năng thì thêm test trong `tests/`.
5. Mỗi lần chỉnh để cải thiện: ghi lại đã đổi gì và chỉ số nào đổi bao nhiêu (đưa vào slide).

## Mốc
- Giai đoạn 1: 23h 8/11 · M1: 12/11 · feature freeze: 17/11 · nộp: 20/11. Chi tiết xem `docs/ISSUES.md`.
