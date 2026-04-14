import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import engine
from sqlalchemy import text

tables = ['LopHoc', 'NguoiDung', 'DiemDanh', 'BangDiem', 'PhanCongGiangDay', 'MonHoc', 'LoaiDiem', 'KhoiHoc']

with engine.connect() as conn:
    for table in tables:
        print(f"\n--- {table} ---")
        try:
            res = conn.execute(text(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")).fetchall()
            print([r[0] for r in res])
        except Exception as e:
            print(f"Error inspecting {table}: {e}")
