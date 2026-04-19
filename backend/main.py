# -*- coding: utf-8 -*-
import os
import sys
import socket
import webbrowser
from threading import Timer

# --- KHẮC PHỤC LỖI TIẾNG VIỆT ---
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
os.environ["PYTHONIOENCODING"] = "utf-8"

from app import create_app, socketio
from app.config import Config
from app.services.ai_service import register_ai_events # ✅ Import để kích hoạt AI

# Khởi tạo App
app = create_app()

# ✅ Đăng ký các sự kiện Chat AI với SocketIO
register_ai_events(socketio)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def open_browser(port):
    """Tự động mở trình duyệt sau 1.5 giây khi server chạy"""
    Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

if __name__ == '__main__':
    port = 3000
    local_ip = get_local_ip()
    
    # 1. Cấu hình hiển thị bảng thông báo
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        if os.name == 'nt':
            os.system('chcp 65001 > nul')
            
        print("\n" + "═"*60)
        print("🚀 EDUNEXT PLATFORM v4.0 - Hệ Sinh Thái Giáo Dục Số")
        print(f"📡 LOCAL (Máy tính): http://127.0.0.1:{port}")
        print(f"📱 MOBILE (Cùng mạng): http://{local_ip}:{port}")
        print(f"🤖 AI Engine: {Config.GEMINI_MODEL}")
        print(f"🔑 API Status: {'✅ Đã nạp' if Config.GENAI_API_KEY else '❌ Thiếu Key!'}")
        print("═"*60 + "\n")
        
        # Mở trình duyệt tự động
        open_browser(port)

    # 2. Chạy Server với SocketIO
    # allow_unsafe_werkzeug=True cần thiết khi chạy socketio ở chế độ debug
    try:
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=port, 
            debug=True, 
            use_reloader=True, 
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Đang đóng server EduNext...")