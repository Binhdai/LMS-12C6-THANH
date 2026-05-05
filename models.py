from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()
# -------------------
# USER (HỌC SINH)
# -------------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'   # (tốt, rõ ràng)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20), default='student')
    scores = db.relationship('Score', backref='student', lazy=True)


# Bảng Điểm số (Score)
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    subject = db.Column(db.String(50), nullable=False) # Ví dụ: "Bài 1", "Giữa kỳ"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
  # -------------------
# SUBJECT (CHỦ ĐỀ)
# ------------------  
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
# -------------------
# LESSON (BÀI HỌC)
# -------------------
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    content_type = db.Column(db.String(50))
    ## content_path = db.Column(db.String(500))
    content_url = db.Column(db.String(500))
    content_pdf = db.Column(db.Text)   
    content_doc = db.Column(db.Text)   
# -------------------
# CÂU HỎI TRẮC NGHIỆM
# -------------------
class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer)
    question = db.Column(db.String(500))
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(1))
# -------------------
# TIẾN TRÌNH HỌC
# -------------------
class Progress(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, primary_key=True)
    completed = db.Column(db.Boolean, default=False)
# -------------------
# KẾT QUẢ TRẮC NGHIỆM
# -------------------im
class Result(db.Model):
    _tablename_="result"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    score = db.Column(db.Integer)
    lesson = db.relationship('Lesson')
    attempt = db.Column(db.Integer)   # số lần làm
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # thời gian
    answers = db.Column(db.Text)   

#Thêm bảng Comment
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)      # học sinh
    lesson_id = db.Column(db.Integer)   # bài học

    content = db.Column(db.Text)        # nội dung nhận xét
    created_at = db.Column(db.DateTime)

    teacher_name = db.Column(db.String(50))  # tên giáo viên
    