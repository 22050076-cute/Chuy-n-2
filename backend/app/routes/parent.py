from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import text
from app.config import SessionLocal
from datetime import datetime

# Khởi tạo Blueprint cho Phụ huynh
parent_bp = Blueprint('parent', __name__)

# ==============================================================================
# 1. ĐỊNH TUYẾN GIAO DIỆN (RENDER TEMPLATES)
# ==============================================================================

@parent_bp.route('/dashboard_parent')
def dashboard():
    """Giao diện tổng quan của Phụ huynh"""
    return render_template('PH/dashboard_parent.html', active_page='dashboard')

@parent_bp.route('/parent/gradebook')
def gradebook():
    """Trang xem điểm và phân tích AI về kết quả học tập của con"""
    return render_template('PH/diem-so.html', active_page='gradebook')

@parent_bp.route('/parent/homework')
def homework():
    """Theo dõi danh sách bài tập về nhà của con"""
    return render_template('PH/bai-tap.html', active_page='homework')

@parent_bp.route('/parent/wallet')
def wallet():
    """Giao diện ví điện tử học đường (Edu-Wallet)"""
    return render_template('PH/vi-dien-tu.html', active_page='wallet')

@parent_bp.route('/parent/chat')
def chat():
    """Trang nhắn tin trực tiếp với Giáo viên chủ nhiệm"""
    return render_template('PH/chat.html', active_page='chat')

# ==============================================================================
# 2. API NGHIỆP VỤ PHỤ HUYNH
# ==============================================================================

@parent_bp.route('/api/parent/dashboard', methods=['GET'])
def get_parent_data():
    """API lấy thông tin định danh: Tên con, Lớp, Giáo viên chủ nhiệm"""
    db = SessionLocal()
    parent_id = session.get('user_id')
    if not parent_id:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    try:
        # Truy vấn thông tin bắc cầu từ Phụ huynh -> Học sinh -> Lớp -> GVCN
        query = text("""
            SELECT 
                p.HoTen AS TenPhuHuynh,
                hs.MaNguoiDung AS MaHocSinh,
                hs.HoTen AS TenHocSinh,
                lh.TenLop,
                gv.HoTen AS TenGVCN
            FROM NguoiDung p
            JOIN NguoiDung hs ON p.MaHocSinhLienKet = hs.MaNguoiDung
            LEFT JOIN LopHoc lh ON hs.MaLop = lh.MaLop
            LEFT JOIN NguoiDung gv ON lh.MaGVCN = gv.MaNguoiDung
            WHERE p.MaNguoiDung = :pid
        """)
        result = db.execute(query, {"pid": parent_id}).fetchone()

        if result:
            return jsonify({
                "success": True,
                "data": {
                    "parent_name": result.TenPhuHuynh,
                    "student_name": result.TenHocSinh,
                    "class_name": result.TenLop or "Chưa phân lớp",
                    "teacher_name": result.TenGVCN or "Chưa xác định"
                }
            })
        return jsonify({"success": False, "message": "Không tìm thấy dữ liệu"}), 404
    finally:
        db.close()

@parent_bp.route('/api/parent/leave-request', methods=['GET', 'POST'])
def handle_leave_request():
    """API Phụ huynh gửi đơn xin nghỉ hoặc xem lịch sử xin nghỉ của con"""
    db = SessionLocal()
    parent_id = session.get('user_id')
    
    try:
        # Lấy ID học sinh liên kết
        child = db.execute(text("SELECT MaHocSinhLienKet FROM NguoiDung WHERE MaNguoiDung = :pid"), 
                           {"pid": parent_id}).fetchone()
        if not child or not child[0]:
            return jsonify({"success": False, "message": "Tài khoản chưa liên kết học sinh"}), 400
        
        student_id = child[0]

        if request.method == 'POST':
            data = request.json
            db.execute(text("""
                INSERT INTO DonXinNghiHoc (MaHocSinh, LyDo, NgayNghi, TrangThai, NgayTao) 
                VALUES (:sid, :reason, :date, N'ChoDuyet', GETDATE())
            """), {"sid": student_id, "reason": data['reason'], "date": data['date']})
            db.commit()
            return jsonify({"success": True, "message": "Gửi đơn thành công"})
        
        else: # GET: Xem lịch sử đơn của con
            results = db.execute(text("SELECT * FROM DonXinNghiHoc WHERE MaHocSinh = :sid ORDER BY NgayNghi DESC"), 
                                 {"sid": student_id}).fetchall()
            return jsonify({"success": True, "data": [dict(r._mapping) for r in results]})
            
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

@parent_bp.route('/api/parent/chat-contacts', methods=['GET'])
def get_parent_contacts():
    """API lấy danh bạ (Mặc định là GVCN của con)"""
    db = SessionLocal()
    parent_id = session.get('user_id')
    try:
        # Tìm GVCN thông qua lớp của con
        query = text("""
            SELECT gv.MaNguoiDung, gv.HoTen 
            FROM NguoiDung p
            JOIN NguoiDung hs ON p.MaHocSinhLienKet = hs.MaNguoiDung
            JOIN LopHoc lh ON hs.MaLop = lh.MaLop
            JOIN NguoiDung gv ON lh.MaGVCN = gv.MaNguoiDung
            WHERE p.MaNguoiDung = :pid AND gv.VaiTro = 'Teacher'
        """)
        teacher = db.execute(query, {"pid": parent_id}).fetchone()
        
        contacts = []
        if teacher:
            contacts.append({
                "MaNguoiDung": teacher.MaNguoiDung,
                "HoTen": teacher.HoTen,
                "Role": "GVCN"
            })
        return jsonify({"success": True, "data": contacts})
    finally:
        db.close()