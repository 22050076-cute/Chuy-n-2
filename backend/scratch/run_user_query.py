import os
import sys
import json
from sqlalchemy import text

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app.config import engine

query = text("""
SELECT 
    gv.Email AS EmailGiaoVien,
    lh.TenLop,
    hs.HoTen,
    hs.Email
FROM NguoiDung gv
JOIN LopHoc lh ON gv.MaNguoiDung = lh.MaGVCN
JOIN NguoiDung hs ON hs.MaLop = lh.MaLop
WHERE gv.Email IN (
    'gv.6a1@teacher.edunext.vn',
    'gv.7a1@teacher.edunext.vn',
    'gv.8a1@teacher.edunext.vn',
    'gv.9a1@teacher.edunext.vn'
)
""")

with engine.connect() as conn:
    try:
        results = conn.execute(query).fetchall()
        data = [dict(r._mapping) for r in results]
        with open('user_query_results.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Success: Results written to user_query_results.json")
    except Exception as e:
        print(f"Error executing query: {e}")
