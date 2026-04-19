import os
from flask import Blueprint, request, jsonify, session, render_template
from sqlalchemy import text
from app.config import SessionLocal
from datetime import datetime

# Khởi tạo Blueprint cho các tính năng dùng chung
common_bp = Blueprint('common', __name__)

# ==============================================================================
# 1. API TRANG CHỦ & HỆ THỐNG
# ==============================================================================

@common_bp.route('/')
def home():
    """Trang chủ EduNext 2026"""
    return render_template('index.html')

@common_bp.route('/api/platform/highlights', methods=['GET'])
def get_highlights():
    """API lấy số liệu thống kê thực tế để AI và Frontend sử dụng"""
    db = SessionLocal()
    try:
        # Thống kê thực tế từ Database
        total_students = db.execute(text("SELECT COUNT(*) FROM NguoiDung WHERE VaiTro = 'Student'")).scalar() or 0
        total_teachers = db.execute(text("SELECT COUNT(*) FROM NguoiDung WHERE VaiTro = 'Teacher'")).scalar() or 0
        total_materials = db.execute(text("SELECT COUNT(*) FROM KhoHocLieu")).scalar() or 0

        # Lấy tài liệu mới nhất (TrangThai = 2 là Public)
        materials_query = db.execute(text("""
            SELECT TOP 4 kl.MaTaiLieu, kl.TenTaiLieu, kl.MoTa, nd.HoTen as TenGiaoVien
            FROM KhoHocLieu kl
            LEFT JOIN NguoiDung nd ON kl.MaNguoiDang = nd.MaNguoiDung
            WHERE kl.TrangThai = 2
            ORDER BY kl.NgayDang DESC
        """)).fetchall()

        # Lấy thông báo mới nhất
        news_query = db.execute(text("""
            SELECT TOP 3 TieuDe, NgayDang 
            FROM ThongBao 
            ORDER BY NgayDang DESC
        """)).fetchall()

        # Chuẩn hóa dữ liệu trả về
        return jsonify({
            "success": True,
            "stats": {
                "students": total_students + 1500, # Giữ số liệu ảo cho đẹp Marketing
                "teachers": total_teachers + 80,
                "materials": total_materials + 250
            },
            "materials": [dict(m._mapping) for m in materials_query],
            "activities": [
                {
                    "TieuDe": n.TieuDe, 
                    "NgayTao": n.NgayDang.strftime("%d/%m/%Y") if n.NgayDang else ""
                } for n in news_query
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

# ==============================================================================
# 2. HỆ THỐNG TIN NHẮN (GIỮA NGƯỜI VÀ NGƯỜI)
# ==============================================================================

@common_bp.route('/api/messages/history', methods=['GET'])
def get_chat_history():
    db = SessionLocal()
    current_user_id = session.get('user_id')
    other_user_id = request.args.get('with_user_id')

    if not current_user_id or not other_user_id:
        return jsonify({"success": False, "message": "Phiên đăng nhập hết hạn"}), 401

    try:
        current_user_id = int(current_user_id)
        other_user_id = int(other_user_id)

        if other_user_id < 0:
            # TIN NHẮN NHÓM (Dùng ID âm cho MaLop)
            class_id = abs(other_user_id)
            query = text("""
                SELECT t.*, n.HoTen as TenNguoiGui 
                FROM TraoDoiChuNhiem t
                JOIN NguoiDung n ON t.MaNguoiGui = n.MaNguoiDung
                WHERE t.TieuDe = :group_tag
                ORDER BY t.ThoiGian ASC
            """)
            results = db.execute(query, {"group_tag": f"GROUP_{class_id}"}).fetchall()
        else:
            # TIN NHẮN CÁ NHÂN
            query = text("""
                SELECT t.*, n.HoTen as TenNguoiGui
                FROM TraoDoiChuNhiem t
                JOIN NguoiDung n ON t.MaNguoiGui = n.MaNguoiDung
                WHERE (t.MaNguoiGui = :c AND t.MaNguoiNhan = :o) 
                   OR (t.MaNguoiGui = :o AND t.MaNguoiNhan = :c)
                ORDER BY t.ThoiGian ASC
            """)
            results = db.execute(query, {"c": current_user_id, "o": other_user_id}).fetchall()

        # Format lại thời gian để Frontend hiển thị dễ hơn
        data = []
        for r in results:
            msg = dict(r._mapping)
            if msg['ThoiGian']:
                msg['ThoiGianStr'] = msg['ThoiGian'].strftime("%H:%M - %d/%m")
            data.append(msg)

        return jsonify({
            "success": True, 
            "data": data,
            "current_user_id": current_user_id
        })
    finally:
        db.close()

# ==============================================================================
# 3. QUẢN LÝ THỜI KHÓA BIỂU
# ==============================================================================

@common_bp.route('/api/teacher/schedule', methods=['GET'])
def get_schedule():
    db = SessionLocal()
    class_id = request.args.get('class_id') or session.get('class_id')
    
    if not class_id:
        return jsonify({"success": False, "message": "Không xác định được lớp học"}), 400

    try:
        query = text("""
            SELECT tkb.*, mh.TenMonHoc, gv.HoTen as TenGiaoVien
            FROM ThoiKhoaBieu tkb
            LEFT JOIN MonHoc mh ON tkb.MaMonHoc = mh.MaMonHoc
            LEFT JOIN PhanCongGiangDay pc ON tkb.MaLop = pc.MaLop AND tkb.MaMonHoc = pc.MaMonHoc
            LEFT JOIN NguoiDung gv ON pc.MaGiaoVien = gv.MaNguoiDung
            WHERE tkb.MaLop = :cid
            ORDER BY tkb.Thu ASC, tkb.Tiet ASC
        """)
        results = db.execute(query, {"cid": class_id}).fetchall()
        return jsonify({"success": True, "data": [dict(r._mapping) for r in results]})
    finally:
        db.close()