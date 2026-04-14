import os
import uuid
from flask import Blueprint, render_template, request, jsonify, session, current_app
from sqlalchemy import text
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import SessionLocal

# Khởi tạo Blueprint cho Giáo viên
teacher_bp = Blueprint('teacher', __name__)

# ==============================================================================
# 1. ĐỊNH TUYẾN GIAO DIỆN (RENDER TEMPLATES)
# ==============================================================================

@teacher_bp.route('/dashboard_teacher')
def dashboard():
    """Trang chủ quản trị của Giáo viên"""
    return render_template('GV/dashboard_teacher.html', active_page='dashboard')

@teacher_bp.route('/teacher/attendance')
def attendance_page():
    """Giao diện điểm danh lớp học"""
    return render_template('GV/attendance.html', active_page='attendance')

@teacher_bp.route('/teacher/gradebook')
def gradebook_page():
    """Giao diện sổ điểm môn học"""
    return render_template('GV/gradebook.html', active_page='gradebook')

@teacher_bp.route('/teacher/class-ledger')
def class_ledger():
    """Giao diện 'Số cái' lớp học (Thống kê tổng hợp học sinh)"""
    db = SessionLocal()
    teacher_id = session.get('user_id')
    if not teacher_id:
        return "Vui lòng đăng nhập lại", 401
    
    try:
        # Lấy MaLop của Giáo viên chủ nhiệm
        u_res = db.execute(text("SELECT MaLop FROM NguoiDung WHERE MaNguoiDung = :uid"), {"uid": teacher_id}).fetchone()
        class_id = u_res.MaLop if u_res and u_res.MaLop else 1

        query = text("""
            SELECT 
                nd.MaNguoiDung, 
                nd.HoTen, 
                nd.Email,
                (SELECT TOP 1 DiemSo FROM BangDiem bd WHERE bd.MaHocSinh = nd.MaNguoiDung AND bd.MaMonHoc = 1 AND bd.MaLoai = 4) as DiemToan,
                (SELECT ISNULL(SUM(DiemXP), 0) FROM NhatKyReNep nk WHERE nk.MaHocSinh = nd.MaNguoiDung) as TongXP,
                (SELECT COUNT(*) FROM DiemDanh dd WHERE dd.MaHocSinh = nd.MaNguoiDung AND dd.TrangThai IN (N'VangCP', N'VangKP')) as SoBuoiVang
            FROM NguoiDung nd
            WHERE nd.MaLop = :cid AND nd.VaiTro = 'Student'
            ORDER BY nd.HoTen ASC
        """)
        students_data = db.execute(query, {"cid": class_id}).fetchall()
        return render_template('GV/class_ledger.html', students=students_data, active_page='ledger')
    finally:
        db.close()

# ==============================================================================
# 2. API NGHIỆP VỤ QUẢN LÝ LỚP HỌC
# ==============================================================================

@teacher_bp.route('/api/teacher/attendance', methods=['GET', 'POST'])
def handle_attendance():
    """Lấy danh sách điểm danh hoặc lưu dữ liệu điểm danh"""
    db = SessionLocal()
    try:
        if request.method == 'GET':
            date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            class_id = request.args.get('class_id') or session.get('class_id', 1)
            
            query = text("""
                SELECT nd.MaNguoiDung, nd.HoTen, dd.TrangThai, dd.GhiChu
                FROM NguoiDung nd
                LEFT JOIN DiemDanh dd ON nd.MaNguoiDung = dd.MaHocSinh AND dd.NgayDiemDanh = :date
                WHERE nd.MaLop = :cid AND nd.VaiTro = 'Student'
            """)
            results = db.execute(query, {"date": date_str, "cid": class_id}).fetchall()
            return jsonify({"success": True, "data": [dict(r._mapping) for r in results]})
        
        else: # POST: Lưu điểm danh
            data = request.json
            records = data.get('records', [])
            date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
            teacher_id = session.get('user_id', 2)

            for rec in records:
                # Kiểm tra tồn tại để UPDATE hoặc INSERT
                check = db.execute(text("SELECT MaDiemDanh FROM DiemDanh WHERE MaHocSinh = :sid AND NgayDiemDanh = :date"), 
                                   {"sid": rec['student_id'], "date": date_str}).fetchone()
                if check:
                    db.execute(text("UPDATE DiemDanh SET TrangThai = :st, GhiChu = :note, NguoiDiemDanh = :tid WHERE MaDiemDanh = :did"),
                               {"st": rec['status'], "note": rec.get('reason',''), "tid": teacher_id, "did": check[0]})
                else:
                    db.execute(text("INSERT INTO DiemDanh (MaHocSinh, MaLop, NgayDiemDanh, TrangThai, GhiChu, NguoiDiemDanh) VALUES (:sid, :cid, :date, :st, :note, :tid)"),
                               {"sid": rec['student_id'], "cid": session.get('class_id', 1), "date": date_str, "st": rec['status'], "note": rec.get('reason',''), "tid": teacher_id})
            db.commit()
            return jsonify({"success": True, "message": "Lưu điểm danh thành công"})
    finally:
        db.close()

@teacher_bp.route('/api/teacher/conduct/update', methods=['POST'])
def update_conduct():
    """Cập nhật điểm nề nếp (XP)"""
    db = SessionLocal()
    try:
        data = request.json
        db.execute(text("INSERT INTO NhatKyReNep (MaHocSinh, NoiDung, DiemXP, LoaiLog, NgayGhi) VALUES (:sid, :reason, :xp, :type, GETDATE())"),
                   {"sid": data['student_id'], "reason": data['reason'], "xp": data['xp'], "type": "Thuong" if int(data['xp']) > 0 else "Phat"})
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

# ==============================================================================
# 3. API QUẢN LÝ BÀI TẬP & ĐƠN XIN NGHỈ
# ==============================================================================

@teacher_bp.route('/api/assignment/create', methods=['POST'])
def create_assignment():
    """Giao bài tập mới (LMS)"""
    db = SessionLocal()
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        class_id = request.form.get('class_id')
        file = request.files.get('file')
        file_path = None

        if file:
            filename = secure_filename(f"lesson_{uuid.uuid4().hex}_{file.filename}")
            file.save(os.path.join(current_app.root_path, 'static/uploads', filename))
            file_path = f"/static/uploads/{filename}"

        db.execute(text("""
            INSERT INTO BaiTap (TieuDe, NoiDung, HanNop, MaPhanCong, LoaiBai, FileDinhKem)
            VALUES (:t, :c, :d, :cid, 'TuLuan', :f)
        """), {"t": title, "c": content, "d": request.form.get('deadline'), "cid": class_id, "f": file_path})
        db.commit()
        return jsonify({'success': True})
    finally:
        db.close()

@teacher_bp.route('/api/teacher/leave-requests/update', methods=['POST'])
def update_leave_status():
    """Duyệt đơn xin nghỉ và gửi thông báo tự động cho Phụ huynh"""
    db = SessionLocal()
    try:
        data = request.json
        rid, status, comment = data.get('id'), data.get('status'), data.get('comment', '')
        teacher_id = session.get('user_id')

        # 1. Cập nhật trạng thái đơn
        db.execute(text("UPDATE DonXinNghiHoc SET TrangThai = :st, PhanHoiGiaoVien = :comment WHERE MaDon = :rid"),
                   {"st": status, "comment": comment, "rid": rid})

        # 2. Gửi tin nhắn thông báo tự động vào bảng TraoDoiChuNhiem
        info = db.execute(text("SELECT MaHocSinh, NgayNghi FROM DonXinNghiHoc WHERE MaDon = :rid"), {"rid": rid}).fetchone()
        if info:
            parent = db.execute(text("SELECT MaNguoiDung FROM NguoiDung WHERE MaHocSinhLienKet = :sid"), {"sid": info[0]}).fetchone()
            if parent:
                msg = f"[Hệ thống] Đơn nghỉ ngày {info[1]} đã được {status}. {comment}"
                db.execute(text("INSERT INTO TraoDoiChuNhiem (MaNguoiGui, MaNguoiNhan, NoiDung, ThoiGian, TrangThai) VALUES (:tid, :pid, :msg, GETDATE(), 'DaDoc')"),
                           {"tid": teacher_id, "pid": parent[0], "msg": msg})
        
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()