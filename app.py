from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, QuizQuestion, Progress, Result, Lesson, Score
from flask_migrate import Migrate
from flask_migrate import upgrade
import random
from flask import abort
from datetime import datetime 
from werkzeug.utils import secure_filename
import os
import csv
import json
from models import Comment
import pandas as pd
from flask import send_file 
import io 
# TẠO FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = 'khoa-bi-mat-cua-lop-12c6' # Để bảo mật session
if os.environ.get("DATABASE_URL"):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# TẠO FLASK APP-
# KẾT NỐI DATABASE
db.init_app(app)
migrate = Migrate(app, db)
# Cấu hình đăng nhập
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#KẾT NỐI DATABASE VỚI FLASK (app.py)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
# --- PHẦN 2: CÁC ROUTES (ĐƯỜNG DẪN) ---
# 1. Tạo Database (Chạy lần đầu)
@app.route('/initdb')
def initdb():
    with app.app_context():
        db.create_all()
        # Tạo sẵn 1 tài khoản giáo viên demo
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
            db.session.add(admin)
            db.session.commit()
    return "Đã tạo Database thành công!"

# 2. Đăng nhập / Đăng ký
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        action = request.form.get('action') # Kiểm tra xem đang bấm nút Đăng nhập hay Đăng ký
       
        if action == 'register':
            # Logic Đăng ký
            if User.query.filter_by(username=username).first():
                flash('Tài khoản đã tồn tại!')
            else:
                new_user = User(
                    username=username, 
                    password=generate_password_hash(password),
                    role="student"
                )
                db.session.add(new_user)
                db.session.commit()
                flash('Đăng ký thành công! Hãy đăng nhập.')
        
        else:
            # Logic Đăng nhập
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Sai tên hoặc mật khẩu!')
                
    return render_template('login.html')
# Đặng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
#reset mật khẩu 
@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Đổi mật khẩu thành công. Hãy đăng nhập lại.")
            return redirect(url_for('login'))
        else:
            flash("Không tìm thấy tài khoản")

    return render_template('forgot_password.html')


# 3. Dashboard (Trang chủ sau khi đăng nhập) -> Xem điểm, Nội dung học
# -------------------------
# ROUTE ĐẦU TIÊN
# -------------------------
@app.route('/')
def index():
    return redirect(url_for("login"))
#    return "Flask LMS đã chạy thành công"

@app.route('/dashboard')
@login_required
def dashboard():
    lessons=Lesson.query.all()
    if current_user.role == 'admin':
        results_all = Result.query.all()
        users = User.query.filter_by(role='student').all()
        #lessons = Lesson.query.all()
        
        report = []
        scores_all=[]
        for user in users:
            results = Result.query.filter_by(user_id=user.id).all()
            #result_dict = {r.lesson_id: r.score for r in results}
            progress_list = Progress.query.filter_by(
    user_id=current_user.id
).all()
            
            result_dict = {}

            for r in results:
                if r.lesson_id not in result_dict:
                    result_dict[r.lesson_id] = r.score
                else:
                    result_dict[r.lesson_id] = max(result_dict[r.lesson_id], r.score)
            total = sum(result_dict.values()) if result_dict else 0
            scores_all.append(total)
            #tiến trình
            completed=Progress.query.filter_by(
                user_id=user.id,
                completed=True
            ).count()
            percent=int((completed/len(lessons))*100) if lessons else 0

            report.append({
            "username": user.username,
            "scores": result_dict,
            "total": total,
            "progress":percent
        })
        #thống kê
        total_students=len(users)
        avg_score=int(sum(scores_all)/total_students) if total_students else 0

        #top 5 học sinh
        top_students=sorted(report, key=lambda x:x["total"], reverse=True)[:5]  
        weak_students = [r for r in report if r['total'] < 5]
        good_students = [r for r in report if r['total'] >= 8]
        return render_template(
        'dashboard.html',
        role='admin',
        lessons=lessons,
        report=report,
        total_students=total_students,
        avg_score=avg_score,
        top_students=top_students,
        weak_students=weak_students,
        good_students=good_students,
        results_all=results_all         
    )
    else:
        #lessons = Lesson.query.all()
        results = Result.query.filter_by(
        user_id=current_user.id).all()

        result_dict = {}
        total_score=0
        for r in results:
            if r.lesson_id not in result_dict:
                result_dict[r.lesson_id] = r.score
            else:
                result_dict[r.lesson_id] = max(result_dict[r.lesson_id], r.score)


        total_score = sum(result_dict.values()) if result_dict else 0
        #tiến trình
        completed = Progress.query.filter_by(
            user_id=current_user.id,
            completed=True
        ).count()
        percent=int((completed/len(lessons))*100) if lessons else 0

        progress_list = []

        for lesson in lessons:
            prog = Progress.query.filter_by(
                 user_id=current_user.id,
                lesson_id=lesson.id,
                completed=True
    ).first()

            progress_list.append({
        "lesson": lesson,
        "done": True if prog else False
    })
        return render_template(
        'dashboard.html',
        role='student',
        lessons=lessons,
        result_dict=result_dict,
        total_score=total_score,
        percent=percent,
        progress_list=progress_list 
    )
#TẠo câu hỏi 
@app.route('/quiz/lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def quiz_by_lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)
    if request.method == 'GET':
        questions = QuizQuestion.query.filter_by(lesson_id=lesson_id).all()
        questions = random.sample(questions, min(10, len(questions)))

    if not questions:
        return "Bài này chưa có câu hỏi"

    if request.method == 'POST':

        score = 0
        user_answers = {}

        for q in questions:
            user_ans = request.form.get(str(q.id))
            user_answers[q.id] = user_ans

            if user_ans == q.correct_answer:
                score += 1

       
        # đếm số lần làm 
        attempt_count = Result.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).count()

        attempt = attempt_count + 1

        # lưu kết quả
        result = Result(
        user_id=current_user.id,
        lesson_id=lesson_id,
        score=score,
        attempt=attempt,
        created_at=datetime.now(),
        answers=json.dumps(user_answers)
        )

        db.session.add(result)
        db.session.commit()
         # Lưu tiến trình
        progress = Progress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson_id
        ).first()

        if not progress:
            progress = Progress(
                user_id=current_user.id,
                lesson_id=lesson_id,
                completed=True
            )
            db.session.add(progress)
        else:
            progress.completed = True
        db.session.commit()

        return render_template(
            'quiz_result.html',
            lesson=lesson,
            questions=questions,
            user_answers=user_answers,
            score=score,
            attempt=attempt
        )

    return render_template(
        'quiz.html',
        lesson=lesson,
        questions=questions
    )

#Route hiển thị lịch sử làm bài họ
@app.route('/lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson_detail(lesson_id):

    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        abort(404)  # tránh lỗi nếu lesson không tồn tại

    next_lesson = Lesson.query.filter(Lesson.id > lesson.id).order_by(Lesson.id).first()
    questions = QuizQuestion.query.filter_by(lesson_id=lesson_id).all()

    all_lessons=Lesson.query.all()
    # Lấy lịch sử làm bài
    results= Result.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).order_by(Result.attempt.desc()).all()
    comments = Comment.query.filter_by(
    user_id=current_user.id,
    lesson_id=lesson_id
).order_by(Comment.created_at.desc()).all()
    
    score = None
    user_answers = {}

    if request.method == 'POST':
        score = 0
        #user_answers = {}

        for q in questions:
            selected = request.form.get(str(q.id))
            user_answers[q.id] = selected
            if selected == q.correct_answer:
                score += 1

        attempt_count = Result.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson_id
        ).count()

        attempt = attempt_count + 1

        new_result = Result(
            score=score,
            attempt=attempt,
            created_at=datetime.now(),
            user_id=current_user.id,
            lesson_id=lesson_id,
            answers=json.dumps(user_answers)
        )
        db.session.add(new_result)
        # ===== LƯU TIẾN TRÌNH =====
        progress = Progress.query.filter_by(
                user_id=current_user.id,
                lesson_id=lesson_id
).first()

        if not progress:
            progress = Progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
                completed=True
    )
            db.session.add(progress)
        else:
            progress.completed = True

        db.session.commit()
        # cập nhật lại attempts sau khi thêm
        results = Result.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson_id
        ).order_by(Result.attempt.desc()).all()

    return render_template(
        'lesson_detail.html',
        lesson=lesson,
        questions=questions,
        score=score,
        user_answers=user_answers,
              results=results,
              next_lesson=next_lesson, 
              all_lessons=all_lessons,
              comments=comments 
    )



#Form upload bài (route)
@app.route('/teacher/add_lesson', methods=['GET','POST'])
@login_required
def add_lesson():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        title = request.form['title']
        subject_id = request.form['subject_id']
        content_type = request.form['content_type']
        content_url = request.form['content_url']

        lesson = Lesson(
            title=title,
            subject_id=subject_id,
            content_type=content_type,
            content_url=content_url
        )
        db.session.add(lesson)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_lesson.html')

@app.route('/subject/<int:id>')
def subject_lesson(id):
    subject_lesson = Lesson.query.filter_by(subject_id=id).all()
    return render_template('lessons.html', subject_lesson=subject_lesson)

#@app.before_first_request
def create_admin():
    admin = User.query.filter_by(role='admin').first()

    if not admin:
        admin_user = User(
            username='admin',
            password=generate_password_hash('123456'),
            role='admin'
        )

        db.session.add(admin_user)
        db.session.commit()
        print("✅ Đã tạo tài khoản admin mặc định")
# ==============================
# UPLOAD CÂU HỎI TỪ FILE CSV
# ==============================
@app.route('/upload_questions', methods=['GET', 'POST'])
@login_required
def upload_questions():

    if request.method == 'POST':
        title = request.form.get('title')
        word_link = request.form.get('word_link')
        pdf_link = request.form.get('pdf_link')
        csv_file = request.files.get('csv_file')

        if not title:
            flash("❌ Chưa nhập tên bài")
            return render_template('upload_questions.html')

        if not word_link:
            flash("❌ Chưa nhập link Word")
            return render_template('upload_questions.html')

        if not pdf_link:
            flash("❌ Chưa nhập link PDF")
            return render_template('upload_questions.html')

        if not csv_file or csv_file.filename == '':
            flash("❌ Chưa chọn file CSV")
            return render_template('upload_questions.html')
        lesson = Lesson(
            title=title,
            content_type="word",
            content_doc=word_link,
            content_pdf=pdf_link
        )
        db.session.add(lesson)
        db.session.commit()

        # ===== CSV =====
        try:
            stream = csv_file.stream.read().decode("utf-8").splitlines()
            reader = csv.DictReader(stream)

            for row in reader:
                q = QuizQuestion(
                    lesson_id=lesson.id,
                    question=row.get('question') or "",
                    option_a=row.get('option_a') or "",
                    option_b=row.get('option_b') or "",
                    option_c=row.get('option_c') or "",
                    option_d=row.get('option_d') or "",
                    correct_answer=row.get('correct_answer') or "A"
                )
                db.session.add(q)

            db.session.commit()

        except Exception as e:
            flash(f"Lỗi CSV: {e}")
            #print("LỖI CHI TIẾT:", e)
            #flash(f"Lỗi: {e}")
            return render_template('upload_questions.html')

        flash("✅ Upload thành công!")
        return redirect(url_for('dashboard'))

    # ===== GET =====
    return render_template('upload_questions.html')


#TẠO NHẬN XÉT- GV
@app.route('/admin/comment/<int:user_id>/<int:lesson_id>', methods=['POST'])
@login_required
def add_comment(user_id, lesson_id):
    if current_user.role != 'admin':
        abort(403)
    content = request.form.get('content')
    if content:
        comment = Comment(
            user_id=user_id,
            lesson_id=lesson_id,
            content=content,
            created_at=datetime.now(),
            teacher_name=current_user.username
        )
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for('lesson_detail', lesson_id=lesson_id))

# GV XEM BÀI LÀM HS
@app.route('/admin/view_result/<int:result_id>')
@login_required
def view_result(result_id):

    if current_user.role != 'admin':
        abort(403)

    result = Result.query.get_or_404(result_id)
    questions = QuizQuestion.query.filter_by(lesson_id=result.lesson_id).all()

    import json
    user_answers={}
    if result.answers:
        user_answers = json.loads(result.answers)

    return render_template(
        'view_result.html',
        result=result,
        questions=questions,
        user_answers=user_answers
    )


# xuất file excel
@app.route('/export_excel')
@login_required
def export_excel():

    # ===== CHỈ ADMIN =====
    if current_user.role != 'admin':
        abort(403)

    # ===== LẤY DỮ LIỆU =====
    users = User.query.filter_by(role='student').all()
    lessons = Lesson.query.all()

    data = []

    # ===== DUYỆT TỪNG HỌC SINH =====
    for user in users:

        row = {
            "Tên học sinh": user.username
        }

        tong_diem = 0

        # ===== DUYỆT TỪNG BÀI =====
        for lesson in lessons:

            # lấy điểm theo tên bài
            scores = Score.query.filter_by(
                user_id=user.id,
                subject=lesson.title
            ).all()

            # ===== NẾU ĐÃ LÀM BÀI =====
            if scores:

                # điểm cao nhất
                diem_cao_nhat = max(s.score for s in scores)

                # số lần làm
                so_lan_lam = len(scores)

            else:

                diem_cao_nhat = 0
                so_lan_lam = 0

            # thêm vào excel
            row[f"{lesson.title}"] = diem_cao_nhat
            row[f"{lesson.title} - Lần làm"] = so_lan_lam

            tong_diem += diem_cao_nhat

        # ===== TỔNG ĐIỂM =====
        row["Tổng điểm"] = tong_diem

        data.append(row)

    # ===== TẠO DATAFRAME =====
    df = pd.DataFrame(data)

    # ===== XUẤT EXCEL =====
    output = io.BytesIO()

    df.to_excel(
        output,
        index=False,
        engine='openpyxl'
    )

    output.seek(0)

    # ===== GỬI FILE =====
    return send_file(
        output,
        download_name="bao_cao_hoc_sinh.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

#Tạo route hiển thị danh sách bài học
@app.route('/admin/lessons')
@login_required
def admin_lessons():
    lessons = Lesson.query.all()
    return render_template('admin_lessons.html', lessons=lessons)
#Thêm route xóa
@app.route('/admin/delete_lesson/<int:id>')
@login_required
def delete_lesson(id):
    lesson = Lesson.query.get_or_404(id)

    # Xóa dữ liệu liên quan
    QuizQuestion.query.filter_by(lesson_id=id).delete()
    Result.query.filter_by(lesson_id=id).delete()
    Progress.query.filter_by(lesson_id=id).delete()

    db.session.delete(lesson)
    db.session.commit()

    return redirect('/admin/lessons')

#Tạo route sửa (nếu chưa có)
@app.route('/admin/fix_link/<int:lesson_id>', methods=['GET', 'POST'])
def fix_link(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    if request.method == 'POST':
        lesson.content_doc = request.form.get('word_link')
        lesson.content_pdf = request.form.get('pdf_link')
        db.session.commit()
        return "Đã cập nhật!"

    return f"""
    <form method="POST">
        Word: <input name="word_link" value="{lesson.content_doc or ''}"><br>
        PDF: <input name="pdf_link" value="{lesson.content_pdf or ''}"><br>
        <button>Lưu</button>
    </form>
    """

@app.route('/admin/auto_fix_links')
@login_required
def auto_fix_links():
    if current_user.role != 'admin':
        return "❌ Không có quyền"
    # 👉 map ID bài → link đúng
    mapping = {
        11: {
            "doc": "https://docs.google.com/document/d/16JzX6aLeGkTRvl5-2SexUOY6XNRf8d3o/export?format=docx",
            "pdf": "https://drive.google.com/file/d/1WW7CuLYlqB0G1ACCByzVbUX2GA_idIL9/preview"
        },
        12: {
            "doc": "https://docs.google.com/document/d/1m25EdvcqMBURHnH-MdTLgFkzXc_NLR1r/export?format=docx",
            "pdf": "https://drive.google.com/file/d/164_icTuacIwQMllzCvSBmtU1adf9aUIJ/preview"
        },
        13: {
            "doc": "https://docs.google.com/document/d/1_dBW_a5do5UO745ZfUiGm4IyOofKlSpW/export?format=docx",
            "pdf": "https://drive.google.com/file/d/1gXI_CUXbToJ03T4UYjjw9Q9C7gPPmwCh/preview"
        },
        14: {
            "doc": "https://docs.google.com/document/d/12oflzpK3RSpxiAn0ufhTWEW_uRzrNuF2/export?format=docx",
            "pdf": "https://drive.google.com/file/d/15fQ4XOJqW6y7FrYp2MkTu3XxUaeEov92/preview"
        },
        15: {
            "doc": "https://docs.google.com/document/d/1vJrUnoCMuI-n05h53sp7UNeeZ59Vnskc/export?format=docx",
            "pdf": "https://drive.google.com/file/d/1ovMdwJUDN3vcJsBaASaqnW2Jq_VAFsmX/preview"
        },
        16: {
            "doc": "https://docs.google.com/document/d/12RXwEYcMAfVTWdCvtQF0aTtdIr5BYQvp/export?format=docx",
            "pdf": "https://drive.google.com/file/d/1Ad39ru42_d-aCDhunZWrOUn7FIsNB2Ty/preview"
        },
        17: {
            "doc": "https://docs.google.com/document/d/1bkYHNhvMkYNmzs06_pzGYmR8-xY_XrN_/export?format=docx",
            "pdf": "https://drive.google.com/file/d/1AekKiVgl2cDVhWtHjqRaYgQmwfLS8Dz5/preview"
        },
        18: {
            "doc": "https://docs.google.com/document/d/1t-ymCLQkWgmskNH20ft29qF98gVNvI5j/export?format=docx",
            "pdf": "https://drive.google.com/file/d/1ZZZe9g692lwuTdhWTOgSm7f6r4gd9zjY/preview"
        }

    }

    for lesson_id, links in mapping.items():

        lesson = Lesson.query.get(lesson_id)

        print("ID:", lesson_id)
        print("LESSON:", lesson)

        if lesson:
            lesson.content_doc = links["doc"]
            lesson.content_pdf = links["pdf"]
            db.session.add(lesson)
            
            print("ĐÃ UPDATE:", lesson.id)

    db.session.commit()

    return "✅ Đã cập nhật đúng từng bài!"
# -------------------------https
# CHẠY APP
# -------------------------

with app.app_context():
    try:
        # ✅ cập nhật database
        upgrade()
        print("✅ Database upgraded")
    except Exception as e:
        print("❌ Lỗi migrate:", e)

    # ✅ tạo bảng nếu chưa có
    db.create_all()

    # ✅ tạo admin
    create_admin()
if __name__ == '__main__':
    import os
    #app.run(host="0.0.0.0",port=5000,debug=True)
    port = int(os.environ.get("PORT", 5000))
    print(app.url_map)
    app.run(host="0.0.0.0", port=port,debug =True)