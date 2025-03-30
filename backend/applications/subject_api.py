from flask import request, jsonify, make_response
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from applications.model import db, Subject
import json
from applications.extensions import cache

class SubjectAPI(Resource):

    @jwt_required()
    def get(self):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') == 'admin':
            subjects = Subject.query.all()
        else:
            cached_data = cache.get('subjects')
            if cached_data:
                return make_response(jsonify(cached_data), 200)
            subjects = Subject.query.all()

        subject_json = [
            {
                "id": subject.id,
                "name": subject.name,
                "description": subject.description,
                "chapters": [
                    {"id": chapter.id, "name": chapter.name, "description": chapter.description, "n_questions": chapter.n_questions,"n_quizzes":chapter.n_quizzes}
                    for chapter in subject.chapters
                ],
            }
            for subject in subjects
        ]

        if current_user.get('role') != 'admin':
            cache.set('subjects', subject_json, timeout=120) 

        return make_response(jsonify(subject_json), 200)
    
    @jwt_required()
    def post(self):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "Invalid or missing JSON data"}), 400)

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return make_response(jsonify({"error": "Name is required"}), 400)
        if not (3 <= len(name) <= 30):
            return make_response(jsonify({"error": "Subject Name must be between 3 and 30 characters"}), 400)

        subject = Subject(name=name, description=description)
        try:
            db.session.add(subject)
            db.session.commit()
            cache.delete('subjects')
            return make_response(jsonify({
                "message": "Subject Created Successfully",
                "subject": {"id": subject.id, "name": subject.name, "description": subject.description}
            }), 201)
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({"error": "Subject with this name already exists"}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": f"An error occurred: {str(e)}"}), 500)

    @jwt_required()
    def put(self, subject_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        subject = Subject.query.get_or_404(subject_id)
        data = request.get_json()

        if not data:
            return make_response(jsonify({"error": "Invalid or missing JSON data"}), 400)

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return make_response(jsonify({"error": "Name is required"}), 400)
        if not (3 <= len(name) <= 30):
            return make_response(jsonify({"error": "Subject Name must be between 3 and 30 characters"}), 400)

        if Subject.query.filter(Subject.id != subject.id, Subject.name == name).first():
            return make_response(jsonify({"error": "Subject with this name already exists"}), 400)

        subject.name = name
        subject.description = description
        db.session.commit()
        cache.delete('subjects')
        return make_response(jsonify({
            "message": "Subject Updated Successfully",
            "subject": {"id": subject.id, "name": subject.name, "description": subject.description}
        }), 200)

    @jwt_required()
    def delete(self, subject_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        subject = Subject.query.get_or_404(subject_id)
        try:
            for chapter in subject.chapters:
                db.session.delete(chapter)
            db.session.delete(subject)
            db.session.commit()
            cache.delete('subjects')
            return make_response(jsonify({"message": "Subject Deleted Successfully"}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": f"An error occurred: {str(e)}"}), 500)