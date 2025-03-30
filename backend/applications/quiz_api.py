from flask import request, jsonify, make_response, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from applications.model import db, Quiz, Chapter, QuizSubmission, Question
import json
from datetime import datetime

class QuizAPI(Resource):
    @jwt_required()
    def get(self, quiz_id=None):
        try:
            if quiz_id:
                quiz = Quiz.query.get(quiz_id)
                if not quiz:
                    return make_response(jsonify({"error": "Quiz not found"}), 404)
                
                return jsonify({
                    "id": quiz.id,
                    "title": quiz.title,
                    "chapter_id": quiz.chapter_id,
                    "num_questions": quiz.num_questions,
                    "date_of_quiz": quiz.date_of_quiz.isoformat(),
                    "last_date": quiz.last_date.isoformat(),
                    "time_duration": quiz.time_duration,
                    "remarks": quiz.remarks,
                    "created_at": quiz.created_at.isoformat() if quiz.created_at else None
                })

            chapter_id = request.args.get('chapter_id')
            if chapter_id:
                try:
                    chapter_id = int(chapter_id)
                except ValueError:
                    return make_response(jsonify({"error": "Invalid chapter_id"}), 400)

            quizzes = Quiz.query.all()
            if chapter_id:
                quizzes = [q for q in quizzes if q.chapter_id == chapter_id]

            quiz_list = [
                {
                    "id": quiz.id,
                    "title": quiz.title,
                    "chapter_id": quiz.chapter_id,
                    "num_questions": quiz.num_questions,
                    "date_of_quiz": quiz.date_of_quiz.isoformat(),
                    "last_date": quiz.last_date.isoformat(),
                    "time_duration": quiz.time_duration,
                    "remarks": quiz.remarks,
                    "created_at": quiz.created_at.isoformat() if quiz.created_at else None
                }
                for quiz in quizzes
            ]
            
            return jsonify(quiz_list)

        except Exception as e:
            print(f"🔥 ERROR in /api/quiz: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 500)

    @jwt_required()
    def post(self):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "Missing request data"}), 400)
        chapter_id = data.get('chapter_id')
        date_of_quiz = data.get('date_of_quiz')
        last_date = data.get('last_date')
        time_duration = data.get('time_duration', '').strip()
        remarks = data.get('remarks', '').strip()
        title = data.get('title', '').strip() 


        if not chapter_id or not time_duration or not title:
            return make_response(jsonify({"error": "Chapter ID, Title, and Time Duration are required"}), 400)

        try:
            date_of_quiz = datetime.strptime(date_of_quiz, "%Y-%m-%d") if date_of_quiz else datetime.now()
            last_date = datetime.strptime(last_date, "%Y-%m-%d") if last_date else datetime.now()
        except ValueError:
            return make_response(jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400)

        if not self.validate_time_format(time_duration):
            return make_response(jsonify({"error": "Time duration must be in 'hh:mm' format"}), 400)
        quiz = Quiz(
            title=title,
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            last_date=last_date,
            time_duration=time_duration,
            remarks=remarks
        )

        db.session.add(quiz)

        chapter = Chapter.query.get(chapter_id)
        if chapter:
            chapter.n_quizzes += 1

        db.session.commit()
        return make_response(jsonify({
            "message": "Quiz Created Successfully",
            "created_at": quiz.created_at.isoformat() if quiz.created_at else None
        }), 201)

    @jwt_required()
    def put(self, quiz_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return make_response(jsonify({"error": "Quiz not found"}), 404)

        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "Missing request data"}), 400)
        if 'title' in data:
            title = data.get('title', '').strip()
            if not title:
                return make_response(jsonify({"error": "Title cannot be empty"}), 400)
            quiz.title = title

        quiz.chapter_id = data.get('chapter_id', quiz.chapter_id)

        if 'date_of_quiz' in data:
            try:
                quiz.date_of_quiz = datetime.strptime(data['date_of_quiz'], "%Y-%m-%d")
            except ValueError:
                return make_response(jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400)
            
        if 'last_date' in data:
            try:
                quiz.last_date = datetime.strptime(data['last_date'], "%Y-%m-%d")
            except ValueError:
                return make_response(jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400)

        if 'time_duration' in data:
            time_duration = data['time_duration'].strip()
            if not self.validate_time_format(time_duration):
                return make_response(jsonify({"error": "Time duration must be in 'hh:mm' format"}), 400)
            quiz.time_duration = time_duration

        quiz.remarks = data.get('remarks', quiz.remarks)

        db.session.commit()
        return make_response(jsonify({"message": "Quiz Updated Successfully"}), 200)

    @jwt_required()
    def delete(self, quiz_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return make_response(jsonify({"error": "Quiz not found"}), 404)

        db.session.delete(quiz)
        chapter = Chapter.query.get(quiz.chapter_id)
        if chapter and chapter.n_quizzes > 0:
            chapter.n_quizzes -= 1
            chapter.n_questions = 0
        db.session.commit()
        return make_response(jsonify({"message": "Quiz Deleted Successfully"}), 200)

    @staticmethod
    def validate_time_format(time_str):
        try:
            hours, minutes = map(int, time_str.split(':'))
            return 0 <= hours < 24 and 0 <= minutes < 60
        except ValueError:
            return False


class SubmitQuizAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            try:
                current_user = json.loads(get_jwt_identity() or "{}")
            except json.JSONDecodeError:
                return make_response(jsonify({"error": "Invalid JWT token"}), 401)

            quiz_id = request.args.get('quiz_id')
            if quiz_id in [None, "", "null", "undefined"]:
                return make_response(jsonify({"error": "quiz_id is required"}), 400)

            try:
                quiz_id = int(quiz_id)
            except ValueError:
                return make_response(jsonify({"error": "Invalid quiz_id parameter"}), 400)

            query = QuizSubmission.query.filter_by(quiz_id=quiz_id)
            if current_user.get('role') != 'admin':
                query = query.filter_by(user_id=current_user.get('id'))

            submissions = query.all()

            if not submissions:
                submission_data = []  
            else:
                submission_data = [
                    {
                        "id": sub.id,
                        "quiz_id": sub.quiz_id,
                        "user_id": sub.user_id,
                        "score": sub.score,
                        "total_questions": sub.total_questions,
                        "submitted_at": sub.submitted_at.isoformat(),
                        "answers": sub.answers
                    }
                    for sub in submissions
                ]

            return make_response(jsonify(submission_data), 200)

        except Exception as e:
            import traceback
            error_message = str(e)
            traceback_details = traceback.format_exc()
            print("Error fetching quiz submissions:", error_message)
            print(traceback_details)
            return make_response(jsonify({"error": error_message}), 500)

    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            current_user = get_jwt_identity()
            if isinstance(current_user, str):
                try:
                    current_user = json.loads(current_user)  
                except json.JSONDecodeError:
                    return {'error': 'Invalid identity format'}, 401

            if not isinstance(current_user, dict) or 'id' not in current_user:
                return {'error': 'Invalid user identity in token'}, 401
            user_id = current_user['id']

            quiz = Quiz.query.get(data['quizId'])
            if not quiz:
                return {'error': 'Quiz not found'}, 404

            questions = {q.id: q for q in quiz.questions}

            score = 0
            valid_submissions = []
            for answer in data.get('answers', []):
                question = questions.get(answer.get('question_id'))
                if not question:
                    continue
                is_correct = answer.get('selected_option') == (question.correct_option - 1)
                if is_correct:
                    score += 1
                
                valid_submissions.append({
                    'question_id': question.id,
                    'selected_option': answer.get('selected_option'),
                    'is_correct': is_correct
                })

            submission = QuizSubmission(
                user_id=user_id,
                quiz_id=quiz.id,
                score=score,
                total_questions=len(questions),
                answers=valid_submissions,
                submitted_at=datetime.now()
            )
            db.session.add(submission)
            db.session.commit()

            return {
                'message': 'Quiz submitted successfully',
                'score': score,
                'total': len(questions)
            }, 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error: {str(e)}')
            return {'error': 'Submission failed'}, 500

class QuizQuestionsAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            quiz_id = request.args.get('quiz_id')
            if not quiz_id or quiz_id in ["", "null", "undefined"]:
                return make_response(jsonify({"error": "quiz_id is required"}), 400)
            try:
                quiz_id = int(quiz_id)
            except ValueError:
                return make_response(jsonify({"error": "Invalid quiz_id parameter"}), 400)
            questions = Question.query.filter_by(quiz_id=quiz_id).all()
            if not questions:
                return make_response(jsonify([]), 200)
            
            question_data = [
                {
                    "id": question.id,
                    "q_no": question.q_no,
                    "title": question.title,
                    "question_statement": question.question_statement,
                    "options": [
                        question.option1,
                        question.option2,
                        question.option3,
                        question.option4
                    ],
                    "correct_option": question.correct_option + 1
                }
                for question in questions
            ]
            return make_response(jsonify(question_data), 200)
        except Exception as e:
            import traceback
            error_message = str(e)
            print("Error fetching quiz questions:", error_message)
            print(traceback.format_exc())
            return make_response(jsonify({"error": error_message}), 500)
