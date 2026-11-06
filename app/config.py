"""Cấu hình tập trung. Mọi module đọc cấu hình từ đây, không tự gọi os.getenv rải rác."""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv chưa cài thì dùng biến môi trường có sẵn
    pass

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "stub")  # stub | gemini | openai
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

REQUIRE_PHONE_VERIFY = os.getenv("REQUIRE_PHONE_VERIFY", "true").lower() == "true"

LANGFUSE_ENABLED = bool(
    os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
)

POLICY_DIR = os.getenv("POLICY_DIR", "data/policies")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
ORDERS_DB = os.getenv("ORDERS_DB", "data/orders.db")

# Câu trả lời cố định
MSG_BLOCKED = "Xin lỗi, mình không thể hỗ trợ yêu cầu này. Bạn cần giúp gì khác về chính sách hoặc đơn hàng không?"
MSG_NO_INFO = "Mình chưa tìm thấy thông tin phù hợp trong chính sách. Mình sẽ chuyển bạn cho nhân viên hỗ trợ."
MSG_NEED_VERIFY = "Để tra cứu đơn, bạn vui lòng cung cấp mã đơn và 4 số cuối số điện thoại đặt hàng."
MSG_ORDER_NOT_FOUND = "Mình không tìm thấy đơn hàng khớp với thông tin bạn cung cấp. Bạn kiểm tra lại mã đơn và 4 số cuối SĐT giúp mình nhé."
