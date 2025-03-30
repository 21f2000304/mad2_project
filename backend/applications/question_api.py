from flask import request, jsonify, make_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from applications.model import db, Question, Quiz, Chapter
from applications.extensions import cache

class QuestionAPI(Resource):
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

            cache_key = f"questions_{quiz_id}" if quiz_id else "questions_all"

            if current_user.get('role') != 'admin':
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    return make_response(jsonify(cached_data), 200)

            questions = Question.query.filter_by(quiz_id=quiz_id).all()

            if not questions:
                return make_response(jsonify([]), 200)

            question_data = [
                {
                    "id": question.id,
                    "quiz_id": question.quiz_id,
                    "q_no": question.q_no,
                    "title": question.title,
                    "question_statement": question.question_statement,
                    "options": [
                        question.option1,
                        question.option2,
                        question.option3,
                        question.option4
                    ],
                    "correct_option": question.correct_option
                } for question in questions
            ]

            if current_user.get('role') != 'admin':
                cache.set(cache_key, question_data, timeout=120)

            return make_response(jsonify(question_data), 200)

        except Exception as e:
            import traceback
            error_message = str(e)
            traceback_details = traceback.format_exc()
            print("Error fetching questions:", error_message)
            print(traceback_details)
            return make_response(jsonify({"error": error_message}), 500)


    @jwt_required()
    def post(self):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        data = request.get_json()

        quiz_id = data.get('quiz_id')
        q_no= data.get('q_no')
        title = data.get('title', '').strip()
        question_statement = data.get('question_statement', '').strip()
        options = [
            data.get('option1', '').strip(), 
            data.get('option2', '').strip(), 
            data.get('option3', '').strip(), 
            data.get('option4', '').strip()
        ]
        correct_option = data.get('correct_option')

        if not quiz_id or not title or not question_statement:
            return make_response(jsonify({"error": "Quiz ID, Title and Question statement are required"}), 400)
        if not all(options):
            return make_response(jsonify({"error": "All 4 options must be provided and non-empty"}), 400)
        if correct_option not in [1, 2, 3, 4]:
            return make_response(jsonify({"error": "Correct option must be 1, 2, 3, or 4"}), 400)

        question = Question(
            quiz_id=quiz_id,
            title=title,
            q_no=q_no,
            question_statement=question_statement,
            option1=options[0],
            option2=options[1],
            option3=options[2],
            option4=options[3],
            correct_option=correct_option
        )

        db.session.add(question)

        quiz = Quiz.query.get(quiz_id)
        if quiz:
            quiz.num_questions += 1  

        chapter = Chapter.query.get(quiz.chapter_id)
        if chapter:
            chapter.n_questions += 1
        
        db.session.commit()
        return make_response(jsonify({"message": "Question Created Successfully"}), 201)

    
    @jwt_required()
    def put(self, question_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        question = Question.query.get(question_id)
        if not question:
            return make_response(jsonify({"error": "Question not found"}), 404)

        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "Invalid or missing JSON data"}), 400)

        q_no = data.get('q_no')
        title = data.get('title', '').strip() 
        question_statement = data.get('question_statement', '').strip()
        options = [
            data.get('option1', '').strip(),
            data.get('option2', '').strip(),
            data.get('option3', '').strip(),
            data.get('option4', '').strip()
        ]
        correct_option = data.get('correct_option')

        if not title or not question_statement:
            return make_response(jsonify({"error": "Title and Question statement are required"}), 400)
        if not all(options):
            return make_response(jsonify({"error": "All 4 options must be provided and non-empty"}), 400)
        if correct_option not in [1, 2, 3, 4]:
            return make_response(jsonify({"error": "Correct option must be 1, 2, 3, or 4"}), 400)

        question.title = title
        question.q_no = q_no
        question.question_statement = question_statement
        question.option1 = options[0]
        question.option2 = options[1]
        question.option3 = options[2]
        question.option4 = options[3]
        question.correct_option = correct_option

        db.session.commit()
        return make_response(jsonify({"message": "Question Updated Successfully"}), 200)

    @jwt_required()
    def delete(self, question_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        question = Question.query.get(question_id)
        if not question:
            return make_response(jsonify({"error": "Question not found"}), 404)

        db.session.delete(question)
        
        quiz = Quiz.query.get(question.quiz_id)
        if quiz and quiz.num_questions > 0:
            quiz.num_questions -= 1
        chapter = Chapter.query.get(quiz.chapter_id)
        if chapter and chapter.n_questions > 0:
            chapter.n_questions -= 1

        db.session.commit()
        return make_response(jsonify({"message": "Question Deleted Successfully"}), 200)
