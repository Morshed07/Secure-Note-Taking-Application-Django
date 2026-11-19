import jwt
from datetime import datetime, timedelta
from bson import ObjectId
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from utils.db import get_users_col

class MongoUser:
    """Wrapper class so MongoDB documents behave like standard Django auth users"""
    def __init__(self, doc):
        self.doc = doc
        self.raw_id = doc.get('_id')
        self.id = str(self.raw_id)
        self.pk = self.id
        self.email = doc.get('email')
        self.name = doc.get('name')
        self.role = doc.get('role', 'user')
        self.interests = doc.get('interests', [])
        self.is_authenticated = True
        self.is_anonymous = False
        self.is_admin = (self.role == 'admin')

    def __str__(self):
        return f"{self.name} <{self.email}> ({self.role})"

    def to_dict(self):
        return {
            "_id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "interests": self.interests,
            "createdAt": self.doc.get("createdAt"),
            "updatedAt": self.doc.get("updatedAt"),
        }


class MongoJWTAuthentication(BaseAuthentication):
    """
    Custom JWT Authentication backend compatible with SimpleJWT and Express JWT tokens.
    Authenticates users against MongoDB's 'users' collection.
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY')
        algorithm = settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')

        try:
            payload = jwt.decode(token, signing_key, algorithms=[algorithm])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired. Please log in again.')
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f'Invalid authentication token: {str(e)}')

        user_id = payload.get('id') or payload.get('user_id')
        if not user_id:
            raise AuthenticationFailed('Token missing user identifier.')

        try:
            obj_id = ObjectId(user_id)
        except Exception:
            raise AuthenticationFailed('Invalid user ID format in token.')

        users_col = get_users_col()
        user_doc = users_col.find_one({"_id": obj_id})
        if not user_doc:
            raise AuthenticationFailed('User belonging to this token no longer exists.')

        return (MongoUser(user_doc), token)


def generate_jwt_tokens(user_doc):
    """Generates interoperable JWT tokens matching Express backend format"""
    user_id = str(user_doc.get('_id'))
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY')
    algorithm = settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')
    expiry_days = getattr(settings, 'SIMPLE_JWT', {}).get('ACCESS_TOKEN_LIFETIME', timedelta(days=7))

    payload = {
        'id': user_id,
        'email': user_doc.get('email'),
        'role': user_doc.get('role', 'user'),
        'name': user_doc.get('name'),
        'exp': datetime.utcnow() + expiry_days,
        'iat': datetime.utcnow(),
    }

    token = jwt.encode(payload, signing_key, algorithm=algorithm)
    return token
