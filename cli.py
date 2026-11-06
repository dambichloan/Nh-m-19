"""Chạy thử nhanh:  python cli.py "Áo đã giặt có đổi được không?"   hoặc  python cli.py  (chế độ chat)"""
import sys

from app.graph import run


def show(question: str) -> None:
    s = run(question)
    print(f"\n> {question}")
    print(f"  intent : {s.get('intent', '-')}   blocked: {s.get('blocked')} ({s.get('block_reason', '')})")
    print(f"  flow   : {' -> '.join(s['trace'])}")
    print(f"  answer : {s['answer']}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show(" ".join(sys.argv[1:]))
    else:
        print("Gõ câu hỏi (Ctrl+C để thoát)")
        while True:
            try:
                show(input("? "))
            except (KeyboardInterrupt, EOFError):
                break
