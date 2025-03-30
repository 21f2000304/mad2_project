from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, time
from flask_bcrypt import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  
    full_name = db.Column(db.String(50), nullable=False)
    qualification = db.Column(db.String(50))
    dob = db.Column(db.Date)
    status = db.Column(db.String(10), default="pending", nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.now, nullable=False)
    reminder_time = db.Column(db.Time, default=time(19, 0), nullable=False)


    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  


    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    chapters = db.relationship('Chapter', backref='subject', cascade="all, delete-orphan", lazy=True)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    n_questions = db.Column(db.Integer, default=0, nullable=False)
    n_quizzes = db.Column(db.Integer, default=0, nullable=False) 
    quizzes = db.relationship('Quiz', backref='chapter', cascade="all, delete-orphan", lazy=True)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(50), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.Date, default=datetime.now, nullable=False)
    last_date = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.String(10), default='01:00', nullable=False)
    remarks = db.Column(db.Text)
    num_questions = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    questions = db.relationship('Question', backref='quiz', cascade="all, delete-orphan", lazy=True)
    def __init__(self, time_duration='01:00', **kwargs):
        if not self.validate_time_format(time_duration):
            raise ValueError("Time duration must be in 'hh:mm' format")
        self.time_duration = time_duration
        super().__init__(**kwargs)

    def update(self, **kwargs):
        """Update the quiz attributes with validation."""
        time_duration = kwargs.get('time_duration', self.time_duration)
        if not self.validate_time_format(time_duration):
            raise ValueError("Time duration must be in 'hh:mm' format")
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def validate_time_format(time_str):
        """Validate that the time duration is in 'hh:mm' format."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return 0 <= hours < 24 and 0 <= minutes < 60
        except ValueError:
            return False

    def __repr__(self):
        return f"<Quiz {self.id}>"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    q_no = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(50), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(50), nullable=False)
    option2 = db.Column(db.String(50), nullable=False)
    option3 = db.Column(db.String(50))
    option4 = db.Column(db.String(50))
    correct_option = db.Column(db.Integer, nullable=False)


class QuizSubmission(db.Model):
    __tablename__ = 'quiz_submissions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False)
    answers = db.Column(db.JSON, nullable=False)
    def __repr__(self):
        return f'<QuizSubmission {self.id}>'