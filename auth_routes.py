from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db, bcrypt
from flask_jwt_extended import create_access_token
from models.user import User
from models.stats import UserStats
from utils import get_json_body


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    data = get_json_body()

    if data is None:
        return jsonify({"error": "Request body must be a JSON object"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if not all(isinstance(v, str) for v in (username, email, password)):
        return jsonify({"error": "Username, email and password must be text"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password_hash=hashed_pw)

    try:
        db.session.add(new_user)
        db.session.flush()

        new_stats = UserStats(user_id=new_user.id)
        db.session.add(new_stats)
        db.session.commit()

    except IntegrityError:
        # Do log ek saath signup kare to check pass ho jata hai, par DB unique rule rok deta hai
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 409

    return jsonify({"message": "User created successfully"}), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = get_json_body()

    if data is None:
        return jsonify({"error": "Request body must be a JSON object"}), 400

    username = data.get('username')
    password = data.get('password')

    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": access_token,
        "user": {"id": user.id, "username": user.username}
    }), 200