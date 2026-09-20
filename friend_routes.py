from flask import Blueprint, request,jsonify
from flask_jwt_extended import jwt_required , get_jwt_identity

from extensions import db
from models.user import User
from models.friendship import Friendship

friend_bp = Blueprint('friend',__name__)

#===============================================
# SEND friend request
#===============================================

@friend_bp.route('/api/friends/request', methods=['POST'])
@jwt_required()
def send_friend_request():

    user_id = int(get_jwt_identity())

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be JSON object"
        }), 400

    username = data.get("username")

    if not username:
        return jsonify({
            "error": "Username is required"
        }), 400

    receiver = User.query.filter_by(
        username=username
    ).first()

    if not receiver:
        return jsonify({
            "error": "User not found"
        }), 404

    if receiver.id == user_id:
        return jsonify({
            "error": "You cannot send a request to yourself"
        }), 400

    existing = Friendship.query.filter(
        (
            (Friendship.sender_id == user_id) &
            (Friendship.receiver_id == receiver.id)
        ) |
        (
            (Friendship.sender_id == receiver.id) &
            (Friendship.receiver_id == user_id)
        )
    ).first()

    if existing:

        if existing.status == "accepted":
            return jsonify({
                "error": "Already friends"
            }), 400

        if existing.status == "pending":
            return jsonify({
                "error": "Friend request already exists"
            }), 400

    friendship = Friendship(
        sender_id=user_id,
        receiver_id=receiver.id,
        status="pending"
    )

    db.session.add(friendship)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Friend request sent",
        "request_id": friendship.id
    }), 201

#====================================================
#View Pending Request
#====================================================

@friend_bp.route('/api/friends/request',methods=['GET'])
@jwt_required()

def get_friend_requests():
    user_id = int(get_jwt_identity())
    requests = Friendship.query.filter_by(receiver_id=user_id , status="pending").all()

    result = []

    for friendship in requests:
        sender = User.query.get(friendship.sender_id)
        result.append({
            "request_id" : friendship.id,
            "user_id" : sender.id,
            "username" : sender.username,
            "created_at" : friendship.created_at.isoformat()
        })

    return jsonify({
        "requests" : result
    }),200

#==============================================================
# Accept Friend Request
#==============================================================

@friend_bp.route('/api/friends/request/<int:request_id>/accept', methods = ['POST'])
@jwt_required()

def accept_friend_request(request_id):
    user_id = int(get_jwt_identity())
    friendship = Friendship.query.filter_by(
        id = request_id,
        receiver_id=user_id,
        status = "pending"
    ).first()

    if not friendship:
        return jsonify({
            "error" : "Friend request not found"
        }),404

    friendship.status = "accepted"

    db.session.commit()
    return jsonify({
        "success" : True,
        "message" : "friend request accepted"
    }),200

# =====================================================
# Reject Friend Request
# =====================================================

@friend_bp.route('/api/friends/request/<int:request_id>/reject',methods = ['POST'])
@jwt_required()

def reject_friend_request(request_id):
    user_id = int(get_jwt_identity())

    friendship =  Friendship.query.filter_by(
        id = request_id,
        receiver_id = user_id,
        status = "pending"
    ).first()

    if not friendship:
        return jsonify({
            "success" : True,
            "message" : "Friend request rejected"
        }),200

# ==================================================
# FRIENDS LIST
# ==================================================

@friend_bp.route('/api/friends', methods=['GET'])
@jwt_required()
def get_friends():

    user_id = int(get_jwt_identity())

    # ----------------------------------------------
    # DEBUG: database me saari friendships dekho
    # ----------------------------------------------

    all_friendships = Friendship.query.all()

    print("====================================")
    print("USER ID:", user_id)

    print("ALL FRIENDSHIPS:", [
        {
            "id": f.id,
            "sender": f.sender_id,
            "receiver": f.receiver_id,
            "status": f.status
        }
        for f in all_friendships
    ])

    # ----------------------------------------------
    # Sirf accepted friendships
    # ----------------------------------------------

    friendships = Friendship.query.filter(
        (
            (Friendship.sender_id == user_id) |
            (Friendship.receiver_id == user_id)
        ),
        Friendship.status == "accepted"
    ).all()

    print("ACCEPTED FRIENDSHIPS:", [
        {
            "id": f.id,
            "sender": f.sender_id,
            "receiver": f.receiver_id,
            "status": f.status
        }
        for f in friendships
    ])

    # ----------------------------------------------
    # Friends list
    # ----------------------------------------------

    friends = []

    for friendship in friendships:

        if friendship.sender_id == user_id:
            friend_id = friendship.receiver_id
        else:
            friend_id = friendship.sender_id

        friend = User.query.get(friend_id)

        if friend:

            friends.append({
                "user_id": friend.id,
                "username": friend.username
            })

    print("FINAL FRIENDS:", friends)
    print("====================================")

    return jsonify({
        "friends": friends
    }), 200

