import os
import uuid
from flask import Blueprint, render_template, request, jsonify, session, current_app
from sqlalchemy import text
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import SessionLocal

# Khởi tạo Blueprint cho Học sinh
student_bp = Blueprint('student', __name__)

# ==============================================================================
# 1. ĐỊNH TUYẾN GIAO DIỆN (RENDER TEMPLATES)
# ==============================================================================

@student_bp.route('/dashboard')
def dashboard():
    return render_template('HS/dashboard_student.html', active_page='dashboard')

@student_bp.route('/kho-hoc-lieu')
def kho_hoc_lieu():
    return render_template('HS/khohoclieu.html', active_page='khohoclieu')

@student_bp.route('/bai-tap')
def list_assignments():
    return render_template('HS/baitap.html', active_page='baitap')

@student_bp.route('/bang-thanh-tich')
def bang_thanh_tich():
    return render_template('HS/bangthanhtich.html', active_page='thanhtich')

@student_bp.route('/chat-ai')
def chat_ai():
    return render_template('HS/chatai.html', active_page='chatai')

@student_bp.route('/profile')
def profile():
    return render_template('HS/profile.html', active_page='profile')

@student_bp.route('/thoi-khoa-bieu')
def schedule():
    return render_template('HS/thoikhoabieu.html', active_page='thoikhoabieu')

# ==============================================================================
# 2. API NGHIỆP VỤ HỌC SINH
# ==============================================================================

@student_bp.route('/api/assignment/submit', methods=['POST'])
def submit_assignment():
    """API nộp bài làm: Xử lý cả nội dung text và file đính kèm"""
    db = SessionLocal()
    try:
        student_id = session.get('user_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Phiên đăng nhập hết hạn'}), 401
        
        assignment_id = request.form.get('assignment_id')
        content = request.form.get('content', '')
        
        if not assignment_id:
            return jsonify({'success': False, 'message': 'Thiếu ID bài tập'}), 400
            
        # --- Xử lý File đính kèm ---
        file = request.files.get('file')
        file_path = None
        if file and file.filename != '':
            # Tạo tên file duy nhất để tránh ghi đè bài của người khác
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"SUB_{assignment_id}_{student_id}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # Đường dẫn vật lý trên server
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file.save(os.path.join(upload_folder, unique_filename))
            # Đường dẫn lưu vào Database (để hiển thị trên web)
            file_path = f"/static/uploads/{unique_filename}"
        
        # --- Cập nhật vào Database (Sử dụng logic Upsert) ---
        check_query = text("SELECT MaBaiLam FROM BaiLam WHERE MaBaiTap = :aid AND MaHocSinh = :sid")
        exists = db.execute(check_query, {"aid": assignment_id, "sid": student_id}).fetchone()
        
        if exists:
            # Nếu đã nộp rồi thì cập nhật lại (cho phép nộp đè bài mới)
            update_sql = text("""
                UPDATE BaiLam 
                SET [BaiLam] = :content, 
                    NoiDungBaiLam = :content, 
                    FileDinhKem = COALESCE(:fpath, FileDinhKem), 
                    NgayNop = GETDATE() 
                WHERE MaBaiTap = :aid AND MaHocSinh = :sid
            """)
            db.execute(update_sql, {"content": content, "aid": assignment_id, "sid": student_id, "fpath": file_path})
        else:
            # Nếu chưa nộp thì thêm mới
            insert_sql = text("""
                INSERT INTO BaiLam (MaBaiTap, MaHocSinh, [BaiLam], NoiDungBaiLam, FileDinhKem, NgayNop)
                VALUES (:aid, :sid, :content, :content, :fpath, GETDATE())
            """)
            db.execute(insert_sql, {"aid": assignment_id, "sid": student_id, "content": content, "fpath": file_path})
        
        db.commit()
        return jsonify({'success': True, 'message': 'Nộp bài thành công!'})
        
    except Exception as e:
        db.rollback()
        print(f"DEBUG Error submit: {str(e)}")
        return jsonify({'success': False, 'message': 'Lỗi máy chủ'}), 500
    finally:
        db.close()

@student_bp.route('/api/resource/rate', methods=['POST'])
def rate_resource():
    """API đánh giá học liệu: Mỗi học sinh chỉ được đánh giá 1 lần/tài liệu"""
    db = SessionLocal()
    try:
        data = request.json
        res_id = data.get('resource_id')
        student_id = session.get('user_id')
        stars = int(data.get('stars', 5))
        
        if not student_id:
            return jsonify({"success": False, "message": "Vui lòng đăng nhập"}), 401
            
        # Kiểm tra xem đã tồn tại đánh giá chưa
        check = db.execute(text("SELECT MaDanhGia FROM DanhGiaHocLieu WHERE MaTaiLieu = :rid AND MaHocSinh = :sid"),
                           {"rid": res_id, "sid": student_id}).fetchone()
        
        if check:
            db.execute(text("UPDATE DanhGiaHocLieu SET SoSao = :stars WHERE MaDanhGia = :did"),
                       {"stars": stars, "did": check[0]})
        else:
            db.execute(text("INSERT INTO DanhGiaHocLieu (MaTaiLieu, MaHocSinh, SoSao) VALUES (:rid, :sid, :stars)"),
                       {"rid": res_id, "sid": student_id, "stars": stars})
            
        db.commit()
        return jsonify({"success": True, "message": "Đã lưu đánh giá"})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()