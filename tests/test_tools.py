"""
tests/test_tools.py
Kiểm thử tính năng Database SQLite và các Stub Functions của module tools.
"""

import sys
import os

# Đảm bảo Python luôn tìm thấy thư mục gốc dự án (Nh-m-19)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.tools.orders import (
    init_db,
    get_order,
    check_return_eligibility,
    create_return_request,
    create_complaint
)

def run_tests():
    print("--- BAT DAU CHAY UNIT TEST DATABASE & TOOLS ---")

    # 1. Khoi tao DB
    init_db()
    print("[PASS] 1. Khoi tao bang SQLite va du lieu mau thanh cong.")

    # 2. Test tra cuu dung
    res1 = get_order("123", "6789")
    assert res1["status"] == "success", "Loi: Tra cuu don dung that bai!"
    print("[PASS] 2. Tra cuu don hop le: Thanh cong.")

    # 3. Test sai 4 so cuoi -> Tra NOT_FOUND
    res2 = get_order("123", "0000")
    assert res2.get("error_code") == "NOT_FOUND", "Loi: Sai SDT khong tra NOT_FOUND!"
    print("[PASS] 3. Sai 4 so cuoi: Tra ma loi NOT_FOUND dong nhat.")

    # 4. Test don khong ton tai -> Tra cung loi NOT_FOUND
    res3 = get_order("99999", "6789")
    assert res3.get("error_code") == "NOT_FOUND", "Loi: Don khong ton tai khong tra NOT_FOUND!"
    print("[PASS] 4. Don khong ton tai: Tra ma loi NOT_FOUND dong nhat (chong IDOR).")

    # 5. Test kiem tra doi/tra
    eligibility = check_return_eligibility("123", "6789", "SKU-DR-01")
    assert eligibility.get("eligible") is True
    print("[PASS] 5. Kiem tra dieu kien doi tra: Hop le.")

    # 6. Test tao yeu cau doi/tra
    ret_res = create_return_request("123", "6789", "SKU-DR-01", "Rong eo")
    assert ret_res["status"] == "success"
    print(f"[PASS] 6. Tao return request: Thanh cong ({ret_res['data']['request_id']}).")

    # 7. Test tao khieu nai
    cmp_res = create_complaint("123", "6789", "Hop bi mop")
    assert cmp_res["status"] == "success"
    print(f"[PASS] 7. Tao complaint: Thanh cong ({cmp_res['data']['complaint_id']}).")

    print("\n==========================================")
    print(">>> TAT CA CAC BAI TEST DAU HOAN TOAN DAT CHUAN! <<<")
    print("==========================================\n")

if __name__ == "__main__":
    run_tests()