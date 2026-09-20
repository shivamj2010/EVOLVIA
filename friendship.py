from extensions import db
from datetime import datetime

class Friendship(db.Model):
    id = db.Column(
        db.Integer,
        primary_key = True
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable = False
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable = False
    )

    status = db.Column(
        db.String(20),
        default = 'pending',
        nullable = False
    )

    created_at = db.Column(
        db.DateTime,
        default = datetime.utcnow
    )