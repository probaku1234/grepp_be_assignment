import jwt
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

JWT_SECRET = os.environ.get('JWT_SECRET')


def encode_jwt(id, user_id, role):
    payload = {
        'id': id,
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60 * 60 * 24)
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return jwt_token


def decode_jwt(token):
    return jwt.decode(token, JWT_SECRET, algorithms='HS256')
