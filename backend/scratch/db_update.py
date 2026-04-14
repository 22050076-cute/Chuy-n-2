import sys
import os
# Thêm đường dẫn để import được app.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("Checking and updating KhoHocLieu table...")
    try:
        # Thêm cột MaLop nếu chưa có
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns 
                           WHERE object_id = OBJECT_ID('KhoHocLieu') AND name = 'MaLop')
            BEGIN
                ALTER TABLE KhoHocLieu ADD MaLop INT;
                PRINT 'Added MaLop column';
            END
        """))
        conn.commit()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
