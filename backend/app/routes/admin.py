from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from sqlalchemy import text
from app.config import SessionLocal

# Khởi tạo Blueprint
admin_bp = Blueprint('admin', __name__)

def is_admin():
    """Kiểm tra quyền Admin từ session"""
    # Debug: in ra session để kiểm tra nếu cần
    # print(f"DEBUG: Current Session Role: {session.get('vai_tro')}")
    return session.get('vai_tro') == 'Admin'

@admin_bp.route('/dashboard_admin')
def dashboard():
    """Trang dashboard chính cho Admin"""
    if not is_admin():
        # Nếu không phải Admin, chuyển về trang login của blueprint 'auth'
        return redirect(url_for('auth.login_page'))
    
    db = SessionLocal()
    try:
        # 1. Thống kê tổng quan (Sử dụng lệnh COUNT của SQL Server)
        stats = {
            'total_users': db.execute(text("SELECT COUNT(*) FROM NguoiDung")).scalar() or 0,
            'pending_teachers': db.execute(text("SELECT COUNT(*) FROM NguoiDung WHERE VaiTro='Teacher' AND TrangThai='Pending'")).scalar() or 0,
            'total_schools': db.execute(text("SELECT COUNT(*) FROM TruongHoc")).scalar() or 0,
            'total_students': db.execute(text("SELECT COUNT(*) FROM NguoiDung WHERE VaiTro='Student'")).scalar() or 0
        }

        # 2. Danh sách giáo viên chờ duyệt
        pending_query = text("""
            SELECT MaNguoiDung, HoTen, Email, NgayTao 
            FROM NguoiDung 
            WHERE VaiTro='Teacher' AND TrangThai='Pending'
            ORDER BY NgayTao DESC
        """)
        pending_list = db.execute(pending_query).fetchall()

        # 3. Danh sách các trường học
        schools = db.execute(text("SELECT * FROM TruongHoc ORDER BY TenTruong")).fetchall()

        # Đảm bảo đường dẫn template là 'admin/dashboard.html'
        return render_template('admin/dashboard.html', stats=stats, pending_list=pending_list, schools=schools)
    
    except Exception as e:
        print(f"❌ Lỗi Admin Dashboard: {str(e)}")
        return f"Lỗi hệ thống: {str(e)}", 500
    finally:
        db.close()

@admin_bp.route('/api/admin/user-status', methods=['POST'])
def update_status():
    """API phê duyệt hoặc từ chối tài khoản"""
    if not is_admin():
        return jsonify({'success': False, 'message': 'Không có quyền truy cập'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    status = data.get('status') # 'Active' hoặc 'Rejected'

    if not user_id or not status:
        return jsonify({'success': False, 'message': 'Thiếu dữ liệu'}), 400

    db = SessionLocal()
    try:
        query = text("UPDATE NguoiDung SET TrangThai = :s WHERE MaNguoiDung = :id")
        db.execute(query, {"s": status, "id": user_id})
        db.commit()
        return jsonify({'success': True, 'message': f'Đã cập nhật trạng thái: {status}'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()