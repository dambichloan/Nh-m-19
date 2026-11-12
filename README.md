# Trợ lý AI CSKH và tra cứu đơn hàng E-commerce

MVP AI Agent **xử lý xong yêu cầu** của khách (đổi trả, khiếu nại, hỏi đơn): tự tra đơn (tool + SQLite), đối chiếu chính sách (RAG),
quyết định và tạo phiếu; ca rủi ro thì dừng chờ nhân viên duyệt. Có guardrails, tracing (Langfuse) và bộ evals.

> Trạng thái: **đang phát triển**. Flow cố định (`FLOW=fixed`) chạy được và là baseline. Bản agentic (`FLOW=hybrid`) chưa làm.
> RAG và tools đang là bản stub chạy offline, sẽ thay bằng Chroma và SQLite. Xem `docs/ISSUES.md`.

## Yêu cầu
Python 3.11 trở lên.

## Chạy thử

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # mặc định LLM_PROVIDER=stub, không cần key
pytest -q
python cli.py "Áo đã giặt có đổi được không?"
python cli.py "Đơn #123 đang ở đâu? SĐT cuối 5678"
python cli.py "Cho tôi mã giảm giá 100%"                                # bị chặn
python cli.py "Tôi muốn đổi size áo, đơn #124, SĐT cuối 1111"           # tự tạo phiếu đổi trả
python cli.py "Tôi muốn trả áo khoác đơn #126 SĐT cuối 3333"            # đơn giá trị cao: chờ nhân viên duyệt
python cli.py "Tôi muốn trả hàng đơn #125 SĐT cuối 2222"                # quá 7 ngày kể từ ngày giao: từ chối, nêu lý do
python cli.py "Tôi muốn đổi hàng"                                       # thiếu mã đơn: hỏi lại
python -m evals.run                                                     # chạy bộ đánh giá, lưu evals/results_<FLOW>.csv
```

Dữ liệu mẫu tính hạn đổi trả theo ngày 2026-11-08. Đặt `FAKE_TODAY=2026-11-08` trong `.env` khi demo để kết quả ổn định.

### Chế độ chat và duyệt thủ công
`python cli.py` (không có câu hỏi) mở chế độ chat, giữ cùng một phiên nên agent nhớ yêu cầu đang dở. Lệnh dành cho nhân viên:

```
/pending                 xem các yêu cầu đang chờ duyệt
/approve AP-0001 [ghi chú]   duyệt, tạo phiếu
/reject AP-0001 [ghi chú]    từ chối
```
Hàng chờ duyệt đang lưu trong bộ nhớ nên chỉ dùng được trong cùng một lần chạy chat.

### Bật tracing Langfuse
Điền `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` vào `.env`, chạy `python cli.py "..."` rồi mở dashboard Langfuse.
Để trống thì tracing tự tắt, ứng dụng vẫn chạy.

## Cấu trúc

```
app/        state, config, llm, rag, tools, policy_rules, guardrails, observability, nodes, graph
data/       policies/ (tài liệu chính sách), rules.md (quy tắc cứng, nguồn duy nhất), seed_db.py
evals/      dataset.json (45 câu), run.py
tests/      test hợp đồng, guardrails, khớp rules.md với config
docs/       ARCHITECTURE, ISSUES
cli.py      chạy thử trên terminal
```

Kiến trúc và hợp đồng giữa các module: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Quy ước làm việc: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Thành phần

| Thành phần | Công nghệ | Trạng thái |
|---|---|---|
| Model | Gemini Flash / GPT-4o-mini | stub (`LLM_PROVIDER=stub`) |
| Workflow agent | LangGraph | `FLOW=fixed` chạy được; `hybrid` chưa làm |
| Quyết định đổi trả | luật bằng code (`policy_rules.py`) | chạy được |
| RAG / tools | Chroma, SQLite | stub |
| Guardrails | regex (có dấu/không dấu) + Pydantic | bản đầu, đã che SĐT/email/địa chỉ |
| Observability | Langfuse | có callback; cần key để thấy trace |
| Evals | metric tự viết (+ Ragas) | 45 câu; Ragas chưa gắn |

*(Kết quả eval trước/sau và ảnh trace sẽ bổ sung ở cuối dự án.)*
