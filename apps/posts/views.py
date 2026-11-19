from datetime import datetime
from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.db import get_posts_col, get_users_col
from utils.permissions import IsAuthenticatedMongoUser
from utils.pagination import paginate_mongo, serialize_mongo_doc

class PostsListCreateAPIView(APIView):
    """
    GET /api/posts - Public feed with pagination
    POST /api/posts - Authenticated post creation
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticatedMongoUser()]
        return []

    def get(self, request):
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 10)
        posts_col = get_posts_col()
        users_col = get_users_col()

        # Supported by index: postSchema.index({ createdAt: -1 })
        result = paginate_mongo(
            posts_col,
            filter_query={},
            page=page,
            limit=limit,
            sort=[("createdAt", -1)]
        )

        for post in result['data']:
            try:
                author_id = ObjectId(post['userId'])
                user = users_col.find_one({"_id": author_id}, {"name": 1, "email": 1})
                if user:
                    post['userId'] = serialize_mongo_doc(user)
            except Exception:
                pass

        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()

        if not title or not content:
            return Response({"success": False, "message": "Title and content are required."}, status=status.HTTP_400_BAD_REQUEST)

        now = datetime.utcnow()
        new_post = {
            "title": title,
            "content": content,
            "userId": request.user.raw_id,
            "createdAt": now,
            "updatedAt": now,
        }

        posts_col = get_posts_col()
        res = posts_col.insert_one(new_post)
        new_post['_id'] = res.inserted_id

        return Response({
            "success": True,
            "message": "Post created successfully.",
            "post": serialize_mongo_doc(new_post)
        }, status=status.HTTP_201_CREATED)
