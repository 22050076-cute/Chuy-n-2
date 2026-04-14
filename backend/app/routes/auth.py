from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from sqlalchemy import text
from app.config import SessionLocal

# Khởi tạo Blueprint cho xác thực
auth_bp = Blueprint('auth', __name__)

# ==============================================================================
# 1. ĐỊNH TUYẾN GIAO DIỆN (RENDER TEMPLATES)
# ==============================================================================

@auth_bp.route('/login')
def login_page():
    """Trả về giao diện đăng nhập phong cách Aurora"""
    return render_template('login.html')

@auth_bp.route('/register')
def register_page():
    """Trả về giao diện đăng ký tài khoản mới"""
    return render_template('register.html')

@auth_bp.route('/forgot-password')
def forgot_password_page():
    """Trả về giao diện quên mật khẩu"""
    return render_template('forgot-password.html')

@auth_bp.route('/logout')
def logout():
    """Đăng xuất và xóa toàn bộ session"""
    session.clear()
    return redirect(url_for('auth.login_page'))

# ==============================================================================
# 2. API XỬ LÝ LOGIC XÁC THỰC
# ==============================================================================

@auth_bp.route('/api/auth/login', methods=['POST'])
def login_api():
    """Xử lý đăng nhập, lưu session và phân quyền"""
    db = SessionLocal()
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'}), 400

        # Truy vấn thông tin người dùng và mã lớp (nếu có)
        query = text("""
            SELECT MaNguoiDung, HoTen, MatKhau, VaiTro, MaLop 
            FROM NguoiDung 
            WHERE Email = :email
        """)
        user = db.execute(query, {"email": email}).fetchone()

        if user:
            # Kiểm tra mật khẩu (Hỗ trợ mật khẩu thật hoặc mật khẩu demo 123456)
            if password == user.MatKhau or password == '123456':
                # --- LƯU THÔNG TIN VÀO SESSION ---
                session['user_id'] = user.MaNguoiDung
                session['ho_ten'] = user.HoTen
                session['vai_tro'] = user.VaiTro
                
                # Logic lấy MaLop thông minh
                class_id = user.MaLop
                if user.VaiTro == 'Teacher':
                    # Nếu là giáo viên, ưu tiên lấy lớp đang chủ nhiệm
                    c_res = db.execute(text("SELECT MaLop FROM LopHoc WHERE MaGVCN = :uid"), {"uid": user.MaNguoiDung}).fetchone()
                    if c_res: class_id = c_res[0]
                elif user.VaiTro == 'Parent':
                    # Nếu là phụ huynh, lấy lớp của con liên kết
                    u_info = db.execute(text("SELECT MaLop FROM NguoiDung WHERE MaNguoiDung = :sid"), {"sid": user.MaHocSinhLienKet if hasattr(user, 'MaHocSinhLienKet') else None}).fetchone()
                    if u_info: class_id = u_info[0]

                session['class_id'] = class_id or 1 # Fallback về lớp 1 cho demo
                
                # Bản đồ chuyển hướng theo vai trò (Đã sửa lỗi dashboard_stuent)
                role_redirects = {
                    'Student': '/dashboard',
                    'Teacher': '/dashboard_teacher',
                    'Parent': '/dashboard_parent',
                    'Admin': '/dashboard_admin'
                }

                return jsonify({
                    'success': True,
                    'redirect': role_redirects.get(user.VaiTro, '/dashboard'),
                    'user': {
                        'id': user.MaNguoiDung,
                        'name': user.HoTen,
                        'role': user.VaiTro
                    }
                })
            else:
                return jsonify({'success': False, 'message': 'Mật khẩu không chính xác'}), 401
        else:
            return jsonify({'success': False, 'message': 'Tài khoản không tồn tại'}), 404

    except Exception as e:
        print(f"❌ Lỗi API Login: {str(e)}")
        return jsonify({'success': False, 'message': 'Lỗi hệ thống'}), 500
    finally:
        db.close()

@auth_bp.route('/api/auth/register', methods=['POST'])
def register_api():
    """Xử lý đăng ký người dùng mới vào SQL Server"""
    db = SessionLocal()
    try:
        data = request.json
        fullname = data.get('fullname')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'Student') # Mặc định là học sinh

        # Kiểm tra email tồn tại
        check_email = db.execute(text("SELECT MaNguoiDung FROM NguoiDung WHERE Email = :e"), {"e": email}).fetchone()
        if check_email:
            return jsonify({'success': False, 'message': 'Email này đã được sử dụng'}), 400

        # Thêm người dùng mới
        query = text("""
            INSERT INTO NguoiDung (HoTen, Email, MatKhau, VaiTro, NgayTao) 
            VALUES (:n, :e, :p, :r, GETDATE())
        """)
        db.execute(query, {"n": fullname, "e": email, "p": password, "r": role})
        db.commit()

        return jsonify({'success': True, 'message': 'Đăng ký tài khoản thành công!'})

    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi API Register: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()