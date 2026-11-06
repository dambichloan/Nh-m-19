# Agenda họp kickoff (45 phút, ngày 1)

1. **(5') Mục tiêu và mốc**: M1 cuối ngày 6, eval ngày 8, freeze ngày 11, nộp ngày 14.
2. **(10') Xem khung repo**: `python cli.py "Áo đã giặt có đổi được không?"`, `pytest -q`, đọc `docs/ARCHITECTURE.md`.
3. **(10') Chốt hợp đồng**: có ai cần đổi chữ ký hàm hoặc thêm trường vào `AgentState` không? Chốt ngay hôm nay.
4. **(5') Chốt LLM**: Gemini Flash (free tier, hợp chạy eval nhiều lần) hay GPT-4o-mini. Ai tạo key, chia key thế nào (không gửi qua repo).
5. **(5') Chốt Langfuse**: D tạo project, mời cả nhóm.
6. **(5') Quy ước Git** theo `CONTRIBUTING.md`; tạo Issue theo `docs/ISSUES.md`.
7. **(5') Việc phải xong trong 2 ngày đầu**: B xong file chính sách; C xong seed DB; mọi người chạy được khung trên máy mình.

## Checklist ngày 1-2 của lead
- [ ] Đẩy repo lên GitHub, bật branch protection, mời thành viên
- [ ] Mọi người clone, tạo venv, `pip install -r requirements.txt`, `pytest -q` xanh
- [ ] Tạo 5 nhóm issue từ `docs/ISSUES.md`
- [ ] Chốt LLM, tạo key, điền `.env` của từng người
- [ ] Kênh chat và giờ họp 10 phút mỗi ngày
