import json

from flask import request


def get_json_body():
    """
    Request body ko safely dict ki tarah return karta hai.
    Body galat ho (JSON nahi / dict nahi) to None return karta hai.
    Postman kabhi kabhi JSON ko string bana ke bhejta hai, wo bhi handle hota hai.
    """
    data = request.get_json(silent=True)

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return None

    return data if isinstance(data, dict) else None