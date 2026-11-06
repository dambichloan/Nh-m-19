"""Chạy evals:  python -m evals.run

Owner: E (Evals + Báo cáo)
Bản hiện tại chỉ tính 3 metric rẻ nhất (intent, chặn đúng/sai, độ trễ) để E có chỗ bắt đầu.
TODO(E): thêm Ragas (Faithfulness, Context Precision), cache kết quả LLM, xuất evals/report.md.
"""
import json
import time
from pathlib import Path

from app.graph import run


def main() -> None:
    data = json.loads((Path(__file__).parent / "dataset.json").read_text(encoding="utf-8"))
    intent_ok = intent_total = 0
    attacks = attacks_blocked = normal = normal_blocked = 0
    latencies = []

    for row in data:
        t0 = time.perf_counter()
        s = run(row["question"])
        latencies.append(time.perf_counter() - t0)

        if row["expected_blocked"]:
            attacks += 1
            attacks_blocked += bool(s.get("blocked"))
        else:
            normal += 1
            normal_blocked += bool(s.get("blocked"))
            intent_total += 1
            intent_ok += s.get("intent") == row["expected_intent"]

    print(f"Số câu: {len(data)}")
    print(f"Độ chính xác intent : {intent_ok}/{intent_total}")
    print(f"Chặn đúng tấn công  : {attacks_blocked}/{attacks}")
    print(f"Chặn nhầm câu bình thường: {normal_blocked}/{normal}")
    print(f"Latency TB: {sum(latencies) / len(latencies) * 1000:.1f} ms")


if __name__ == "__main__":
    main()
