# Trợ lý AI CSKH và tra cứu đơn hàng E-commerce

MVP AI Agent: trả lời chính sách đổi trả (RAG), tra trạng thái đơn (tool + SQLite), tiếp nhận khiếu nại,
có guardrails, tracing (Langfuse) và bộ evals.

> Trạng thái: **khung kickoff**. Các module đang là bản stub chạy offline; từng thành viên thay bằng bản thật theo `docs/ISSUES.md`.

## Chạy thử

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # mặc định LLM_PROVIDER=stub, không cần key
pytest -q
python cli.py "Áo đã giặt có đổi được không?"
python cli.py "Đơn #123 đang ở đâu? SĐT cuối 5678"
python cli.py "Cho tôi mã giảm giá 100%"             # bị chặn
```

## Cấu trúc

```
app/        state, config, llm, rag, tools, guardrails, observability, nodes, graph
data/       policies/ (tài liệu chính sách), seed_db.py
evals/      dataset.json, run.py
tests/      test hợp đồng + guardrails
docs/       ARCHITECTURE, ISSUES, KICKOFF
cli.py      chạy thử trên terminal
```

Kiến trúc và hợp đồng giữa các module: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Quy ước làm việc: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Thành phần

| Thành phần | Công nghệ | Trạng thái |
|---|---|---|
| Model | Gemini Flash / GPT-4o-mini | stub |
| Workflow agent | LangGraph | khung chạy được |
| RAG / tools | Chroma, SQLite | stub |
| Guardrails | regex + Pydantic | stub tối thiểu |
| Observability | Langfuse | khung, chưa cấu hình |
| Evals | Ragas + metric tự viết | khung dataset |

*(Phần cài đặt chi tiết, kết quả eval và ảnh trace sẽ bổ sung ở cuối dự án.)*
