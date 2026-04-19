# -*- coding: utf-8 -*-
import os
import uuid
from flask import Blueprint, render_template, request, jsonify, session, current_app
from sqlalchemy import text
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path
from app.config import SessionLocal

teacher_bp = Blueprint('teacher', __name__)

# Helper: Lấy MaLop của giáo viên hiện tại
def get_teacher_class(db, teacher_id):
    res = db.execute(text("SELECT MaLop FROM NguoiDung WHERE MaNguoiDung = :uid"), {"uid": teacher_id}).fetchone()
    return res.MaLop if res and res.MaLop else None

# ==============================================================================
# 1. GIAO DIỆN
# ==============================================================================

@teacher_bp.route('/dashboard_teacher')
def dashboard():
    if not session.get('user_id'): 
        return render_template('login.html')
    return render_template('GV/dashboard_teacher.html', active_page='dashboard')

@teacher_bp.route('/teacher/class-ledger')
def class_ledger():
    db = SessionLocal()
    teacher_id = session.get('user_id')
    if not teacher_id: return "Vui lòng đăng nhập lại", 401
    
    try:
        class_id = get_teacher_class(db, teacher_id)
        if not class_id: return "Bạn chưa được phân công chủ nhiệm", 404

        query = text("""
            SELECT 
                nd.MaNguoiDung, nd.HoTen, nd.Email,
                (SELECT TOP 1 DiemSo FROM BangDiem bd WHERE bd.MaHocSinh = nd.MaNguoiDung AND bd.MaMonHoc = 1 AND bd.MaLoai = 4) as DiemToan,
                (SELECT ISNULL(SUM(DiemXP), 0) FROM NhatKyReNep nk WHERE nk.MaHocSinh = nd.MaNguoiDung) as TongXP,
                (SELECT COUNT(*) FROM DiemDanh dd WHERE dd.MaHocSinh = nd.MaNguoiDung AND dd.TrangThai IN ('VangCP', 'VangKP')) as SoBuoiVang
            FROM NguoiDung nd
            WHERE nd.MaLop = :cid AND nd.VaiTro = 'Student'
            ORDER BY nd.HoTen ASC
        """)
        students_data = db.execute(query, {"cid": class_id}).fetchall()
        return render_template('GV/class_ledger.html', students=students_data, active_page='ledger')
    finally:
        db.close()

# ==============================================================================
# 2. NGHIỆP VỤ ĐIỂM DANH & RÈN LUYỆN
# ==============================================================================

@teacher_bp.route('/api/teacher/attendance', methods=['GET', 'POST'])
def handle_attendance():
    db = SessionLocal()
    teacher_id = session.get('user_id')
    try:
        class_id = get_teacher_class(db, teacher_id)
        
        if request.method == 'GET':
            date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            query = text("""
                SELECT nd.MaNguoiDung, nd.HoTen, ISNULL(dd.TrangThai, 'DiHoc') as TrangThai, dd.GhiChu
                FROM NguoiDung nd
                LEFT JOIN DiemDanh dd ON nd.MaNguoiDung = dd.MaHocSinh AND dd.NgayDiemDanh = :date
                WHERE nd.MaLop = :cid AND nd.VaiTro = 'Student'
            """)
            results = db.execute(query, {"date": date_str, "cid": class_id}).fetchall()
            return jsonify({"success": True, "data": [dict(r._mapping) for r in results]})
        
        else: # POST: Lưu điểm danh
            data = request.json
            records = data.get('records', [])
            date_val = data.get('date', datetime.now().strftime('%Y-%m-%d'))

            for rec in records:
                # Dùng Merge hoặc Check để tránh lỗi khóa chính
                check = db.execute(text("SELECT MaDiemDanh FROM DiemDanh WHERE MaHocSinh = :sid AND NgayDiemDanh = :date"), 
                                   {"sid": rec['student_id'], "date": date_val}).fetchone()
                
                if check:
                    db.execute(text("UPDATE DiemDanh SET TrangThai = :st, GhiChu = :note, NguoiDiemDanh = :tid WHERE MaDiemDanh = :did"),
                               {"st": rec['status'], "note": rec.get('reason',''), "tid": teacher_id, "did": check[0]})
                else:
                    db.execute(text("INSERT INTO DiemDanh (MaHocSinh, MaLop, NgayDiemDanh, TrangThai, GhiChu, NguoiDiemDanh) VALUES (:sid, :cid, :date, :st, :note, :tid)"),
                               {"sid": rec['student_id'], "cid": class_id, "date": date_val, "st": rec['status'], "note": rec.get('reason',''), "tid": teacher_id})
            db.commit()
            return jsonify({"success": True, "message": "Đã lưu thông tin điểm danh"})
    finally:
        db.close()

# ==============================================================================
# 3. QUẢN LÝ BÀI TẬP & ĐƠN TỪ
# ==============================================================================

@teacher_bp.route('/api/assignment/create', methods=['POST'])
def create_assignment():
    db = SessionLocal()
    try:
        teacher_id = session.get('user_id')
        class_id = request.form.get('class_id') or get_teacher_class(db, teacher_id)
        
        file = request.files.get('file')
        file_path = None

        if file and file.filename != '':
            ext = Path(file.filename).suffix
            filename = secure_filename(f"lesson_{uuid.uuid4().hex[:6]}{ext}")
            upload_dir = Path(current_app.root_path) / 'static' / 'uploads'
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            file.save(str(upload_dir / filename))
            file_path = f"/static/uploads/{filename}"

        db.execute(text("""
            INSERT INTO BaiTap (TieuDe, NoiDung, HanNop, MaPhanCong, LoaiBai, FileDinhKem)
            VALUES (:t, :c, :d, :cid, 'TuLuan', :f)
        """), {
            "t": request.form.get('title'),
            "c": request.form.get('content'),
            "d": request.form.get('deadline'),
            "cid": class_id,
            "f": file_path
        })
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()

@teacher_bp.route('/api/teacher/leave-requests/update', methods=['POST'])
def update_leave_status():
    db = SessionLocal()
    try:
        data = request.json
        rid = data.get('id')
        status = data.get('status') # 'DaDuyet' hoặc 'TuChoi'
        comment = data.get('comment', '')
        teacher_id = session.get('user_id')

        # 1. Cập nhật trạng thái
        db.execute(text("UPDATE DonXinNghiHoc SET TrangThai = :st, PhanHoiGiaoVien = :comment WHERE MaDon = :rid"),
                   {"st": status, "comment": comment, "rid": rid})

        # 2. Lấy thông tin để báo cho phụ huynh
        info = db.execute(text("SELECT MaHocSinh, NgayNghi FROM DonXinNghiHoc WHERE MaDon = :rid"), {"rid": rid}).fetchone()
        if info:
            # Tìm phụ huynh liên kết
            parent = db.execute(text("SELECT MaNguoiDung FROM NguoiDung WHERE MaHocSinhLienKet = :sid AND VaiTro = 'Parent'"), 
                               {"sid": info.MaHocSinh}).fetchone()
            if parent:
                msg = f"[EduNext] Đơn nghỉ ngày {info.NgayNghi.strftime('%d/%m/%Y')} của con đã được {status}. Ghi chú: {comment}"
                db.execute(text("""
                    INSERT INTO TraoDoiChuNhiem (MaNguoiGui, MaNguoiNhan, NoiDung, ThoiGian, TrangThai) 
                    VALUES (:tid, :pid, :msg, GETDATE(), 'ChuaDoc')
                """), {"tid": teacher_id, "pid": parent.MaNguoiDung, "msg": msg})
        
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()