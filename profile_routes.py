from flask import Blueprint , jsonify
from flask_jwt_extended import jwt_required,get_jwt_identity

from models.user import User
from models.stats import UserStats
from services.gamification_service import(get_all_badges,get_effective_daily_xp,get_effective_streak)

profile_bp = Blueprint("profile",__name__)

@profile_bp.route("/api/profile",methods=["GET"])
@jwt_required()

def get_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "error" : "user not found"
        }),404

    stats = UserStats.query.filter_by(user_id=user_id).first()

    if not stats:
        return jsonify({
            "error" : "Stats not found"
        }),404

    daily_xp = get_effective_daily_xp(stats)

    return jsonify({
        "user" : {
            "id" : user.id,
            "username" : user.username,
            "email" : user.email
        },
        "stats" : {
            "score" : stats.total_score,
            "xp" : stats.total_xp,
            "level" : stats.level,
            "streak" : get_effective_streak(stats),
            "code_runs" : stats.total_code_runs,
            "error_solved" : stats.errors_solved,
            "coding_seconds" : stats.total_coding_seconds
        },
        "badges" : get_all_badges(stats)

    }),200