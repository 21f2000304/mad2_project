from datetime import datetime, timedelta, timezone
import calendar
import logging
import os
from jinja2 import Environment, FileSystemLoader
from flask_mail import Message
from celery.schedules import crontab
from applications.worker import celery
from applications.model import db, User, Quiz, QuizSubmission

logging.basicConfig(level=logging.INFO)

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
reminder_template = env.get_template('daily_reminder.html')
report_template = env.get_template('monthly_report.html')

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from main import app
    with app.app_context():
        active_users = User.query.filter(User.status == "active").all()
        for user in active_users:
            reminder_time = user.reminder_time
            sender.add_periodic_task(
                crontab(hour=reminder_time.hour, minute=reminder_time.minute),
                send_daily_reminder.s(user.id),
                name=f"daily_reminder_user_{user.id}"
            )
        sender.add_periodic_task(
            crontab(day_of_month=1, hour=8, minute=00),
            send_monthly_report.s(),
            name="monthly_user_activity_report"
        )


@celery.task(bind=True, max_retries=3)
def send_daily_reminder(self, user_id):
    from main import app  
    with app.app_context():
        user = User.query.get(user_id)
        if not user or user.status != "active":
            logging.error(f"User with ID {user_id} not found or not active.")
            return
        
        now = datetime.now(timezone.utc)
        last_24_hours = now - timedelta(days=1)
        new_quiz_available = Quiz.query.filter(Quiz.created_at >= last_24_hours).first()
        last_seen = user.last_seen.replace(tzinfo=timezone.utc) if user.last_seen else None

        if (last_seen and (now - last_seen).days >= 1) or new_quiz_available:
            try:
                send_email_reminder.apply_async(args=[user.id])
            except Exception as e:
                logging.error(f"Failed to send reminder to {user.email}: {e}")
                raise self.retry(exc=e, countdown=60)


@celery.task(bind=True, max_retries=3)
def send_email_reminder(self, user_id):
    from main import app, mail  
    with app.app_context():
        user = User.query.get(user_id)
        if not user or user.status != "active":
            logging.error(f"User with ID {user_id} not found or not active.")
            return

        subject = "Reminder: Attempt Your Quiz!"
        quiz_link = "http://localhost:5173"
        email_body = reminder_template.render(
            user_name=user.full_name,
            quiz_link=quiz_link
        )

        msg = Message(
            subject,
            recipients=[user.email]
        )
        msg.html = email_body

        try:
            mail.send(msg)
            logging.info(f"Reminder email sent to {user.email}")
        except Exception as e:
            logging.error(f"Failed to send email to {user.email}: {e}")
            raise self.retry(exc=e, countdown=60)


@celery.task(bind=True, max_retries=3)
def send_monthly_report(self):
    from main import app, mail  
    with app.app_context():
        now = datetime.now(timezone.utc)
        first_day = now.replace(day=1)
        last_day = first_day.replace(day=calendar.monthrange(first_day.year, first_day.month)[1])
        active_users = User.query.filter(User.status == "active").all()

        for user in active_users:
            submissions = QuizSubmission.query.filter(
                QuizSubmission.user_id == user.id,
                QuizSubmission.submitted_at.between(first_day, last_day)
            ).all()
            total_quizzes = len(submissions)
            total_score = sum(sub.score for sub in submissions)
            average_score = total_score / total_quizzes if total_quizzes > 0 else 0

            report_body = report_template.render(
                user_name=user.full_name,
                total_quizzes=total_quizzes,
                average_score=average_score,
                quiz_link="http://localhost:5173"
            )

            msg = Message(
                subject="Your Monthly Quiz Report",
                recipients=[user.email]
            )
            msg.html = report_body

            try:
                mail.send(msg)
                logging.info(f"Monthly report sent to {user.email}")
            except Exception as e:
                logging.error(f"Failed to send report to {user.email}: {e}")
                raise self.retry(exc=e, countdown=60)

