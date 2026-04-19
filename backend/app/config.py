# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Xác định đường dẫn gốc (Root Directory)
# Giả sử file này nằm trong app/config.py, ta cần lùi 1 cấp để ra thư mục chứa .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Config:
    # --- AI CONFIG ---
    GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # --- SECURITY CONFIG ---
    SECRET_KEY = os.getenv("SECRET_KEY", "edunext_secret_key_default_123")
    
    # --- DATABASE CONFIG ---
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("⚠️ [WARNING] DATABASE_URL không tồn tại trong .env!")

    # --- MAIL CONFIG (Nạp hoàn toàn từ .env) ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") # KHÔNG để password cứng ở đây

    # --- APP CONFIG ---
    PORT = int(os.getenv("PORT", 3000))

# 2. Khởi tạo Database với Connection Pooling tối ưu
# pool_size: Số kết nối duy trì sẵn
# max_overflow: Số kết nối tối đa có thể mở thêm khi quá tải
engine = create_engine(
    Config.DATABASE_URL, 
    pool_size=10, 
    max_overflow=20, 
    pool_pre_ping=True, # Tự động kiểm tra kết nối "sống" trước khi dùng
    pool_recycle=1800   # Tự động làm mới kết nối sau 30 phút
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

print(f"🚀 [CONFIG] System Ready | Model: {Config.GEMINI_MODEL}")