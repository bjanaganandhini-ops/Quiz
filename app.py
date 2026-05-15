from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from config import Config
from models import db, User, Quiz, Question, Score

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------
@app.route("/register/<role>", methods=["GET", "POST"])
def register(role):

    # ✅ Allow only valid roles
    if role not in ["player", "host", "admin"]:
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(request.url)

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(request.url)

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(request.url)

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password=hashed_pw,
            role=role
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    # Load correct template
    if role == "player":
        return render_template("register_player.html")
    elif role == "host":
        return render_template("register_host.html")
    elif role == "admin":
        return render_template("admin_register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):

            login_user(user)

            # ✅ Role-based redirect
            if user.role == "admin":
                return redirect(url_for("dashboard_admin"))
            elif user.role == "host":
                return redirect(url_for("dashboard_host"))
            else:
                return redirect(url_for("dashboard_player"))

        flash("Invalid credentials!", "danger")

    return render_template("login.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/dashboard/admin")
@login_required
def dashboard_admin():

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    total_users = User.query.count()
    total_quizzes = Quiz.query.count()
    total_scores = Score.query.count()

    users = User.query.all()
    quizzes = Quiz.query.all()

    return render_template(
        "dashboard_admin.html",
        total_users=total_users,
        total_quizzes=total_quizzes,
        total_scores=total_scores,
        users=users,
        quizzes=quizzes
    )


# ---------------- HOST DASHBOARD ----------------
@app.route("/dashboard/host")
@login_required
def dashboard_host():

    # Role protection
    if current_user.role != "host":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    # Get quizzes created by this host
    quizzes = Quiz.query.filter_by(
        creator_id=current_user.id
    ).order_by(Quiz.created_at.desc()).all()

    return render_template(
        "dashboard_host.html",
        username=current_user.username,
        quizzes=quizzes
    )

#------------------VIEW_QUIZ--------------------

@app.route("/view_quiz/<int:quiz_id>")
@login_required
def view_quiz(quiz_id):
    if current_user.role != "host":
        return redirect(url_for("login"))

    quiz = Quiz.query.get_or_404(quiz_id)

    return render_template(
        "view_quiz.html",
        quiz=quiz
    )

#-----------------QUIZZESS-------------------
@app.route("/quizzes")
@login_required
def player_quizzes():

    if current_user.role != "player":
        return redirect(url_for("dashboard_host"))

    quizzes = Quiz.query.all()

    return render_template("player_quizzes.html", quizzes=quizzes)   


# ---------------- CREATE QUIZ ----------------
@app.route("/create_quiz", methods=["POST"])
@login_required
def create_quiz():

    if current_user.role != "host":
        return redirect(url_for("home"))

    title = request.form.get("title")
    duration = request.form.get("duration")

    quiz = Quiz(
        title=title,
        duration=int(duration),
        creator_id=current_user.id
    )

    db.session.add(quiz)
    db.session.commit()

    flash("Quiz Created Successfully!", "success")

    return redirect(url_for("add_question", quiz_id=quiz.id))

#---------------------EDIT QUESTION-----------------------
@app.route("/question/edit/<int:question_id>", methods=["GET", "POST"])
@login_required
def edit_question(question_id):

    if current_user.role != "host":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    question = Question.query.get_or_404(question_id)

    # Make sure host owns this quiz
    if question.quiz.creator_id != current_user.id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("dashboard_host"))

    if request.method == "POST":
        question.question = request.form["question"]
        question.option1 = request.form["option1"]
        question.option2 = request.form["option2"]
        question.option3 = request.form["option3"]
        question.option4 = request.form["option4"]
        question.answer = request.form["answer"]

        db.session.commit()

        flash("Question updated successfully!", "success")
        return redirect(url_for("add_question", quiz_id=question.quiz_id))

    return render_template("edit_question.html", question=question)

#---------------------------DELETE QUESTION -------------------
@app.route("/question/delete/<int:question_id>", methods=["POST"])
@login_required
def delete_question(question_id):

    # Allow only host
    if current_user.role != "host":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    # Get question
    question = Question.query.get_or_404(question_id)

    # Ensure host owns this quiz
    if question.quiz.creator_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for("dashboard_host"))

    quiz_id = question.quiz_id

    try:
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting question!", "danger")

    return redirect(url_for("add_question", quiz_id=quiz_id))    

#------------------------HOST QUIZZES------------------------
@app.route("/host/quizzes")
@login_required
def host_quizzes():

    if current_user.role != "host":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()

    return render_template(
        "host_quizzes.html",
        quizzes=quizzes,
        username=current_user.username
    )

# ------------------------ADD QUESTION -----------------------
@app.route("/add_question/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def add_question(quiz_id):

    quiz = Quiz.query.get_or_404(quiz_id)

    if current_user.role != "host":
        return redirect(url_for("home"))

    if request.method == "POST":

        if len(quiz.questions) >= quiz.duration:
            flash("Question limit reached!", "danger")
            return redirect(url_for("add_question", quiz_id=quiz_id))

        question_text = request.form.get("question")
        option1 = request.form.get("option1")
        option2 = request.form.get("option2")
        option3 = request.form.get("option3")
        option4 = request.form.get("option4")
        correct_option = request.form.get("correct_option")

        options = {
            "1": option1,
            "2": option2,
            "3": option3,
            "4": option4
        }

        answer = options.get(correct_option)

        question = Question(
            question=question_text,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            answer=answer,
            quiz_id=quiz_id
        )

        db.session.add(question)
        db.session.commit()

        flash("Question Added Successfully!", "success")
        return redirect(url_for("add_question", quiz_id=quiz_id))

    return render_template("add_question.html", quiz=quiz)


# ---------------- PLAYER DASHBOARD ----------------
@app.route("/dashboard/player")
@login_required
def dashboard_player():

    if current_user.role != "player":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    quizzes = Quiz.query.all()

    return render_template(
        "dashboard_player.html",
        quizzes=quizzes,
        username=current_user.username
    )


# ---------------- ATTEMPT QUIZ ----------------
@app.route("/attempt_quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def attempt_quiz(quiz_id):

    quiz = Quiz.query.get_or_404(quiz_id)

    if current_user.role != "player":
        return redirect(url_for("home"))

    if request.method == "POST":

        score = 0

        for question in quiz.questions:
            selected = request.form.get(f"question_{question.id}")
            if selected == question.answer:
                score += 1

        new_score = Score(
            marks=score,
            total=len(quiz.questions),
            user_id=current_user.id,
            quiz_id=quiz.id
        )

        db.session.add(new_score)
        db.session.commit()

        return render_template(
            "score_result.html",
            score=score,
            total=len(quiz.questions),
            quiz=quiz
        )

    return render_template("attempt_quiz.html", quiz=quiz)


# ---------------- VIEW SCORES ----------------
@app.route("/scores")
@login_required
def view_scores():

    scores = Score.query.filter_by(
        user_id=current_user.id
    ).order_by(Score.timestamp.desc()).all()

    return render_template("scores.html", scores=scores)

#-----------------ADEMIN DELETE USER-------------------

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    user = User.query.get_or_404(user_id)

    # Prevent deleting admin itself
    if user.role == "admin":
        flash("Cannot delete admin!", "danger")
        return redirect(url_for("dashboard_admin"))

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully!", "success")
    return redirect(url_for("dashboard_admin"))

#---------------------ADMIN DELETE QUIZ-------------------

@app.route("/admin/delete_quiz/<int:quiz_id>", methods=["POST"])
@login_required
def delete_quiz(quiz_id):

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    quiz = Quiz.query.get_or_404(quiz_id)

    db.session.delete(quiz)
    db.session.commit()

    flash("Quiz deleted successfully!", "success")
    return redirect(url_for("dashboard_admin"))


# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)