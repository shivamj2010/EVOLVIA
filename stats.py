from extensions import db


class UserStats(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        unique=True,
        nullable=False
    )

    # Score
    total_score = db.Column(
        db.Integer,
        default=0
    )

    # XP
    total_xp = db.Column(
        db.Integer,
        default=0
    )

    daily_xp = db.Column(
        db.Integer,
        default=0
    )

    # NEW: daily_xp kis din ka hai (daily reset iske basis pe hoga)
    last_xp_date = db.Column(
        db.Date,
        nullable=True
    )

    level = db.Column(
        db.Integer,
        default=1
    )

    # Coding
    total_code_runs = db.Column(
        db.Integer,
        default=0
    )

    errors_solved = db.Column(
        db.Integer,
        default=0
    )

    total_coding_seconds = db.Column(
        db.Integer,
        default=0
    )

    # Streak
    current_streak = db.Column(
        db.Integer,
        default=0
    )

    last_coded_date = db.Column(
        db.Date,
        nullable=True
    )