import google.generativeai as genai
from flask_socketio import emit
from sqlalchemy import text
from app.config import SessionLocal, Config

# 1. Cấu hình AI Gemini
genai.configure(api_key=Config.GENAI_API_KEY)

# Sau dòng genai.configure(api_key=Config.GENAI_API_KEY)
try:
    print("--- 🔍 ĐANG KIỂM TRA CÁC MODEL KHẢ DỤNG ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Model: {m.name}")
    
    # In ra model mà mình đang chỉ định dùng
    print(f"🚀 Hệ thống EduNext đang cố gắng kết nối với: models/gemini-1.5-flash")
    print("------------------------------------------")
except Exception as e:
    print(f"❌ Không thể liệt kê model: {e}")

# 2. Thiết lập Model (Sửa lại cách gọi để tránh lỗi 404)
# Mình khai báo Model ngay trong hàm hoặc dùng một instance chuẩn
def get_model():
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }

    # Thiết lập bộ lọc an toàn (Chỉnh về BLOCK_ONLY_HIGH để AI linh hoạt hơn)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]

    return genai.GenerativeModel(
        model_name='models/gemini-pro-latest', # Nếu vẫn lỗi 404, thử đổi thành 'models/gemini-1.5-flash'
        generation_config=generation_config,
        safety_settings=safety_settings
    )

model_ai = get_model()

def register_ai_events(socketio):
    """Đăng ký các sự kiện Realtime Chat AI qua Socket.IO"""

    # --- [A] EVENT: GEMINI MENTOR (DÀNH CHO GIÁO VIÊN) ---
    @socketio.on('ask_teacher_ai')
    def handle_teacher_ai(data):
        user_id = data.get('userId')
        session_id = data.get('session_id')
        user_query = data.get('question', '')
        db = SessionLocal()
        try:
            # Truy vấn thông tin giáo viên
            u = db.execute(text("SELECT HoTen, MaLop FROM NguoiDung WHERE MaNguoiDung = :uid"), {"uid": user_id}).fetchone()
            ten_gv = u.HoTen if u else "Quý thầy cô"
            ma_lop = u.MaLop if u else "Chưa xác định"

            # Logic lấy dữ liệu thực tế để RAG (Retrieval Augmented Generation)
            data_context = ""
            keywords = ['thành tích', 'điểm', 'nề nếp', 'vi phạm', 'tình hình', 'tổng hợp', 'báo cáo', 'lớp']
            
            if any(word in user_query.lower() for word in keywords):
                try:
                    top_students = db.execute(text("""
                        SELECT TOP 5 nd.HoTen, bd.DiemSo 
                        FROM BangDiem bd 
                        JOIN NguoiDung nd ON bd.MaHocSinh = nd.MaNguoiDung 
                        WHERE nd.MaLop = :ml ORDER BY bd.DiemSo DESC
                    """), {"ml": ma_lop}).fetchall()
                    
                    vi_pham = db.execute(text("""
                        SELECT nd.HoTen, bn.NoiDung 
                        FROM BangNeNep bn
                        JOIN NguoiDung nd ON bn.MaHocSinh = nd.MaNguoiDung
                        WHERE bn.MaLop = :ml
                    """), {"ml": ma_lop}).fetchall()

                    data_context = f"\n[DỮ LIỆU LỚP {ma_lop}]:\n"
                    data_context += "- Top 5 điểm cao: " + ", ".join([f"{r.HoTen} ({r.DiemSo}đ)" for r in top_students]) + "\n"
                    data_context += "- Vi phạm nề nếp: " + (", ".join([f"{v.HoTen} ({v.NoiDung})" for v in vi_pham]) if vi_pham else "Không có")
                except Exception as db_e:
                    print(f"❌ Lỗi truy vấn SQL: {db_e}")

            sys_msg = (
                f"Bạn là 'Gemini Mentor' - Trợ lý AI của Thầy/Cô {ten_gv}.\n"
                f"Bối cảnh lớp {ma_lop}: {data_context}\n"
                "Nhiệm vụ: Phân tích dữ liệu, soạn bài giảng hoặc tư vấn sư phạm. Trả lời chuyên nghiệp, dùng Markdown."
            )

            response = model_ai.generate_content([sys_msg, f"Câu hỏi giáo viên: {user_query}"])
            
            if response.text:
                emit('ai_response', {"answer": response.text})
                # Lưu vào SQL Server
                db.execute(text("INSERT INTO LichSuChatAI (MaPhien, CauHoi, TraLoiAI, ThoiGianGui) VALUES (:sid, :q, :a, GETDATE())"), 
                           {"sid": session_id, "q": user_query, "a": response.text})
                db.commit()

        except Exception as e:
            print(f"❌ Lỗi Teacher AI: {e}")
            emit('ai_response', {"answer": "Hệ thống AI đang bận cập nhật dữ liệu lớp, Thầy/Cô vui lòng thử lại sau ạ!"})
        finally:
            db.close()

    # --- [B] EVENT: GIA SƯ AI (DÀNH CHO HỌC SINH) ---
    @socketio.on('ask_student_ai')
    def handle_student_ai(data):
        user_id = data.get('userId')
        user_query = data.get('question', '')
        db = SessionLocal()
        try:
            u = db.execute(text("SELECT HoTen FROM NguoiDung WHERE MaNguoiDung = :uid"), {"uid": user_id}).fetchone()
            ten_hs = u.HoTen if u else "Học sinh"

            sys_msg = (
                f"Bạn là 'Gia sư AI' thân thiện của bạn {ten_hs}.\n"
                "Nhiệm vụ: Giải đáp kiến thức, hướng dẫn giải bài tập từng bước. "
                "Sử dụng Markdown và LaTeX cho công thức toán học."
            )

            response = model_ai.generate_content([sys_msg, f"Câu hỏi của {ten_hs}: {user_query}"])
            if response.text:
                emit('ai_response', {"answer": response.text})
            
        except Exception as e:
            print(f"❌ Lỗi Student AI: {e}")
            emit('ai_response', {"answer": "Gia sư đang đọc thêm sách, chờ tí nhé!"})
        finally:
            db.close()

    # --- [C] EVENT: TƯ VẤN TUYỂN SINH (DÀNH CHO KHÁCH) ---
    @socketio.on('ask_guest_ai')
    def handle_guest_ai(data):
        user_query = data.get('question', '')
        sys_msg = (
            "Bạn là 'EduNext Bot' - Tư vấn viên trường học tại Bình Dương. "
            "Thông tin: Học phí 2tr-3.5tr, cơ sở vật chất 5 sao, có hồ bơi, CLB Robotics. "
            "Phong cách: Lễ phép, nhiệt tình, chuyên nghiệp."
        )
        try:
            response = model_ai.generate_content([sys_msg, f"Khách hỏi: {user_query}"])
            answer = response.text if response.text else "Dạ, em chưa rõ ý mình, Anh/Chị có thể nói rõ hơn được không ạ?"
            emit('guest_ai_response', {"answer": answer})
        except Exception as e:
            print(f"❌ Lỗi Guest AI: {e}")
            emit('guest_ai_response', {"answer": "Dạ, em đang bận xử lý hồ sơ tuyển sinh một chút, mình nhắn lại sau nhé!"})