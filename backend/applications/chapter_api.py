from flask import request, jsonify, make_response
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from applications.model import db, Subject, Chapter
from applications.extensions import cache
import json

class ChapterAPI(Resource):
    @jwt_required(optional=True)
    def get(self):
        token_identity = get_jwt_identity()
        current_user = None
        if token_identity:
            try:
                current_user = json.loads(token_identity)
            except Exception:
                current_user = None

        is_admin = current_user and current_user.get('role') == 'admin'
        

        subject_id_raw = request.args.get('subject_id', None)
        cache_key = "chapters"
        if subject_id_raw:
            cache_key = f"chapters_{subject_id_raw}"
        

        if not is_admin:
            cached_data = cache.get(cache_key)
            if cached_data:
                return make_response(jsonify(cached_data), 200)
        

        try:
            if subject_id_raw:
                subject_id = int(subject_id_raw)
                chapters = Chapter.query.filter_by(subject_id=subject_id).all()
            else:
                chapters = Chapter.query.all()
        except ValueError:
            return make_response(jsonify({"message": "Invalid subject_id parameter"}), 400)
        
        chapter_json = [
            {
                "id": chapter.id,
                "name": chapter.name,
                "description": chapter.description,
                "n_questions": chapter.n_questions,
                "n_quizzes": chapter.n_quizzes,
                "subject_id": chapter.subject_id
            }
            for chapter in chapters
        ]
        

        if not is_admin:
            cache.set(cache_key, chapter_json)
        return make_response(jsonify(chapter_json), 200)
    
    @jwt_required()
    def post(self):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)
        
        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "Invalid or missing JSON data"}), 400)
        
        name = data.get('name', '').strip()
        subject_id = data.get('subject_id')
        description = data.get('description', '').strip()
        
        if not name or not subject_id:
            return make_response(jsonify({"error": "Name & Subject are required fields"}), 400)
        
        if not (3 <= len(name) <= 30):
            return make_response(jsonify({"error": "Chapter Name must be between 3 and 30 characters"}), 400)
        
        if description and not isinstance(description, str):
            return make_response(jsonify({"error": "Description must be a string"}), 400)
        
        if not Subject.query.get(subject_id):
            return make_response(jsonify({"error": "Given subject not found"}), 400)
        
        try:
            chapter = Chapter(name=name, description=description, subject_id=subject_id)
            db.session.add(chapter)
            db.session.commit()
            cache.delete('chapters')
            cache.delete(f'chapters_{subject_id}')
            return make_response(jsonify({
                "message": "Chapter Created Successfully",
                "chapter": {
                    "id": chapter.id,
                    "name": chapter.name,
                    "n_questions": chapter.n_questions,
                    "n_quizzes": chapter.n_quizzes,
                    "description": chapter.description,
                    "subject_id": chapter.subject_id
                }
            }), 201)
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({"error": "Chapter with this name already exists"}), 400)
    
    @jwt_required()
    def put(self, chapter_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)

        chapter = Chapter.query.get_or_404(chapter_id)
        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "Invalid or missing JSON data"}), 400)

        try:
            if 'name' in data:
                name = data['name'].strip()
                if not (3 <= len(name) <= 30):
                    return make_response(jsonify({"error": "Chapter Name must be between 3 and 30 characters"}), 400)
                if Chapter.query.filter(Chapter.id != chapter.id, Chapter.name == name).first():
                    return make_response(jsonify({"error": "Chapter with this name already exists"}), 400)
                chapter.name = name

            if 'subject_id' in data and Subject.query.get(data['subject_id']):
                chapter.subject_id = data['subject_id']

            if 'description' in data:
                chapter.description = data['description'].strip()

            db.session.commit()

            cache_key = f'chapters_{chapter.subject_id}'
            cache.delete('chapters')
            cache.delete(cache_key)
            print(f"Cache deleted: chapters, {cache_key}")  

            return make_response(jsonify({
                "message": "Chapter Updated Successfully",
                "chapter": {
                    "id": chapter.id,
                    "name": chapter.name,
                    "n_questions": chapter.n_questions,
                    "n_quizzes": chapter.n_quizzes,
                    "description": chapter.description,
                    "subject_id": chapter.subject_id
                }
            }), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

    
    @jwt_required()
    def delete(self, chapter_id):
        current_user = json.loads(get_jwt_identity())
        if current_user.get('role') != 'admin':
            return make_response(jsonify({"error": "Access Denied"}), 403)
        
        chapter = Chapter.query.get_or_404(chapter_id)
        subject_id = chapter.subject_id
        db.session.delete(chapter)
        db.session.commit()
        cache.delete('chapters')
        cache.delete(f'chapters_{subject_id}')
        return make_response(jsonify({"message": "Chapter Deleted Successfully"}), 200)