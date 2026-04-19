import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_mail import Mail
from .config import Config

# Khởi tạo các đối tượng mở rộng (Để bên ngoài để các file khác có thể import)
mail = Mail()
socketio = SocketIO()

def create_app():
    # --- LOGIC XỬ LÝ ĐƯỜNG DẪN THƯ MỤC ---
    current_dir = os.path.abspath(os.path.dirname(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    frontend_dir = os.path.join(root_dir, 'frontend')
    
    # Debug đường dẫn
    print(f"📂 Thư mục gốc: {root_dir}")
    print(f"📂 Thư mục giao diện: {frontend_dir}")

    # Khởi tạo Flask
    app = Flask(__name__, 
                template_folder=os.path.join(frontend_dir, 'templates'), 
                static_folder=os.path.join(frontend_dir, 'static'), 
                static_url_path='/static')

    app.config.from_object(Config)
    
    # Tự động tạo thư mục upload bài giảng nếu chưa có
    upload_path = os.path.join(frontend_dir, 'static', 'uploads', 'lessons')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        print(f"📁 Đã tạo thư mục upload: {upload_path}")

    # Kích hoạt các Plugin
    CORS(app)
    mail.init_app(app)
    # Lưu ý: Luôn để async_mode='eventlet' cho SocketIO trên Windows để chạy ổn định nhất
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

    # --- ĐĂNG KÝ CÁC BLUEPRINTS ---
    with app.app_context():
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
        # Đảm bảo file này chứa hàm register_ai_events đã ép UTF-8 và dùng Gemini SDK
        try:
            from .services.ai_service import register_ai_events
            register_ai_events(socketio)
            print("🤖 Hệ thống AI đã kết nối với SocketIO")
        except Exception as e:
            print(f"❌ Lỗi đăng ký AI Service: {e}")

    return app