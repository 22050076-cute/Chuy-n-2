# -*- coding: utf-8 -*-
import google.generativeai as genai
from flask_socketio import emit
from flask import request, copy_current_request_context
from app.config import Config
import threading

# Cấu hình AI
try:
    if Config.GENAI_API_KEY:
        genai.configure(api_key=Config.GENAI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash') 
        print(f"✅ [AI READY] Model: gemini-2.0-flash")
    else:
        model = None
except Exception as e:
    model = None

def call_gemini_api(prompt):
    if not model: return "AI chưa được cấu hình key."
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.7)
        )
        return response.text if response.text else "Mình chưa nghĩ ra câu trả lời..."
    except Exception as e:
        return f"Lỗi: {str(e)}"

def register_ai_events(socketio):
    # Tên này PHẢI khớp 100% với socket.emit ở HTML
    @socketio.on('ask_clb_connect') 
    def handle_clb_chat(data):
        # Thêm dòng print này để kiểm tra xem Backend đã nhận được tin chưa
        print(f"🤖 Đã nhận tin nhắn từ giao diện: {data.get('question')}")
        
        question = data.get('question', '').strip()
        user_sid = request.sid 

        @copy_current_request_context
        def ai_task(q, sid):
            # Gọi hàm Gemini (nhớ đảm bảo hàm call_gemini_api của bạn đang chạy tốt)
            ans = call_gemini_api(f"Bạn là trợ lý AI của EduNext. Trả lời: {q}")
            
            # Gửi ngược lại cho client. Tên 'ai_response' PHẢI khớp với socket.on ở HTML
            socketio.emit('ai_response', {"answer": ans}, to=sid)
            print(f"✅ Đã gửi phản hồi về cho khách: {sid}")

        import threading
        threading.Thread(target=ai_task, args=(question, user_sid)).start()
        
    # Thêm sự kiện tạo session mới nếu bạn muốn xử lý ở Backend
    @socketio.on('create_ai_session')
    def create_session(data):
        # Logic tạo MaPhien trong DB
        # new_id = db.create_new_session(data['userId'], data['title'])
        # emit('session_created', {'MaPhien': new_id})
        pass