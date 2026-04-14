import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

class Config:
    """Cấu hình các tham số hệ thống cho EduNext Platform"""
    
    # 1. Khóa bí mật dùng cho Session và mã hóa Cookie
    SECRET_KEY = "edunext_secret_key_2026_master"
    
    # 2. Cấu hình AI Gemini (Sử dụng Key mới nhất bạn cung cấp)
    GENAI_API_KEY = "AIzaSyCHJAle_x1g9BmkCxQvogszAZIX3nAFM78"
    
    # 3. Cấu hình SQL Server (Sử dụng Driver ODBC 17)
    # Cú pháp: mssql+pyodbc://[user]:[pass]@[host]/[database]?driver=ODBC+Driver+17+for+SQL+Server
    # Nếu máy bạn dùng Windows Authentication, hãy thêm: &trusted_connection=yes
 # Sử dụng Windows Authentication (không cần user sa/mật khẩu)
    DATABASE_URL = "mssql+pyodbc://HMINH\HA_MINH/LopHocSo?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    
    # 4. Cấu hình Hệ thống Gửi Email (Sử dụng App Password của Gmail)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'thcsedunext@gmail.com'
    MAIL_PASSWORD = 'weyb mhnn lcwp lrlc'  # App Password 16 ký tự
    MAIL_DEFAULT_SENDER = ('EduNext Platform', 'thcsedunext@gmail.com')

# ==============================================================================
# KHỞI TẠO CÁC ĐỐI TƯỢNG KẾT NỐI DATABASE
# ==============================================================================

# Tạo Engine kết nối
try:
    engine = create_engine(
        Config.DATABASE_URL, 
        pool_size=10, 
        max_overflow=20,
        pool_recycle=3600
    )
    # SessionLocal: Dùng để tạo ra các phiên truy vấn (session) trong Routes
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Base: Lớp cha cho mô hình ORM (nếu bạn dùng Class-based Models)
    Base = declarative_base()
    
    print("✅ Hệ thống kết nối Database đã sẵn sàng.")
except Exception as e:
    print(f"❌ Lỗi cấu hình kết nối Database: {e}")