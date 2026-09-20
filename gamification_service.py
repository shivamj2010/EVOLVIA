from datetime import date, timedelta


# ---------------- XP REWARDS ----------------

XP_REWARDS = {
    "code_run": 2,
    "accepted": 5,
    "error_solved": 1,
    "time_challenge": 10,
    "daily_bonus": 20
}

DAILY_XP_MAX = 100


# ---------------- LEVEL THRESHOLDS ----------------

LEVEL_THRESHOLDS = [
    (10000, 10),
    (7500, 9),
    (5000, 8),
    (3500, 7),
    (2000, 6),
    (1000, 5),
    (500, 4),
    (250, 3),
    (100, 2),
    (0, 1)
]


# ---------------- XP BADGES ----------------

XP_BADGES = [
    (10000, "Coding Legend"),
    (7500, "Master Coder"),
    (5000, "Expert Coder"),
    (3500, "Advanced Coder"),
    (2000, "Skilled Coder"),
    (1000, "Rising Coder"),
    (500, "Coder"),
    (100, "Beginner")
]


# ---------------- RARE BADGES ----------------

RARE_BADGES = {
    "error_handler": {
        "name": "Error Handler",
        "requirement": "Solve 50 coding errors"
    },
    "time_master": {
        "name": "Time Master",
        "requirement": "Code for 10 hours"
    },
    "streak_master": {
        "name": "Streak Master",
        "requirement": "Maintain 100 days streak"
    }
}


# ==================================================
# DAILY XP RESET
# ==================================================

def reset_daily_xp_if_needed(stats):
    """
    FIX: pehle last_coded_date se compare hota tha, jo run ke beech mai
    update nahi hoti thi, to daily_xp baar-baar 0 ho jata tha.
    Ab alag column last_xp_date use hota hai.
    """

    today = date.today()

    if stats.last_xp_date != today:
        stats.daily_xp = 0
        stats.last_xp_date = today


# ==================================================
# ADD XP
# ==================================================

def add_xp(stats, amount):

    if amount <= 0:
        return 0

    reset_daily_xp_if_needed(stats)

    remaining = DAILY_XP_MAX - stats.daily_xp

    if remaining <= 0:
        return 0

    xp_added = min(amount, remaining)

    stats.total_xp += xp_added
    stats.daily_xp += xp_added

    return xp_added


# ==================================================
# LEVEL
# ==================================================

def update_level(stats):

    for required_xp, level in LEVEL_THRESHOLDS:

        if stats.total_xp >= required_xp:
            stats.level = level
            break

    return stats.level


# ==================================================
# XP BADGES
# ==================================================

def get_xp_badges(stats):

    badges = []

    for required_xp, badge_name in XP_BADGES:

        if stats.total_xp >= required_xp:
            badges.append(badge_name)

    return badges


# ==================================================
# RARE BADGES
# ==================================================

def get_rare_badges(stats):

    badges = []

    if stats.errors_solved >= 50:
        badges.append(
            RARE_BADGES["error_handler"]["name"]
        )

    if stats.total_coding_seconds >= 36000:
        badges.append(
            RARE_BADGES["time_master"]["name"]
        )

    if stats.current_streak >= 100:
        badges.append(
            RARE_BADGES["streak_master"]["name"]
        )

    return badges


# ==================================================
# ALL BADGES
# ==================================================

def get_all_badges(stats):

    return (
        get_xp_badges(stats)
        + get_rare_badges(stats)
    )


# ==================================================
# DISPLAY HELPERS (DB change nahi karte)
# ==================================================

def get_effective_daily_xp(stats):
    """Aaj ka daily XP. Naya din ho aur user ne abhi code nahi kiya to 0."""

    if stats.last_xp_date != date.today():
        return 0

    return stats.daily_xp


def get_effective_streak(stats):
    """User ko dikhane wali streak. Kal ya aaj code nahi kiya to 0."""

    if stats.last_coded_date is None:
        return 0

    if stats.last_coded_date < date.today() - timedelta(days=1):
        return 0

    return stats.current_streak


def build_summary(stats, xp_before,score_before):
    """Har process_* function ka response ek jaisa rakhne ke liye."""

    daily_xp = get_effective_daily_xp(stats)

    return {
        "xp_earned": stats.total_xp - xp_before,
        "total_xp": stats.total_xp,
        "scored_earned" : stats.total_score - score_before,
        "total_earned" : stats.total_score, 
        "daily_xp": daily_xp,
        "daily_xp_remaining": max(0, DAILY_XP_MAX - daily_xp),
        "level": stats.level,
        "streak": get_effective_streak(stats),
        "badges": get_all_badges(stats)
    }


# ==================================================
# DAILY ACTIVITY
# ==================================================

def update_daily_activity(stats):

    today = date.today()

    # First coding activity
    if stats.last_coded_date is None:

        stats.current_streak = 1
        stats.last_coded_date = today

        return add_xp(
            stats,
            XP_REWARDS["daily_bonus"]
        )

    # Already coded today
    if stats.last_coded_date == today:
        return 0

    # Coded yesterday
    if stats.last_coded_date == today - timedelta(days=1):

        stats.current_streak += 1

    else:

        stats.current_streak = 1

    stats.last_coded_date = today

    return add_xp(
        stats,
        XP_REWARDS["daily_bonus"]
    )


# ==================================================
# CODE RUN
# ==================================================

def process_code_run(stats, accepted=False):

    xp_before = stats.total_xp
    score_before = stats.total_score

    # Every run gets +2
    add_xp(
        stats,
        XP_REWARDS["code_run"]
    )

    stats.total_score += 2
    stats.total_code_runs += 1

    # Accepted gets +5
    if accepted:

        add_xp(
            stats,
            XP_REWARDS["accepted"]
        )

        stats.total_score += 5

    # Daily streak + bonus
    update_daily_activity(stats)

    # Level update
    update_level(stats)

    return build_summary(stats, xp_before,score_before)


# ==================================================
# ERROR SOLVED
# ==================================================

def process_error_solved(stats):

    xp_before = stats.total_xp
    score_before = stats.total_score

    stats.errors_solved += 1

    add_xp(
        stats,
        XP_REWARDS["error_solved"]
    )

    stats.total_score += 1

    update_level(stats)

    return build_summary(stats, xp_before,score_before)


# ==================================================
# TIME CHALLENGE
# ==================================================

def process_time_challenge(stats):

    xp_before = stats.total_xp
    score_before = stats.total_score 

    add_xp(
        stats,
        XP_REWARDS["time_challenge"]
    )

    stats.total_score += 10

    update_level(stats)

    return build_summary(stats, xp_before,score_before)