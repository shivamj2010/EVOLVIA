from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

from extensions import db
from models.stats import UserStats
from services.gamification_service import (process_code_run , process_error_solved)
from utils import get_json_body


code_bp = Blueprint('code', __name__)


# ==================================================
# JUDGE0
# ==================================================

JUDGE0_URL = "https://ce.judge0.com"


# ==================================================
# LANGUAGE IDS
# ==================================================

LANGUAGE_IDS = {
    "c": 50,
    "cpp": 54,
    "c++": 54,
    "java": 62,
    "javascript": 63,
    "js": 63,
    "php": 68,
    "python": 71,
    "ruby": 72,
    "go": 60,
    "rust": 73,
    "typescript": 74
}

# Bahut bada code bhej ke koi server ko slow na kar sake
MAX_CODE_LENGTH = 20000


# ==================================================
# RUN CODE
# ==================================================

@code_bp.route('/api/code/run', methods=['POST'])
@jwt_required()
def run_code():

    # Get logged-in user
    user_id = int(get_jwt_identity())

    # --------------------------------------------------
    # Get JSON body
    # --------------------------------------------------

    data = get_json_body()

    if data is None:
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    # --------------------------------------------------
    # Get language and code
    # --------------------------------------------------

    language = data.get("language")
    code = data.get("code")

    if (
        not isinstance(language, str)
        or not isinstance(code, str)
        or not language.strip()
        or not code.strip()
    ):
        return jsonify({
            "error": "Language and code are required"
        }), 400

    if len(code) > MAX_CODE_LENGTH:
        return jsonify({
            "error": f"Code too long (max {MAX_CODE_LENGTH} characters)"
        }), 413

    # --------------------------------------------------
    # Normalize language
    # --------------------------------------------------

    language = language.lower().strip()

    if language not in LANGUAGE_IDS:
        return jsonify({
            "error": "Language not supported",
            "supported_languages": list(LANGUAGE_IDS.keys())
        }), 400

    # --------------------------------------------------
    # Get user stats
    # --------------------------------------------------

    stats = UserStats.query.filter_by(
        user_id=user_id
    ).first()

    # Create stats if not found
    if not stats:

        stats = UserStats(
            user_id=user_id
        )

        db.session.add(stats)
        db.session.flush()

    # --------------------------------------------------
    # Send code to Judge0
    # --------------------------------------------------

    try:

        response = requests.post(
            f"{JUDGE0_URL}/submissions",

            params={
                "base64_encoded": "false",
                "wait": "true"
            },

            # json= use karne se Content-Type khud set ho jata hai
            json={
                "source_code": code,
                "language_id": LANGUAGE_IDS[language],
                "cpu_time_limit": 2,
                "memory_limit": 128000
            },

            timeout=15
        )

        # --------------------------------------------------
        # Judge0 error
        # --------------------------------------------------

        if response.status_code not in [200, 201]:

            db.session.rollback()

            # Detail sirf server log mai, client ko nahi
            current_app.logger.error(
                "Judge0 submission failed: %s %s",
                response.status_code,
                response.text
            )

            return jsonify({
                "error": "Judge0 submission failed",
                "status_code": response.status_code
            }), 502

        # --------------------------------------------------
        # Get Judge0 result
        # --------------------------------------------------

        result = response.json()

        status = result.get("status", {})

        # Judge0 status ID 3 = Accepted
        accepted = (
            isinstance(status, dict)
            and status.get("id") == 3
        )

        # --------------------------------------------------
        # Gamification
        # --------------------------------------------------

        gamification = process_code_run(
            stats,
            accepted=accepted
        )

        # --------------------------------------------------
        # Save stats
        # --------------------------------------------------

        db.session.commit()

        # --------------------------------------------------
        # Response
        # --------------------------------------------------

        return jsonify({

            "success": True,
            "user_id": user_id,
            "language": language,
            "status": result.get("status"),
            "accepted": accepted,
            "output": result.get("stdout"),
            "error": result.get("stderr"),
            "compile_output": result.get("compile_output"),
            "time": result.get("time"),
            "memory": result.get("memory"),
            "gamification": gamification

        }), 200

    # ==================================================
    # TIMEOUT
    # ==================================================

    except requests.Timeout:

        db.session.rollback()

        return jsonify({
            "error": "Judge0 request timed out"
        }), 504

    # ==================================================
    # REQUEST ERROR
    # ==================================================

    except requests.RequestException:

        db.session.rollback()

        current_app.logger.exception("Judge0 request failed")

        return jsonify({
            "error": "Judge0 service unavailable"
        }), 502

    # ==================================================
    # OTHER SERVER ERROR
    # ==================================================

    except Exception:

        db.session.rollback()

        current_app.logger.exception("run_code failed")

        return jsonify({
            "error": "Server error"
        }), 500

# ==============================================================
# ERROR SLOVED
#===============================================================

@code_bp.route('/api/code/error-sloved',methods = ['POST'])
@jwt_required()

def error_sloved():
    user_id = get_jwt_identity()

    stats = UserStats.query.filter_by(user_id=user_id).first()

    if not stats:
        return jsonify({
            "error" : "Stats not found"
        }),404

    gamification = process_error_solved(stats)

    db.session.commit()

    return jsonify({
        "success" : True,
        "user_id" : user_id,
        "gamification" : gamification
    }),200

#=======================================================
# Add coding time
#=======================================================

@code_bp.route('/api/code/time',methods = ['POST'])
@jwt_required()

def add_coding_time():
    user_id = get_jwt_identity()

    data = request.get_json(silent=True)

    if not isinstance(data,dict):
        return jsonify({
            "error" : "Request body must be JSON object"
        }),400

    seconds = data.get("seconds")

    if not isinstance(seconds,int):
        return jsonify({
            "error" : "seconds must be greater than 0"
        }),400

    

    if seconds <= 0:
        return jsonify({
            "error" : "seconds must be greater than 0"
        }),400

    #Security 1 request mai max 10 min

    if seconds > 600:
        return jsonify({
            "error" : "Maximum 600 seconds allowed per request"
        }),400

    stats = UserStats.query.filter_by(user_id=user_id).first()

    if not stats:
        return jsonify({
            "error" "Stats not found"
        }),404

    stats.total_coding_seconds += seconds

    db.session.commit()

    return jsonify({
        "success" : True,
        "user_id" : user_id,
        "coding_seconds" : stats.total_coding_seconds,
        "added_seconds" : seconds
    }),200
    