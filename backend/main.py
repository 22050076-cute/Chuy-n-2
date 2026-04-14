import os

# --- CẤU HÌNH MÔI TRƯỜNG ĐỂ FIX LỖI ALTS & LOG GOOGLE ---
# Hai dòng này giúp bỏ qua kiểm tra xác thực Google Cloud Platform (GCP)
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
# Ép thư viện sử dụng API Key thay vì ALTS
os.environ["GOOGLE_API_USE_ALTS_CREDENTIALS"] = "false"

import webbrowser
from app import create_app, socketio

# Khởi tạo ứng dụng từ Factory đã định nghĩa trong app/__init__.py
app = create_app()

def start_server():
    """Cấu hình và khởi chạy Server hệ thống EduNext"""
    
    # Thiết lập cổng chạy (Port 3000)
    port = 3000
    
    print("\n" + "="*55)
    print("🚀 EDUNEXT PLATFORM v4.0 - Hệ Sinh Thái Giáo Dục Số")
    print(f"📡 Server đang chạy tại: http://127.0.0.1:{port}")
    print("🤖 Trợ lý AI Gemini: Đã tối ưu cấu hình kết nối")
    print("📧 Hệ thống Email: Đã sẵn sàng")
    print("="*55 + "\n")

    # Tự động mở trình duyệt khi chạy code (tránh mở nhiều tab khi reload)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open(f"http://127.0.0.1:{port}")

    # Khởi chạy bằng SocketIO để hỗ trợ Chat Realtime
    # debug=True: Tự động tải lại code khi có thay đổi
    # use_reloader=True: Theo dõi sự thay đổi của file để restart server
    socketio.run(app, host='0.0.0.0', port=port, debug=True, use_reloader=True)

if __name__ == '__main__':
    try:
        start_server()
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng khi khởi động Server: {e}")