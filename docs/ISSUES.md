# Danh sách issue theo người (copy từng mục thành GitHub Issue)

Mốc chung: **M1 cuối ngày 6** (đầu-cuối bằng module thật) · **Ngày 8** chạy eval lần đầu · **Ngày 11** feature freeze.

---
## A. Tech lead + Agent
- [ ] A1. Tạo repo GitHub, đẩy khung này lên, bật branch protection cho `main`, mời 4 bạn (ngày 1)
- [ ] A2. Họp kickoff: chốt hợp đồng trong `docs/ARCHITECTURE.md`, chốt LLM (Gemini Flash hay GPT-4o-mini) (ngày 1)
- [ ] A3. `llm.classify_intent` bằng LLM + structured output Pydantic, trích `order_id` và `phone_last4` (ngày 3-4)
- [ ] A4. `llm.generate_answer`: prompt chỉ dựa trên context/order, nêu nguồn, không bịa (ngày 4-5)
- [ ] A5. Cho node `policy` biết khi nào "không đủ context" để chuyển nhân viên (ngày 5)
- [ ] A6. Ghép module thật của B, C, D vào graph, giữ test xanh (ngày 5-6)
- [ ] A7. Review PR hằng ngày

## B. Data + RAG
- [ ] B1. Viết 5-6 file markdown trong `data/policies/`: `doi_tra.md`, `hoan_tien.md`, `van_chuyen.md`, `bao_hanh.md`, `size_guide.md`, `faq.md`. **Xong trong 2 ngày đầu** vì E cần để soạn đáp án chuẩn. Viết điều kiện cụ thể (số ngày, tình trạng hàng, ngoại lệ). Tên file khớp trường `source`.
- [ ] B2. `scripts/ingest.py`: chunk 300-500 token, overlap ~50, embedding, lưu Chroma (ngày 3)
- [ ] B3. Thay thân `rag.retrieve` bằng Chroma, giữ chữ ký, metadata có `source` (ngày 3-4)
- [ ] B4. Thử tham số `k`, kích thước chunk; ghi lại số liệu trước/sau cho slide (tuần 2)

## C. Tools + UI
- [ ] C1. `data/seed_db.py`: tạo `orders.db` 20-30 đơn đủ trạng thái, có đơn #123 (SĐT cuối 5678) cho demo (ngày 2)
- [ ] C2. Thay thân `tools.get_order` bằng SQLite, câu lệnh tham số hóa, trả `None` khi sai SĐT (ngày 3)
- [ ] C3. `tools.create_complaint` ghi bảng `tickets` (ngày 3)
- [ ] C4. (Tùy chọn) bọc tool thành MCP server bằng FastMCP (ngày 4-5)
- [ ] C5. `ui.py` Streamlit: khung chat, hiển thị intent, nguồn trích dẫn, trạng thái bị chặn (tuần 2)

## D. Guardrails + Observability
- [ ] D1. Mở rộng `input_guard`: nhiều mẫu tiêm prompt, lừa mã giảm giá, có dấu và không dấu (ngày 3-4)
- [ ] D2. Mở rộng `output_guard`: SĐT, email, địa chỉ; chặn câu trả lời chứa mã giảm giá/cam kết ngoài chính sách (ngày 4)
- [ ] D3. `tests/test_guardrails.py`: ít nhất 20 câu tấn công + 20 câu bình thường (kiểm tra chặn nhầm) (ngày 4-5)
- [ ] D4. Tạo project Langfuse, điền key vào `.env`, kiểm tra `get_run_config` đúng phiên bản langfuse đã cài; trace phải hiện đủ các node, latency, token (ngày 5)
- [ ] D5. Viết README chạy thử từ máy sạch (tuần 2)

## E. Evals + Báo cáo
- [ ] E1. `evals/dataset.json` 25-30 câu: policy / order / complaint / tấn công, có `reference` (đáp án chuẩn) và `expected_intent`. Khung mẫu đã có. Cần file chính sách của B (ngày 3-5)
- [ ] E2. `evals/run.py`: chạy `graph.run` trên dataset, tính metric tự viết (độ chính xác intent, tỉ lệ chặn đúng/chặn nhầm, latency) (ngày 5-6)
- [ ] E3. Thêm Ragas (Faithfulness, Context Precision); **cache kết quả gọi LLM** để khỏi chạm rate limit (ngày 6-8)
- [ ] E4. Chạy eval lần đầu ngày 8, xuất `evals/report.md`, gửi nhóm danh sách câu sai (ngày 8)
- [ ] E5. Dựng khung slide, điều phối quay video (tuần 2)

---
## Bổ sung theo bài toán "xử lý xong yêu cầu" (đã có khung trong repo)
- [ ] A8. Dùng LLM thật cho `classify_intent` phân biệt `policy` (hỏi) và `return` (yêu cầu); đo bằng dataset (ngày 3-5)
- [ ] B5. Viết `doi_tra.md` đúng số liệu trong `app/config.py` (7 ngày, ngoại lệ lỗi nhà sản xuất, hàng đã giặt) hoặc báo A đổi config (ngày 2)
- [ ] C6. SQLite thêm bảng `tickets` (kind: return/complaint, status) và `approvals` (pending/approved/rejected, reviewer, note); đơn mẫu có `delivered_at`, `total_vnd`, phủ 5 tình huống đơn 123-127 (ngày 3-4)
- [ ] C7. `ui.py` có 2 trang: Khách (chat, hiển thị `status`, mã phiếu) và Nhân viên (danh sách `list_pending_approvals`, nút Duyệt/Từ chối gọi `graph.resolve_approval`) (tuần 2)
- [ ] D6. Test: khách không thể ép tạo phiếu bằng prompt ("duyệt luôn", "bỏ qua kiểm tra"); không tạo phiếu khi sai SĐT; output_guard che SĐT trong ghi chú nhân viên (ngày 4-5)
- [ ] E6. Dataset 25-30 câu phủ đủ: đổi trả tự duyệt / từ chối / chờ duyệt / thiếu xác minh, khiếu nại thường / rủi ro. Metric chính: `status` đúng, `Hành động khi chưa được phép = 0` (ngày 3-6)
