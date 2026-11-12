"""Cấu hình tập trung. Mọi module đọc cấu hình từ đây, không tự gọi os.getenv rải rác."""
import os
from datetime import date

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv chưa cài thì dùng biến môi trường có sẵn
    pass

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "stub")  # stub | gemini | openai
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

LLM_STRICT = os.getenv("LLM_STRICT", "false").lower() == "true"
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0"))

REQUIRE_PHONE_VERIFY = os.getenv("REQUIRE_PHONE_VERIFY", "true").lower() == "true"

# fixed = flow cố định (baseline) | hybrid = có vòng agent (chưa cài, dành cho giai đoạn sau)
FLOW = os.getenv("FLOW", "fixed")

# ---- Quy tắc nghiệp vụ. PHẢI khớp data/rules.md (có tests/test_rules_sync.py kiểm tra) ----
RETURN_WINDOW_DAYS = int(os.getenv("RETURN_WINDOW_DAYS", "7"))  # số ngày đổi trả kể từ ngày giao hàng
WARRANTY_DAYS = int(os.getenv("WARRANTY_DAYS", "30"))
WARRANTY_DAYS_ACCESSORY = int(os.getenv("WARRANTY_DAYS_ACCESSORY", "90"))
APPROVAL_THRESHOLD_VND = int(os.getenv("APPROVAL_THRESHOLD_VND", "500000"))  # đơn TRÊN mức này phải có người duyệt
MAX_VERIFY_ATTEMPTS = int(os.getenv("MAX_VERIFY_ATTEMPTS", "3"))  # sai mã đơn/SĐT từng này lần thì chuyển nhân viên
SHIP_FEE_VND = int(os.getenv("SHIP_FEE_VND", "30000"))
FREE_SHIP_FROM_VND = int(os.getenv("FREE_SHIP_FROM_VND", "500000"))
EXCHANGE_FEE_VND = int(os.getenv("EXCHANGE_FEE_VND", "30000"))


def today() -> date:
    """Ngày hiện tại. Đặt FAKE_TODAY=YYYY-MM-DD để test/eval ra kết quả ổn định."""
    v = os.getenv("FAKE_TODAY")
    return date.fromisoformat(v) if v else date.today()


LANGFUSE_ENABLED = bool(
    os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
)

POLICY_DIR = os.getenv("POLICY_DIR", "data/policies")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
ORDERS_DB = os.getenv("ORDERS_DB", "data/orders.db")

# Câu trả lời cố định (kết quả hành động không để LLM tự viết, tránh bịa mã phiếu / hứa sai)
MSG_BLOCKED = "Xin lỗi, mình không thể hỗ trợ yêu cầu này. Bạn cần giúp gì khác về chính sách hoặc đơn hàng không?"
MSG_NO_INFO = "Mình chưa tìm thấy thông tin phù hợp trong chính sách. Mình sẽ chuyển bạn cho nhân viên hỗ trợ."
MSG_NEED_VERIFY = "Để tra cứu đơn, bạn vui lòng cung cấp mã đơn và 4 số cuối số điện thoại đặt hàng."
MSG_ORDER_NOT_FOUND = "Mình không tìm thấy đơn hàng khớp với thông tin bạn cung cấp. Bạn kiểm tra lại mã đơn và 4 số cuối SĐT giúp mình nhé."
MSG_VERIFY_LOCKED = "Thông tin xác minh chưa khớp sau nhiều lần thử. Để bảo vệ tài khoản của bạn, mình sẽ chuyển bạn cho nhân viên hỗ trợ."
MSG_RETURN_DONE = "Mình đã tạo yêu cầu đổi trả cho đơn #{order_id}, mã phiếu {ticket_id}. Nhân viên sẽ hướng dẫn gửi hàng trong 24 giờ."
MSG_COMPLAINT_DONE = "Mình rất tiếc về trải nghiệm này. Mình đã ghi nhận khiếu nại, mã phiếu {ticket_id}. Nhân viên sẽ liên hệ bạn trong 24 giờ."
MSG_PENDING = "Yêu cầu của bạn cần nhân viên xem xét. Mình đã chuyển với mã {approval_id}, bạn sẽ được liên hệ sớm. Lý do: {reasons}."
MSG_REJECTED = "Mình chưa thể tạo yêu cầu đổi trả cho đơn #{order_id}. Lý do: {reasons}."
MSG_WARRANTY_HINT = "Nếu sản phẩm bị lỗi từ nhà sản xuất, bạn vẫn có thể gửi hình ảnh và mô tả lỗi để được bảo hành (còn trong thời hạn bảo hành)."
MSG_APPROVED_NOTIFY = "Yêu cầu {approval_id} của bạn đã được duyệt, mã phiếu {ticket_id}. {note}"
MSG_DENIED_NOTIFY = "Rất tiếc, yêu cầu {approval_id} của bạn chưa được chấp nhận. {note}"
