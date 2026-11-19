from datetime import datetime
from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.db import get_notes_col, get_users_col
from utils.permissions import IsAuthenticatedMongoUser, IsAdminRole
from utils.pagination import paginate_mongo, serialize_mongo_doc

class MyNotesAPIView(APIView):
    """
    GET /api/notes - Get authenticated user's notes (paginated)
    POST /api/notes - Create a new note
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request):
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 10)
        notes_col = get_notes_col()

        user_obj_id = request.user.raw_id

        # Query supported by compound index: noteSchema.index({ userId: 1, createdAt: -1 })
        result = paginate_mongo(
            notes_col,
            filter_query={"userId": user_obj_id},
            page=page,
            limit=limit,
            sort=[("createdAt", -1)]
        )
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()

        if not title or not content:
            return Response({"success": False, "message": "Title and content are required."}, status=status.HTTP_400_BAD_REQUEST)

        now = datetime.utcnow()
        new_note = {
            "title": title,
            "content": content,
            "userId": request.user.raw_id,
            "createdAt": now,
            "updatedAt": now,
        }

        notes_col = get_notes_col()
        res = notes_col.insert_one(new_note)
        new_note['_id'] = res.inserted_id

        return Response({
            "success": True,
            "message": "Note created successfully.",
            "note": serialize_mongo_doc(new_note)
        }, status=status.HTTP_201_CREATED)


class AllNotesAdminAPIView(APIView):
    """
    GET /api/notes/all - Admin only: View all notes across the platform (paginated)
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 10)
        notes_col = get_notes_col()
        users_col = get_users_col()

        # Query supported by index: noteSchema.index({ createdAt: -1 })
        result = paginate_mongo(
            notes_col,
            filter_query={},
            page=page,
            limit=limit,
            sort=[("createdAt", -1)]
        )

        # Populate author user info
        for note in result['data']:
            try:
                author_id = ObjectId(note['userId'])
                user = users_col.find_one({"_id": author_id}, {"name": 1, "email": 1})
                if user:
                    note['userId'] = serialize_mongo_doc(user)
            except Exception:
                pass

        return Response(result, status=status.HTTP_200_OK)


class NoteDetailAPIView(APIView):
    """
    GET, PUT, DELETE /api/notes/<id>
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request, pk):
        try:
            obj_id = ObjectId(pk)
        except Exception:
            return Response({"success": False, "message": "Invalid note ID format."}, status=status.HTTP_400_BAD_REQUEST)

        notes_col = get_notes_col()
        note = notes_col.find_one({"_id": obj_id})
        if not note:
            return Response({"success": False, "message": "Note not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check permissions: owner or admin
        if request.user.role != 'admin' and str(note['userId']) != str(request.user.id):
            return Response({"success": False, "message": "Access denied: You do not own this note."}, status=status.HTTP_403_FORBIDDEN)

        # Populate author
        users_col = get_users_col()
        author = users_col.find_one({"_id": note['userId']}, {"name": 1, "email": 1})
        note_dict = serialize_mongo_doc(note)
        if author:
            note_dict['userId'] = serialize_mongo_doc(author)

        return Response({"success": True, "note": note_dict}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            obj_id = ObjectId(pk)
        except Exception:
            return Response({"success": False, "message": "Invalid note ID format."}, status=status.HTTP_400_BAD_REQUEST)

        notes_col = get_notes_col()
        note = notes_col.find_one({"_id": obj_id})
        if not note:
            return Response({"success": False, "message": "Note not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only owner can update (admin inherits)
        if request.user.role != 'admin' and str(note['userId']) != str(request.user.id):
            return Response({"success": False, "message": "Access denied: You can only update your own notes."}, status=status.HTTP_403_FORBIDDEN)

        update_data = {"updatedAt": datetime.utcnow()}
        if 'title' in request.data:
            update_data['title'] = request.data['title']
        if 'content' in request.data:
            update_data['content'] = request.data['content']

        updated = notes_col.find_one_and_update(
            {"_id": obj_id},
            {"$set": update_data},
            return_document=True
        )

        return Response({
            "success": True,
            "message": "Note updated successfully.",
            "note": serialize_mongo_doc(updated)
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            obj_id = ObjectId(pk)
        except Exception:
            return Response({"success": False, "message": "Invalid note ID format."}, status=status.HTTP_400_BAD_REQUEST)

        notes_col = get_notes_col()
        note = notes_col.find_one({"_id": obj_id})
        if not note:
            return Response({"success": False, "message": "Note not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only owner can delete (admin inherits)
        if request.user.role != 'admin' and str(note['userId']) != str(request.user.id):
            return Response({"success": False, "message": "Access denied: You can only delete your own notes."}, status=status.HTTP_403_FORBIDDEN)

        notes_col.delete_one({"_id": obj_id})

        return Response({
            "success": True,
            "message": "Note deleted successfully."
        }, status=status.HTTP_200_OK)
