from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False) # Mã ví dụ: LUONGTHEVINH2026
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Liên kết với người dùng
    users = db.relationship('User', backref='school', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # Teacher, Student, Parent, Admin
    
    # Trạng thái tài khoản
    status = db.Column(db.String(20), default='active') # active, pending, rejected
    
    # ID trường (có thể null nếu là giáo viên tự do hoặc chưa thuộc trường nào)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)