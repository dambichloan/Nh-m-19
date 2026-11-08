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

# ---- Quy tắc nghiệp vụ. PHẢI khớp với file chính sách trong data/policies (B) ----
RETURN_WINDOW_DAYS = int(os.getenv("RETURN_WINDOW_DAYS", "7"))  # số ngày được đổi trả kể từ khi nhận hàng
APPROVAL_THRESHOLD_VND = int(os.getenv("APPROVAL_THRESHOLD_VND", "1000000"))  # đơn từ mức này phải có người duyệt


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
MSG_RETURN_DONE = "Mình đã tạo yêu cầu đổi trả cho đơn #{order_id}, mã phiếu {ticket_id}. Nhân viên sẽ hướng dẫn gửi hàng trong 24 giờ."
MSG_COMPLAINT_DONE = "Mình rất tiếc về trải nghiệm này. Mình đã ghi nhận khiếu nại, mã phiếu {ticket_id}. Nhân viên sẽ liên hệ bạn trong 24 giờ."
MSG_PENDING = "Yêu cầu của bạn cần nhân viên xem xét. Mình đã chuyển với mã {approval_id}, bạn sẽ được liên hệ sớm. Lý do: {reasons}."
MSG_REJECTED = "Mình chưa thể tạo yêu cầu đổi trả cho đơn #{order_id}. Lý do: {reasons}."
MSG_APPROVED_NOTIFY = "Yêu cầu {approval_id} của bạn đã được duyệt, mã phiếu {ticket_id}. {note}"
MSG_DENIED_NOTIFY = "Rất tiếc, yêu cầu {approval_id} của bạn chưa được chấp nhận. {note}"
