import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_mail import Mail
from .config import Config

# Khởi tạo các đối tượng mở rộng
mail = Mail()
socketio = SocketIO()

def create_app():
    # --- LOGIC XỬ LÝ ĐƯỜNG DẪN THƯ MỤC ---
    # 1. Lấy đường dẫn tuyệt đối của file này (D:\THCS\backend\app\__init__.py)
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 2. Nhảy ra ngoài 2 cấp để lên thư mục gốc D:\THCS
    # Cấp 1: D:\THCS\backend\app -> D:\THCS\backend
    # Cấp 2: D:\THCS\backend -> D:\THCS
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    
    # 3. Kết nối tới thư mục frontend
    frontend_dir = os.path.join(root_dir, 'frontend')
    
    # In ra terminal để bạn dễ dàng kiểm tra khi chạy (Debug)
    print(f"📂 Thư mục gốc: {root_dir}")
    print(f"📂 Thư mục giao diện: {frontend_dir}")

    # Khởi tạo Flask với cấu hình thư mục đã tính toán
    app = Flask(__name__, 
                template_folder=os.path.join(frontend_dir, 'templates'), 
                static_folder=os.path.join(frontend_dir, 'static'), 
                static_url_path='/static')

    # Nạp cấu hình từ Config class
    app.config.from_object(Config)
    
    # Kích hoạt CORS, Mail và SocketIO
    CORS(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

    # --- ĐĂNG KÝ CÁC BLUEPRINTS ---
    from .routes.auth import auth_bp
    from .routes.student import student_bp
    from .routes.teacher import teacher_bp
    from .routes.parent import parent_bp
    from .routes.common import common_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(common_bp)

    # --- ĐĂNG KÝ SỰ KIỆN AI ---
    from .services.ai_service import register_ai_events
    register_ai_events(socketio)

    return app