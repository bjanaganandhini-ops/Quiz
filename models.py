from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---------------- USER TABLE ----------------
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), nullable=False)  # host / player

    quizzes = db.relationship(
        "Quiz",
        backref="creator",
        lazy=True,
        cascade="all, delete"
    )

    scores = db.relationship(
        "Score",
        backref="player",   # access using score.player
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<User {self.username}>"

# ---------------- QUIZ TABLE ----------------
# ---------------- QUIZ TABLE ----------------
class Quiz(db.Model):
    __tablename__ = "quiz"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    creator_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    questions = db.relationship(
        "Question",
        backref="quiz",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # ✅ ADD THIS
    scores = db.relationship(
        "Score",
        backref="quiz",
        lazy=True,
        cascade="all, delete"
    )
# ---------------- QUESTION TABLE ----------------
class Question(db.Model):
    __tablename__ = "question"

    id = db.Column(db.Integer, primary_key=True)

    question = db.Column(db.String(500), nullable=False)

    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)

    answer = db.Column(db.String(200), nullable=False)

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz.id", ondelete="CASCADE"),
        nullable=False
    )

    def __repr__(self):
        return f"<Question {self.id}>"


# ---------------- SCORE TABLE ----------------
class Score(db.Model):
    __tablename__ = "score"

    id = db.Column(db.Integer, primary_key=True)

    marks = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz.id", ondelete="CASCADE"),
        nullable=False
    )

    # ❌ DO NOT ADD relationship here again

    def __repr__(self):
        return f"<Score {self.marks}/{self.total}>"