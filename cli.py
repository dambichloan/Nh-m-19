"""Chạy thử nhanh:  python cli.py "Áo đã giặt có đổi được không?"   hoặc  python cli.py  (chế độ chat)

Chế độ chat có thêm lệnh cho nhân viên: /pending, /approve <AP-id> [ghi chú], /reject <AP-id> [ghi chú].
"""
import sys

from app import config, tools
from app.graph import resolve_approval, run


def show(question: str, session_id: str | None = None) -> None:
    s = run(question, session_id)
    print(f"\n> {question}")
    print(f"  intent : {s.get('intent', '-')}   blocked: {s.get('blocked')} ({s.get('block_reason', '')})")
    print(f"  status : {s.get('status')}   ticket: {s.get('ticket_id')}   approval: {s.get('approval_id')}   handoff: {bool(s.get('handoff'))}")
    print(f"  flow   : {' -> '.join(s['trace'])}   [FLOW={config.FLOW}]")
    print(f"  answer : {s['answer']}\n")


def staff_command(line: str) -> None:
    parts = line.split(maxsplit=2)
    cmd = parts[0]
    if cmd == "/pending":
        pending = tools.list_pending_approvals()
        if not pending:
            print("  Không có yêu cầu nào đang chờ duyệt.\n")
        for a in pending:
            print(f"  {a['id']}  {a['kind']}  đơn #{a['order_id']}  lý do: {'; '.join(a['reasons'])}")
        print()
    elif cmd in ("/approve", "/reject") and len(parts) >= 2:
        note = parts[2] if len(parts) > 2 else ""
        try:
            r = resolve_approval(parts[1], cmd == "/approve", "staff-cli", note)
        except (KeyError, ValueError) as e:
            print(f"  Lỗi: {e}\n")
            return
        print(f"  status : {r['status']}   ticket: {r['ticket_id']}")
        print(f"  gửi khách: {r['message']}\n")
    else:
        print("  Lệnh: /pending | /approve <AP-id> [ghi chú] | /reject <AP-id> [ghi chú]\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show(" ".join(sys.argv[1:]))
    else:
        print("Gõ câu hỏi (Ctrl+C để thoát). Lệnh nhân viên: /pending, /approve AP-0001, /reject AP-0001")
        sid = "cli-chat"  # cùng phiên để agent nhớ yêu cầu đang dở khi hỏi lại
        while True:
            try:
                line = input("? ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not line:
                continue
            if line.startswith("/"):
                staff_command(line)
            else:
                show(line, sid)
