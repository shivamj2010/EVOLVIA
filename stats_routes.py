from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.stats import UserStats
from services.gamification_service import (
    DAILY_XP_MAX,
    get_all_badges,
    get_effective_daily_xp,
    get_effective_streak,
    update_level
)


stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():

    user_id = int(get_jwt_identity())

    stats = UserStats.query.filter_by(
        user_id=user_id
    ).first()

    if not stats:
        return jsonify({
            "error": "Stats not found"
        }), 404

    # Make sure level is up to date (aur DB mai save bhi karo)
    update_level(stats)
    db.session.commit()

    badges = get_all_badges(stats)

    daily_xp = get_effective_daily_xp(stats)

    return jsonify({

        # ---------------- SCORE ----------------

        "score": stats.total_score,

        # ---------------- XP ----------------

        "xp": stats.total_xp,

        "daily_xp": daily_xp,

        "daily_xp_max": DAILY_XP_MAX,

        "daily_xp_remaining": max(
            0,
            DAILY_XP_MAX - daily_xp
        ),

        # ---------------- LEVEL ----------------

        "level": stats.level,

        # ---------------- CODING ----------------

        "code_runs": stats.total_code_runs,

        "errors_solved": stats.errors_solved,

        # Seconds
        "coding_seconds": stats.total_coding_seconds,

        # ---------------- STREAK ----------------

        "streak": get_effective_streak(stats),

        # ---------------- BADGES ----------------

        "badges": badges

    }), 200