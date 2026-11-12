"""
src/tools/orders.py
Phụ trách: Thành viên C (Tools / Database)
Mô tả: Quản lý SQLite schema và cung cấp các hàm get_order, check_return_eligibility,
create_return_request, create_complaint với cơ chế chống quét mã đơn (IDOR).
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# Đường dẫn file SQLite lưu tại data/orders.db theo chuẩn dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "orders.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Khởi tạo SQLite schema gồm 4 bảng: orders, order_items, complaints, return_requests."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Bảng orders (lưu phone_last4 để bảo mật PII, tra cứu xác thực)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        phone_last4 TEXT NOT NULL,
        status TEXT NOT NULL,          -- processing | shipping | delivered | cancelled
        carrier TEXT,
        eta TEXT,
        total_vnd INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Bảng order_items (quan hệ 1-N với orders, lưu sku, size)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        product_name TEXT NOT NULL,
        size TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    );
    """)

    # 3. Bảng complaints (khiếu nại, phản ánh của khách)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        complaint_id TEXT PRIMARY KEY,
        order_id TEXT,
        summary TEXT NOT NULL,
        status TEXT NOT NULL,          -- OPEN | RESOLVED
        created_at TEXT NOT NULL
    );
    """)

    # 4. Bảng return_requests (yêu cầu đổi/trả hàng)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS return_requests (
        request_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL,          -- PENDING_APPROVAL | APPROVED | REJECTED
        created_at TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    );
    """)

    _seed_mock_data(cursor)
    conn.commit()
    conn.close()


def _seed_mock_data(cursor: sqlite3.Cursor):
    """Nạp dữ liệu mẫu nếu database đang trống để chạy thử demo ngay."""
    cursor.execute("SELECT COUNT(*) FROM orders;")
    if cursor.fetchone()[0] == 0:
        # Đơn 123: Đã giao thành công (dùng để test và demo)
        cursor.execute("""
        INSERT INTO orders VALUES 
        ('123', 'Nguyen Van A', '6789', 'delivered', 'GHTK', '2026-11-05', 770000, '2026-11-01')
        """)
        cursor.execute("""
        INSERT INTO order_items (order_id, sku, product_name, size, quantity, price) VALUES 
        ('123', 'SKU-DR-01', 'Đầm Công Sở Cổ V', 'M', 1, 450000),
        ('123', 'SKU-BL-02', 'Áo Sơ Mi Lụa', 'S', 1, 320000)
        """)

        # Đơn 456: Đang vận chuyển
        cursor.execute("""
        INSERT INTO orders VALUES 
        ('456', 'Tran Thi B', '1234', 'shipping', 'ViettelPost', '2026-11-12', 390000, '2026-11-08')
        """)
        cursor.execute("""
        INSERT INTO order_items (order_id, sku, product_name, size, quantity, price) VALUES 
        ('456', 'SKU-PT-03', 'Quần Tây Ống Suông', 'L', 1, 390000)
        """)


# ==========================================
# CÁC STUB FUNCTIONS THEO ĐẶC TẢ
# ==========================================

def get_order(order_id: str, phone_last4: str) -> Dict[str, Any]:
    """
    Tra cứu thông tin đơn hàng.
    BẢO MẬT: Sai 4 số cuối SĐT HOẶC mã đơn không tồn tại đều trả cùng mã lỗi NOT_FOUND
    để tránh việc kẻ xấu quét mã đơn hợp lệ (chống lỗ hổng IDOR).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (str(order_id).strip(),))
    row = cursor.fetchone()

    # Sai 4 số cuối hoặc không tìm thấy đơn -> Trả cùng lỗi NOT_FOUND
    if not row or str(row["phone_last4"]) != str(phone_last4).strip():
        conn.close()
        return {
            "status": "error",
            "error_code": "NOT_FOUND",
            "message": "Không tìm thấy thông tin đơn hàng hoặc thông tin xác minh không hợp lệ."
        }

    cursor.execute("SELECT sku, product_name, size, quantity, price FROM order_items WHERE order_id = ?", (str(order_id).strip(),))
    items_rows = cursor.fetchall()
    conn.close()

    items = [
        {
            "sku": it["sku"],
            "product_name": it["product_name"],
            "size": it["size"],
            "quantity": it["quantity"],
            "price": it["price"]
        }
        for it in items_rows
    ]

    return {
        "status": "success",
        "data": {
            "order_id": row["order_id"],
            "status": row["status"],
            "items": items,
            "carrier": row["carrier"],
            "eta": row["eta"],
            "total_vnd": row["total_vnd"]
        }
    }


def check_return_eligibility(order_id: str, phone_last4: str, sku: str) -> Dict[str, Any]:
    """
    Kiểm tra điều kiện đổi/trả hàng:
    - Nếu sai SĐT hoặc đơn không tồn tại -> Trả lỗi NOT_FOUND đồng nhất.
    - Điều kiện: Đơn phải ở trạng thái 'delivered' và SKU phải nằm trong đơn.
    """
    order_res = get_order(order_id, phone_last4)
    if order_res.get("status") == "error":
        return order_res

    order_data = order_res["data"]
    if order_data["status"] != "delivered":
        return {
            "status": "ineligible",
            "reason": f"Đơn hàng đang ở trạng thái '{order_data['status']}', chỉ được đổi trả sau khi nhận hàng."
        }

    valid_skus = [it["sku"] for it in order_data["items"]]
    if sku not in valid_skus:
        return {
            "status": "ineligible",
            "reason": f"Sản phẩm {sku} không thuộc đơn hàng {order_id}."
        }

    return {
        "status": "eligible",
        "eligible": True,
        "sku": sku,
        "message": "Đủ điều kiện đổi trả trong vòng 7 ngày khi còn nguyên tem mác và chưa giặt tẩy."
    }


def create_return_request(order_id: str, phone_last4: str, sku: str, reason: str) -> Dict[str, Any]:
    """Tạo yêu cầu đổi/trả hàng vào database."""
    check = check_return_eligibility(order_id, phone_last4, sku)
    if check.get("status") == "error":
        return check
    if not check.get("eligible", False):
        return {"status": "failed", "reason": check.get("reason")}

    conn = get_connection()
    cursor = conn.cursor()
    req_id = f"RET-{int(datetime.now().timestamp())}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO return_requests (request_id, order_id, sku, reason, status, created_at)
    VALUES (?, ?, ?, ?, 'PENDING_APPROVAL', ?)
    """, (req_id, order_id, sku, reason, now_str))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "data": {
            "request_id": req_id,
            "order_id": order_id,
            "sku": sku,
            "status": "PENDING_APPROVAL",
            "message": "Yêu cầu đổi trả đã được tiếp nhận thành công."
        }
    }


def create_complaint(order_id: Optional[str], phone_last4: Optional[str], summary: str) -> Dict[str, Any]:
    """Tạo vé khiếu nại (có kiểm tra thông tin đơn nếu khách cung cấp mã đơn)."""
    if order_id and phone_last4:
        order_res = get_order(order_id, phone_last4)
        if order_res.get("status") == "error":
            return order_res

    conn = get_connection()
    cursor = conn.cursor()
    complaint_id = f"CMP-{int(datetime.now().timestamp())}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO complaints (complaint_id, order_id, summary, status, created_at)
    VALUES (?, ?, ?, 'OPEN', ?)
    """, (complaint_id, order_id, summary, now_str))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "data": {
            "complaint_id": complaint_id,
            "order_id": order_id,
            "summary": summary,
            "status": "OPEN",
            "message": "Khiếu nại của bạn đã được ghi nhận."
        }
    }