from flask import jsonify, make_response, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from datetime import datetime
from applications.model import db, User, Quiz, QuizSubmission


class MyReportsAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            try:
                current_user = json.loads(get_jwt_identity() or "{}")
            except json.JSONDecodeError:
                return make_response(jsonify({"error": "Invalid JWT token"}), 401)
            
            user_id = current_user.get("id")
            if not user_id:
                return make_response(jsonify({"error": "Invalid user"}), 401)
            

            submissions = QuizSubmission.query.filter_by(user_id=user_id).all()
            reports = []
            for sub in submissions:
                quiz = Quiz.query.get(sub.quiz_id)
                chapter = quiz.chapter if quiz and hasattr(quiz, "chapter") else None
                subject = chapter.subject if chapter and hasattr(chapter, "subject") else None
                reports.append({
                    "submission_id": sub.id,
                    "quiz_id": sub.quiz_id,
                    "quiz_title": quiz.title if quiz else "Unknown",
                    "subject_name": subject.name if subject else "Unknown",
                    "chapter_name": chapter.name if chapter else "Unknown",
                    "submitted_at": sub.submitted_at.isoformat(),
                    "score": sub.score,
                    "total_questions": sub.total_questions
                })
            return make_response(jsonify(reports), 200)
        except Exception as e:
            current_app.logger.error(str(e))
            return make_response(jsonify({"error": "Failed to fetch reports"}), 500)


class AdminStatsAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            try:
                current_user = json.loads(get_jwt_identity() or "{}")
            except json.JSONDecodeError:
                return make_response(jsonify({"error": "Invalid JWT token"}), 401)
            if current_user.get("role") != "admin":
                return make_response(jsonify({"error": "Unauthorized"}), 403)
            
            total_users = User.query.count()
            total_quizzes = Quiz.query.count()
            total_submissions = QuizSubmission.query.count()
            submissions = QuizSubmission.query.all()
            if submissions:
                average_score = sum(sub.score for sub in submissions) / len(submissions)
            else:
                average_score = 0
            stats = {
                "totalUsers": total_users,
                "totalQuizzes": total_quizzes,
                "totalSubmissions": total_submissions,
                "averageScore": round(average_score, 2)
            }
            return make_response(jsonify(stats), 200)
        except Exception as e:
            current_app.logger.error(str(e))
            return make_response(jsonify({"error": "Failed to fetch admin stats"}), 500)


class SubmissionCountsAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            try:
                current_user = json.loads(get_jwt_identity() or "{}")
            except json.JSONDecodeError:
                return make_response(jsonify({"error": "Invalid JWT token"}), 401)
            if current_user.get("role") != "admin":
                return make_response(jsonify({"error": "Unauthorized"}), 403)
            from sqlalchemy import func
            results = db.session.query(
                Quiz.title,
                func.count(QuizSubmission.id).label("count")
            ).join(QuizSubmission, Quiz.id == QuizSubmission.quiz_id
            ).group_by(Quiz.id).all()
            counts = [{"quiz_title": title, "count": count} for title, count in results]
            return make_response(jsonify(counts), 200)
        except Exception as e:
            current_app.logger.error(str(e))
            return make_response(jsonify({"error": "Failed to fetch submission counts"}), 500)

class QuizCompletionAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            try:
                current_user = json.loads(get_jwt_identity() or "{}")
            except json.JSONDecodeError:
                return make_response(jsonify({"error": "Invalid JWT token"}), 401)
            if current_user.get("role") != "admin":
                return make_response(jsonify({"error": "Unauthorized"}), 403)
            
            now = datetime.now()
            total_quizzes = Quiz.query.filter(Quiz.date_of_quiz <= now).count()
            quizzes_with_submission = (
                db.session.query(QuizSubmission.quiz_id)
                .join(Quiz, QuizSubmission.quiz_id == Quiz.id)
                .filter(Quiz.date_of_quiz <= now)
                .distinct()
                .count()
            )
            quizzes_without_submission = total_quizzes - quizzes_with_submission

            data = {
                "labels": ["Completed", "Not Completed"],
                "datasets": [{
                    "data": [quizzes_with_submission, quizzes_without_submission],
                    "backgroundColor": ["#2ecc71", "#e74c3c"]
                }]
            }
            return make_response(jsonify(data), 200)
        except Exception as e:
            current_app.logger.error(str(e))
            return make_response(jsonify({"error": "Failed to fetch quiz completion data"}), 500)


class AdminUserDetailsAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            try:
                current_user = json.loads(get_jwt_identity() or "{}")
            except json.JSONDecodeError:
                return make_response(jsonify({"error": "Invalid JWT token"}), 401)
            if current_user.get("role") != "admin":
                return make_response(jsonify({"error": "Unauthorized"}), 403)

            submissions = QuizSubmission.query.all()
            details = []
            for sub in submissions:
                quiz = Quiz.query.get(sub.quiz_id)
                if quiz:
                    chapter = quiz.chapter
                    subject = chapter.subject if chapter else None
                    details.append({
                        "user_id": sub.user_id,
                        "quiz_id": sub.quiz_id,
                        "quiz_title": quiz.title,
                        "subject_name": subject.name if subject else "Unknown",
                        "chapter_name": chapter.name if chapter else "Unknown",
                        "score": sub.score,
                        "total_questions": sub.total_questions,
                        "submitted_at": sub.submitted_at.isoformat()
                    })
            grouped = {}
            for d in details:
                uid = d["user_id"]
                if uid not in grouped:
                    user = User.query.get(uid)
                    if not user:
                        continue
                    grouped[uid] = {
                        "user_name": user.full_name,
                        "email": user.email,
                        "details": []
                    }
                grouped[uid]["details"].append(d)
            user_details = []
            for uid, data in grouped.items():
                user_name = data["user_name"]
                email = data["email"]
                user_rows = []
                overall_total = 0
                overall_count = 0
                subject_groups = {}
                for detail in data["details"]:
                    subj = detail["subject_name"]
                    if subj not in subject_groups:
                        subject_groups[subj] = []
                    subject_groups[subj].append(detail)
                    overall_total += detail["score"]
                    overall_count += 1
                overall_avg = round(overall_total / overall_count, 2) if overall_count else 0
                for detail in data["details"]:
                    subj = detail["subject_name"]
                    group = subject_groups[subj]
                    subj_total = sum(item["score"] for item in group)
                    subj_avg = round(subj_total / len(group), 2) if group else 0
                    row = {
                        "id": uid,
                        "user_name": user_name,
                        "email": email,
                        "quiz_title": detail["quiz_title"],
                        "subject_name": subj,
                        "score": detail["score"],
                        "avg_score_subject": subj_avg,
                        "avg_score_all": overall_avg,
                        "submitted_at": detail["submitted_at"]
                    }
                    user_rows.append(row)
                user_details.extend(user_rows)
            return make_response(jsonify(user_details), 200)
        except Exception as e:
            current_app.logger.error(str(e))
            return make_response(jsonify({"error": "Failed to fetch admin user details"}), 500)

class AdminQuizDataAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            try:
                current_user = json.loads(get_jwt_identity() or "{}")
            except json.JSONDecodeError:
                return make_response(jsonify({"error": "Invalid JWT token"}), 401)
            if current_user.get("role") != "admin":
                return make_response(jsonify({"error": "Unauthorized"}), 403)

            submissions = QuizSubmission.query.all()
            reports = []
            for sub in submissions:
                quiz = Quiz.query.get(sub.quiz_id)
                if quiz:
                    chapter = quiz.chapter
                    subject = chapter.subject if chapter else None
                    reports.append({
                        "submission_id": sub.id,
                        "quiz_id": sub.quiz_id,
                        "user_id": sub.user_id,
                        "quiz_title": quiz.title,
                        "subject_name": subject.name if subject else "Unknown",
                        "chapter_name": chapter.name if chapter else "Unknown",
                        "score": sub.score,
                        "total_questions": sub.total_questions,
                        "submitted_at": sub.submitted_at.isoformat()
                    })
            return make_response(jsonify(reports), 200)
        except Exception as e:
            current_app.logger.error(str(e))
            return make_response(jsonify({"error": "Failed to fetch admin quiz data"}), 500)

