# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, session, current_app
# Import hàm call_gemini_api từ file service của bạn
from app.services.ai_service import call_gemini_api 

student_bp = Blueprint('student', __name__)

@student_bp.route('/api/chat-ai/ask', methods=['POST'])
def ask_ai():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        # Lấy tên từ session hoặc mặc định là 'Học sinh'
        student_name = session.get('user_name', 'Học sinh')
        
        if not user_message:
            return jsonify({'success': False, 'message': 'Bạn chưa nhập câu hỏi!'}), 400

        # System Instruction chi tiết để định hướng vai trò "Gia sư"
        sys_instruction = (
            f"Bạn là 'Gia sư AI EduNext', đang hỗ trợ bạn học sinh tên {student_name}.\n"
            "QUY TẮC PHẢN HỒI:\n"
            "1. Tuyệt đối không cho đáp án trực tiếp ngay lập tức, hãy gợi ý và hướng dẫn từng bước.\n"
            "2. Sử dụng LaTeX ($...$) cho công thức toán học và Markdown để trình bày đẹp.\n"
            "3. Ngôn ngữ: Tiếng Việt, xưng hô thân thiện (tớ - cậu hoặc mình - bạn).\n"
            "4. Khuyến khích học sinh suy nghĩ bằng các câu hỏi gợi mở."
        )

        full_prompt = f"{sys_instruction}\n\nHọc sinh hỏi: {user_message}"
        
        # Gọi hàm xử lý từ ai_service.py
        bot_reply = call_gemini_api(full_prompt)

        return jsonify({
            'success': True, 
            'reply': bot_reply
        })
    except Exception as e:
        current_app.logger.error(f"AI Route Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Gia sư đang bận suy nghĩ...'}), 500