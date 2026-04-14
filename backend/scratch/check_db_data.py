from app.config import SessionLocal
from sqlalchemy import text

def check_db():
    db = SessionLocal()
    try:
        print("--- KIEM TRA DU LIEU NGUOI DUNG ---")
        
        # 1. Kiem tra Giao vien
        print("\n[Giao vien]")
        teachers = db.execute(text("SELECT MaNguoiDung, HoTen, Email, MaLop FROM NguoiDung WHERE VaiTro = 'Teacher'")).fetchall()
        for t in teachers:
            print(f"ID: {t.MaNguoiDung} | Ten: {t.HoTen} | Email: {t.Email} | MaLop: {t.MaLop}")
            
        # 2. Kiem tra Hoc sinh
        print("\n[Hoc sinh]")
        students = db.execute(text("SELECT MaNguoiDung, HoTen, MaLop FROM NguoiDung WHERE VaiTro = 'Student'")).fetchall()
        if not students:
            print("(!) Khong co hoc sinh nao trong bảng NguoiDung")
        for s in students:
            print(f"ID: {s.MaNguoiDung} | Ten: {s.HoTen} | MaLop: {s.MaLop}")
            
        # 3. Kiem tra Lop hoc
        print("\n[Lop hoc]")
        classes = db.execute(text("SELECT MaLop, TenLop FROM LopHoc")).fetchall()
        for c in classes:
            print(f"MaLop: {c.MaLop} | TenLop: {c.TenLop}")
            
    except Exception as e:
        print(f"Loi: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    check_db()
