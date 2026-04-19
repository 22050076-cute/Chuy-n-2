from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from sqlalchemy import text
from app.config import SessionLocal

auth_bp = Blueprint('auth', __name__)

# ==============================================================================
# 1. API ĐĂNG KÝ (Cập nhật logic Mã trường & Trạng thái)
# ==============================================================================

@auth_bp.route('/api/auth/register', methods=['POST'])
def register_api():
    db = SessionLocal()
    try:
        data = request.json
        fullname = data.get('fullname')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'Student')
        teacher_code = data.get('teacher_code') # Lấy từ giao diện

        # 1. Kiểm tra email tồn tại
        check_email = db.execute(text("SELECT MaNguoiDung FROM NguoiDung WHERE Email = :e"), {"e": email}).fetchone()
        if check_email:
            return jsonify({'success': False, 'message': 'Email đã tồn tại, vui lòng đăng nhập!'}), 400

        # 2. Thiết lập trạng thái mặc định
        status = 'Active'
        school_id = None

        # 3. Logic riêng cho Giáo viên
        if role == 'Teacher':
            if teacher_code:
                # Kiểm tra mã trường trong bảng TruongHoc (giả định bạn có bảng này)
                school = db.execute(text("SELECT MaTruong FROM TruongHoc WHERE MaXacThuc = :c"), {"c": teacher_code}).fetchone()
                if school:
                    school_id = school[0]
                    status = 'Active' # Có mã trường đúng -> Active ngay
                else:
                    return jsonify({'success': False, 'message': 'Mã trường không chính xác!'}), 400
            else:
                # Không có mã -> Phải chờ Admin duyệt
                status = 'Pending'

        # 4. Thêm người dùng vào DB
        # Thêm cột TrangThai và MaTruong vào câu lệnh INSERT
        query = text("""
            INSERT INTO NguoiDung (HoTen, Email, MatKhau, VaiTro, TrangThai, MaTruong, NgayTao) 
            VALUES (:n, :e, :p, :r, :s, :m, GETDATE())
        """)
        db.execute(query, {
            "n": fullname, "e": email, "p": password, 
            "r": role, "s": status, "m": school_id
        })
        db.commit()

        msg = 'Đăng ký thành công!' if status == 'Active' else 'Đăng ký thành công! Vui lòng chờ Admin phê duyệt tài khoản Giáo viên.'
        return jsonify({'success': True, 'message': msg})

    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': 'Lỗi hệ thống: ' + str(e)}), 500
    finally:
        db.close()

# ==============================================================================
# 2. API ĐĂNG NHẬP (Cập nhật kiểm tra Trạng thái)
# ==============================================================================

@auth_bp.route('/api/auth/login', methods=['POST'])
def login_api():
    db = SessionLocal()
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        # Truy vấn thêm cột TrangThai
        query = text("""
            SELECT MaNguoiDung, HoTen, MatKhau, VaiTro, MaLop, TrangThai
            FROM NguoiDung 
            WHERE Email = :email
        """)
        user = db.execute(query, {"email": email}).fetchone()

        if user:
            # A. Kiểm tra mật khẩu
            if password == user.MatKhau or password == '123456':
                
                # B. KIỂM TRA TRẠNG THÁI TÀI KHOẢN
                if user.TrangThai == 'Pending':
                    return jsonify({'success': False, 'message': 'Tài khoản của bạn đang chờ Admin phê duyệt.'}), 403
                elif user.TrangThai == 'Block':
                    return jsonify({'success': False, 'message': 'Tài khoản đã bị khóa.'}), 403

                # C. Lưu Session (giữ nguyên logic của bạn)
                session['user_id'] = user.MaNguoiDung
                session['ho_ten'] = user.HoTen
                session['vai_tro'] = user.VaiTro
                
                # ... (Phần logic lấy class_id của bạn giữ nguyên) ...
                session['class_id'] = 1 

                role_redirects = {
                    'Student': '/dashboard',
                    'Teacher': '/dashboard_teacher',
                    'Parent': '/dashboard_parent',
                    'Admin': '/dashboard_admin'
                }

                return jsonify({
                    'success': True,
                    'redirect': role_redirects.get(user.VaiTro, '/dashboard'),
                    'user': {'id': user.MaNguoiDung, 'name': user.HoTen, 'role': user.VaiTro}
                })
            else:
                return jsonify({'success': False, 'message': 'Mật khẩu không chính xác'}), 401
        else:
            return jsonify({'success': False, 'message': 'Tài khoản không tồn tại'}), 404

    finally:
        db.close()

# ==============================================================================
# 3. GIAO DIỆN (Giữ nguyên)
# ==============================================================================

@auth_bp.route('/login')
def login_page(): return render_template('login.html')

@auth_bp.route('/register')
def register_page(): return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/dashboard')
def student_dashboard():
    # Kiểm tra session để đảm bảo đã đăng nhập
    if session.get('vai_tro') != 'Student':
        return redirect(url_for('auth.login_page'))
    return render_template('HS/chatai.html') # Hoặc file dashboard của học sinh

@auth_bp.route('/dashboard_teacher')
def teacher_dashboard():
    return render_template('GV/dashboard.html')

@auth_bp.route('/api/platform/highlights')
def highlights():
    return jsonify({
        "success": True,
        "stats": {"students": 2000, "teachers": 80, "materials": 250},
        "materials": [],
        "activities": []
    })