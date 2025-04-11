from flask import Flask, jsonify, request
from flask_restful import Api
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from datetime import timedelta
import os
from flask_cors import CORS

from applications.model import db, User, Admin
from applications.extensions import cache
from applications.worker import celery


from applications.login_api import LoginAPI, SignupAPI, BulkUpdateAPI
from applications.subject_api import SubjectAPI
from applications.chapter_api import ChapterAPI
from applications.quiz_api import QuizAPI,SubmitQuizAPI
from applications.question_api import QuestionAPI
from applications.report_api import MyReportsAPI, AdminStatsAPI,SubmissionCountsAPI,QuizCompletionAPI,AdminUserDetailsAPI,AdminQuizDataAPI

current_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "quiz_master.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Security & JWT Config
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "afsal_quiz_secret_key")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "afsal_quiz_token_key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=10)

# Redis Cache Configuration
REDIS_IP = "172.25.203.197"

app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_REDIS_HOST'] = REDIS_IP
app.config['CACHE_REDIS_URL'] = f"redis://{REDIS_IP}:6379/0"
app.config['CELERY_BROKER_URL'] = f"redis://{REDIS_IP}:6379/0"
app.config['CELERY_RESULT_BACKEND'] = f"redis://{REDIS_IP}:6379/1"
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# Mail Configuration (Use Environment Variables for Security)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_DEFAULT_SENDER'] = "quizapp.mad2@gmail.com"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "quizapp.mad2@gmail.com")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", "afxs vpki ypet jsyx")

# Celery Configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/1'
celery.conf.update(
    broker_url=app.config['CELERY_BROKER_URL'],
    result_backend=app.config['CELERY_RESULT_BACKEND'],
    timezone='Asia/Kolkata',
    enable_utc=False,
    broker_connection_retry_on_startup=True
)


db.init_app(app)
cache.init_app(app) 


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
jwt = JWTManager(app)
mail = Mail(app)
api = Api(app)

CORS(app, resources={r"/*": {
    "origins": ["http://localhost:5173"],
    "methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Authorization", "Content-Type"],
    "supports_credentials": True
}})

# Ensure application context is pushed
with app.app_context():
    db.create_all()

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Admin.query.get(int(user_id))

@app.before_request
def handle_preflight():
    """Handle CORS preflight requests globally."""
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS Preflight OK"}), 204

# Initialize Admin User (if not exists)
def add_admin():
    with app.app_context():
        admin = Admin.query.first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash("admin")
            admin = Admin(name="admin", password=hashed_password, email="quizapp.mad2@gmail.com")
            db.session.add(admin)
            db.session.commit()
            print("Administrator Initialized")

# Register Periodic Celery Tasks
from applications.task import setup_periodic_tasks
celery.on_after_configure.connect(setup_periodic_tasks)

# API Routes
api.add_resource(LoginAPI, '/api/login', '/api/users', '/api/users/<int:user_id>')
api.add_resource(SignupAPI, '/api/signup')
api.add_resource(SubjectAPI, '/api/subject', '/api/subject/<int:subject_id>')
api.add_resource(ChapterAPI, '/api/chapter', '/api/chapter/<int:chapter_id>')
api.add_resource(QuizAPI, '/api/quiz', '/api/quiz/<int:quiz_id>')
api.add_resource(QuestionAPI, '/api/question', '/api/question/<int:question_id>', '/api/quiz-questions')
api.add_resource(BulkUpdateAPI, '/api/users/bulk-update')
api.add_resource(SubmitQuizAPI, '/api/submit-quiz')

api.add_resource(MyReportsAPI, "/api/my-reports")
api.add_resource(AdminStatsAPI, "/api/admin-stats")
api.add_resource(SubmissionCountsAPI, "/api/submission-counts")
api.add_resource(QuizCompletionAPI, "/api/quiz-completion")
api.add_resource(AdminUserDetailsAPI, '/api/admin-user-details')
api.add_resource(AdminQuizDataAPI, '/api/admin-quiz-data')


# Start Application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

