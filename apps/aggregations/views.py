from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.db import get_users_col
from utils.permissions import IsAuthenticatedMongoUser
from utils.pagination import serialize_mongo_doc

class UsersByInterestAggregationView(APIView):
    """
    GET /api/aggregations/users-by-interest
    Scenario 1: Group by Interests
    Constraint: Exactly one collection.aggregate() call.
    Supported by multikey index on interests.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request):
        users_col = get_users_col()

        pipeline = [
            # 1. Filter out users who do not have any interests defined
            {
                "$match": {
                    "interests": {"$exists": True, "$ne": []}
                }
            },
            # 2. Unwind the interests array to produce a document per interest
            {
                "$unwind": "$interests"
            },
            # 3. Group by interest name and aggregate user details
            {
                "$group": {
                    "_id": "$interests",
                    "userCount": {"$sum": 1},
                    "users": {
                        "$push": {
                            "_id": "$_id",
                            "name": "$name",
                            "email": "$email",
                            "role": "$role"
                        }
                    }
                }
            },
            # 4. Sort alphabetically by interest name
            {
                "$sort": {"_id": 1}
            },
            # 5. Rename _id to interest for clarity
            {
                "$project": {
                    "_id": 0,
                    "interest": "$_id",
                    "userCount": 1,
                    "users": 1
                }
            }
        ]

        result = list(users_col.aggregate(pipeline))

        return Response({
            "success": True,
            "scenario": "Scenario 1: Group by Interests (Django DRF + PyMongo)",
            "totalGroups": len(result),
            "data": serialize_mongo_doc(result)
        }, status=status.HTTP_200_OK)


class UserPostsAggregationView(APIView):
    """
    GET /api/aggregations/user-posts/<userId>
    Scenario 2: User Posts ($lookup)
    Constraint: Use a single aggregation pipeline with a $lookup stage.
    Supported by compound index on userId + createdAt.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request, userId):
        try:
            user_obj_id = ObjectId(userId)
        except Exception:
            return Response({"success": False, "message": "Invalid userId format."}, status=status.HTTP_400_BAD_REQUEST)

        users_col = get_users_col()

        # Single aggregation pipeline using $lookup stage
        pipeline = [
            # 1. Match the target user
            {
                "$match": {
                    "_id": user_obj_id
                }
            },
            # 2. Single $lookup stage to join with Posts collection
            {
                "$lookup": {
                    "from": "posts",
                    "localField": "_id",
                    "foreignField": "userId",
                    "as": "posts"
                }
            },
            # 3. Project safe fields
            {
                "$project": {
                    "name": 1,
                    "email": 1,
                    "role": 1,
                    "interests": 1,
                    "createdAt": 1,
                    "postsCount": {"$size": "$posts"},
                    "posts": 1
                }
            }
        ]

        result = list(users_col.aggregate(pipeline))
        if not result:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "scenario": "Scenario 2: User Posts ($lookup) (Django DRF + PyMongo)",
            "data": serialize_mongo_doc(result[0])
        }, status=status.HTTP_200_OK)
