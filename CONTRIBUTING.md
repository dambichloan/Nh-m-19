# Quy ước làm việc nhóm

## Git
- Nhánh main luôn chạy được. Không push thẳng vào main.
- Mỗi người làm trên nhánh feature/<tên>-<việc> (ví dụ feature/b-rag-chroma), mở PR vào main.
- PR nhỏ (dưới ~300 dòng), mô tả ngắn: làm gì, test thế nào. A review; nếu A quá tải thì D review thay.
- Commit message dạng rag: thêm ingest chroma, guard: chặn thêm mẫu tiêm prompt tiếng Việt.

## Trước khi mở PR

pytest -q          # phải xanh
python cli.py "Áo đã giặt có đổi được không?"   # chạy thử bằng tay
## Quy tắc vàng
1. **Không đổi chữ ký hàm** trong docs/ARCHITECTURE.md nếu chưa báo nhóm.
2. **Không commit** .env, chroma_db/, data/orders.db, key API.
3. Thêm tính năng thì thêm test trong tests/.
4. Không làm việc ngoài module của mình mà không báo chủ module đó.

## Họp
- 10 phút mỗi ngày: hôm qua làm gì, hôm nay làm gì, đang vướng gì.
- Mốc M1 (cuối ngày 6): chạy được đầu-cuối cả 3 nhánh với module thật, có trace Langfuse.
- Feature freeze ngày 11.
