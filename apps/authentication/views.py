import bcrypt
from datetime import datetime
from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.db import get_users_col
from utils.jwt_auth import generate_jwt_tokens
from utils.permissions import IsAuthenticatedMongoUser, IsAdminRole
from utils.pagination import paginate_mongo, serialize_mongo_doc
from .serializers import RegisterSerializer, LoginSerializer, UserUpdateSerializer

class RegisterAPIView(APIView):
    """
    POST /api/auth/register
    Public registration endpoint. Hashes password using bcrypt.
    """
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        users_col = get_users_col()

        # Check existing email using { email: 1 } unique index
        if users_col.find_one({"email": data['email'].lower().strip()}):
            return Response({"success": False, "message": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Hash password with bcrypt
        salt = bcrypt.gensalt(10)
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), salt).decode('utf-8')

        now = datetime.utcnow()
        new_user = {
            "name": data['name'].strip(),
            "email": data['email'].lower().strip(),
            "password": hashed_password,
            "role": data.get('role', 'user'),
            "interests": data.get('interests', []),
            "createdAt": now,
            "updatedAt": now,
        }

        result = users_col.insert_one(new_user)
        new_user['_id'] = result.inserted_id

        token = generate_jwt_tokens(new_user)
        user_response = serialize_mongo_doc(new_user)
        user_response.pop('password', None)

        return Response({
            "success": True,
            "message": "User registered successfully.",
            "token": token,
            "user": user_response
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """
    POST /api/auth/login
    Public login endpoint. Authenticates against MongoDB and returns JWT token.
    """
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower().strip()
        password = serializer.validated_data['password']

        users_col = get_users_col()
        user_doc = users_col.find_one({"email": email})
        if not user_doc:
            return Response({"success": False, "message": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # Verify password with bcrypt
        stored_hash = user_doc.get('password', '').encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return Response({"success": False, "message": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        token = generate_jwt_tokens(user_doc)
        user_response = serialize_mongo_doc(user_doc)
        user_response.pop('password', None)

        return Response({
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": user_response
        }, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    """
    GET /api/auth/me
    Retrieves the currently authenticated user's profile.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request):
        return Response({
            "success": True,
            "user": request.user.to_dict()
        }, status=status.HTTP_200_OK)


class UserListCreateAPIView(APIView):
    """
    GET /api/users - List users with pagination (Admin only)
    POST /api/users - Create user (Admin only)
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 10)
        users_col = get_users_col()

        # Query supported by index: userSchema.index({ createdAt: -1 })
        result = paginate_mongo(
            users_col,
            filter_query={},
            page=page,
            limit=limit,
            sort=[("createdAt", -1)],
            projection={"password": 0}
        )
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        users_col = get_users_col()

        if users_col.find_one({"email": data['email'].lower().strip()}):
            return Response({"success": False, "message": "Email is already in use."}, status=status.HTTP_400_BAD_REQUEST)

        salt = bcrypt.gensalt(10)
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), salt).decode('utf-8')
        now = datetime.utcnow()

        user_doc = {
            "name": data['name'].strip(),
            "email": data['email'].lower().strip(),
            "password": hashed_password,
            "role": data.get('role', 'user'),
            "interests": data.get('interests', []),
            "createdAt": now,
            "updatedAt": now,
        }

        res = users_col.insert_one(user_doc)
        user_doc['_id'] = res.inserted_id
        response_data = serialize_mongo_doc(user_doc)
        response_data.pop('password', None)

        return Response({
            "success": True,
            "message": "User created successfully by admin.",
            "user": response_data
        }, status=status.HTTP_201_CREATED)


class UserDetailAPIView(APIView):
    """
    GET, PUT, DELETE /api/users/<id>
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request, pk):
        try:
            obj_id = ObjectId(pk)
        except Exception:
            return Response({"success": False, "message": "Invalid user ID format."}, status=status.HTTP_400_BAD_REQUEST)

        # Only admin or self
        if request.user.role != 'admin' and str(request.user.id) != pk:
            return Response({"success": False, "message": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        users_col = get_users_col()
        user_doc = users_col.find_one({"_id": obj_id}, {"password": 0})
        if not user_doc:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"success": True, "user": serialize_mongo_doc(user_doc)}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if request.user.role != 'admin':
            return Response({"success": False, "message": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        try:
            obj_id = ObjectId(pk)
        except Exception:
            return Response({"success": False, "message": "Invalid user ID format."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        update_fields = {"updatedAt": datetime.utcnow()}
        for k, v in serializer.validated_data.items():
            if v is not None:
                update_fields[k] = v

        users_col = get_users_col()
        result = users_col.find_one_and_update(
            {"_id": obj_id},
            {"$set": update_fields},
            return_document=True,
            projection={"password": 0}
        )
        if not result:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"success": True, "message": "User updated successfully.", "user": serialize_mongo_doc(result)}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        if request.user.role != 'admin':
            return Response({"success": False, "message": "Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        try:
            obj_id = ObjectId(pk)
        except Exception:
            return Response({"success": False, "message": "Invalid user ID format."}, status=status.HTTP_400_BAD_REQUEST)

        if str(request.user.id) == pk:
            return Response({"success": False, "message": "You cannot delete your own admin account."}, status=status.HTTP_400_BAD_REQUEST)

        users_col = get_users_col()
        result = users_col.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"success": True, "message": "User deleted successfully."}, status=status.HTTP_200_OK)
