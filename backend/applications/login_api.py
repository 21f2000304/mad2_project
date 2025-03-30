from flask import request, jsonify, make_response
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from datetime import datetime
import json
import re
from applications.model import db, User, Admin
from applications.extensions import cache
from flask_bcrypt import check_password_hash
from sqlalchemy.exc import IntegrityError

class LoginAPI(Resource):
    @jwt_required()
    def get(self, user_id=None):
        current_user = json.loads(get_jwt_identity())  

        if user_id is None:  
            if current_user["role"] != "admin":
                return make_response(jsonify({"error": "Access Denied"}), 403)

            users = User.query.all()
            return jsonify([
                {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "qualification": user.qualification or None,  
                    "dob": str(user.dob) if user.dob else None,  
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None,  
                    "reminder_time": user.reminder_time.strftime("%H:%M") if user.reminder_time else None,  
                    "status": user.status 
                }
                for user in users
            ])

        user = Admin.query.get(current_user["id"]) if current_user["role"] == "admin" else User.query.get(current_user["id"])

        if not user:
            return make_response(jsonify({"error": "User not found"}), 404)


        response_data = {
            "id": user.id,
            "email": user.email,
            "role": "admin" if isinstance(user, Admin) else "user",
        }

        if isinstance(user, User):  
            response_data.update({
                "full_name": user.full_name,
                "qualification": user.qualification,
                "dob": str(user.dob) if user.dob else None,
                "reminder_time": user.reminder_time.strftime("%H:%M") if user.reminder_time else None,
            })
        else:  
            response_data["name"] = user.name

        return jsonify(response_data)


    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        admin = Admin.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.status != 'active':
                return make_response(jsonify({"error": "Your account is inactive. Contact the administrator!"}), 403)

            user.last_seen = datetime.now()
            db.session.commit()

            access_token = create_access_token(identity=json.dumps({"id": user.id, "role": "user"}))
            return make_response(jsonify({
                "message": "User login successful",
                "role": "user",
                "username": user.full_name,
                "token": access_token
            }), 200)

        if admin and check_password_hash(admin.password, password):
            access_token = create_access_token(identity=json.dumps({"id": admin.id, "role": "admin"}))
            return make_response(jsonify({
                "message": "Admin login successful",
                "role": "admin",
                "username": admin.name,
                "token": access_token
            }), 200)

        return make_response(jsonify({"error": "Invalid credentials"}), 401)

    @jwt_required()
    def patch(self, user_id):
        current_user = json.loads(get_jwt_identity())

        if current_user["role"] != "admin":
            return make_response(jsonify({"error": "Access Denied"}), 403)

        user = User.query.get_or_404(user_id)
        data = request.get_json()

        new_status = data.get('status', '').strip().lower()

        valid_statuses = ['active', 'pending', 'disabled']
        
        if new_status not in valid_statuses:
            return make_response(jsonify({"error": "Invalid status. Must be 'active', 'pending', or 'disabled'."}), 400)

        if user.status == new_status:
            return make_response(jsonify({"message": f"User is already {new_status}"}), 200)

        user.status = new_status
        db.session.commit()

        return make_response(jsonify({"message": f"User status updated to {new_status} successfully"}), 200)

    

    @jwt_required()
    def put(self, user_id):
        current_user = json.loads(get_jwt_identity())

        user = Admin.query.get(user_id) if current_user["role"] == "admin" and Admin.query.get(user_id) else User.query.get(user_id)

        if not user:
            return make_response(jsonify({"error": "User not found"}), 404)

        data = request.get_json()
        role = "admin" if isinstance(user, Admin) else "user"

        mandatory_fields = {
            "admin": ["name", "email"],
            "user": ["full_name", "email"]
        }
        
        allowed_fields = {
            "admin": ["name", "email"],
            "user": ["full_name", "qualification", "dob", "reminder_time", "email"]
        }

        updated_fields = {}

        for field in mandatory_fields[role]:
            if field not in data or not data[field].strip():
                return make_response(jsonify({"error": f"{field.replace('_', ' ').capitalize()} is required"}), 400)

        for field in allowed_fields[role]:
            if field in data:

                if field == "email":
                    existing_user = User.query.filter_by(email=data[field]).first() or Admin.query.filter_by(email=data[field]).first()
                    if existing_user and existing_user.id != user_id:
                        return make_response(jsonify({"error": "Email already registered"}), 400)

                    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_regex, data[field]):
                        return make_response(jsonify({"error": "Invalid email format"}), 400)

                    setattr(user, field, data[field])

                elif field == "dob":
                    if data[field]:  
                        try:
                            setattr(user, field, datetime.strptime(data[field], "%Y-%m-%d").date())
                        except ValueError:
                            return make_response(jsonify({"error": "Invalid date format, expected YYYY-MM-DD"}), 400)

                elif field == "reminder_time":
                    if data[field]:  
                        try:
                            setattr(user, field, datetime.strptime(data[field], "%H:%M").time())  
                        except ValueError:
                            return make_response(jsonify({"error": "Invalid time format, expected HH:MM"}), 400)

                elif field in ["full_name", "name"]:
                    if len(data[field].strip()) < 2:
                        return make_response(jsonify({"error": f"{field.replace('_', ' ').capitalize()} must be at least 2 characters long"}), 400)
                    setattr(user, field, data[field])

                updated_fields[field] = data[field]

        if "password" in data and data["password"].strip():
            if len(data["password"]) < 6 or len(data["password"]) > 128:
                return make_response(jsonify({"error": "Password must be between 6 and 128 characters"}), 400)
            user.set_password(data["password"]) 
            updated_fields["password"] = "Updated"

        if not updated_fields:
            return make_response(jsonify({"message": "No valid fields provided for update"}), 400)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({"error": "Email already registered"}), 400)  

        return make_response(jsonify({
            "message": "User details updated successfully",
            "updated_fields": updated_fields
        }), 200)


class SignupAPI(Resource):
    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        qualification = data.get('qualification')
        dob = data.get('dob')
        reminder_time = data.get('reminder_time')

        if not email or not password or not full_name:
            return make_response(jsonify({"error": "Email, password, and full name are required fields"}), 400)

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return make_response(jsonify({"error": "Invalid email format"}), 400)

        if len(password) < 6 or len(password) > 128:
            return make_response(jsonify({"error": "Password must be between 6 and 128 characters"}), 400)

        if User.query.filter_by(email=email).first():
            return make_response(jsonify({"error": "Email already registered"}), 400)

        new_user = User(
            email=email,
            full_name=full_name,
            qualification=qualification,
            dob=datetime.strptime(dob, "%Y-%m-%d").date() if dob else None,
            reminder_time=datetime.strptime(reminder_time, "%H:%M").time() if reminder_time else None  
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return make_response(jsonify({"message": "User registered successfully!"}), 201)
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({"error": "Email already registered"}), 400)



class BulkUpdateAPI(Resource):
    @jwt_required()
    def patch(self):
        current_user = json.loads(get_jwt_identity())

        if current_user["role"] != "admin":
            return make_response(jsonify({"error": "Access Denied"}), 403)

        data = request.get_json()
        user_ids = data.get('user_ids', [])
        new_status = data.get('status', '').strip().lower()

        valid_statuses = ['active', 'pending', 'disabled']
        if new_status not in valid_statuses:
            return make_response(jsonify({"error": "Invalid status. Must be 'active', 'pending', or 'disabled'."}), 400)

        if not user_ids:
            return make_response(jsonify({"error": "No user IDs provided"}), 400)

        updated_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user and user.status != new_status:
                user.status = new_status
                updated_count += 1

        db.session.commit()

        return make_response(jsonify({
            "message": f"Updated {updated_count} users to {new_status} successfully."
        }), 200)
