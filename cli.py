"""Chạy thử nhanh:  python cli.py "Áo đã giặt có đổi được không?"   hoặc  python cli.py  (chế độ chat)"""
import sys

from app.graph import run


def show(question: str, session_id: str | None = None) -> None:
    s = run(question, session_id)
    print(f"\n> {question}")
    print(f"  intent : {s.get('intent', '-')}   blocked: {s.get('blocked')} ({s.get('block_reason', '')})")
    print(f"  status : {s.get('status')}   ticket: {s.get('ticket_id')}   approval: {s.get('approval_id')}")
    print(f"  flow   : {' -> '.join(s['trace'])}")
    print(f"  answer : {s['answer']}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show(" ".join(sys.argv[1:]))
    else:
        print("Gõ câu hỏi (Ctrl+C để thoát)")
        sid = "cli-chat"  # cùng phiên để agent nhớ yêu cầu đang dở khi hỏi lại
        while True:
            try:
                show(input("? "), sid)
            except (KeyboardInterrupt, EOFError):
                break
