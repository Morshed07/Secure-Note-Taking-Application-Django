import math
from pymongo import DESCENDING

def serialize_mongo_doc(doc):
    """Recursively converts BSON ObjectIds to string for JSON serialization"""
    if not doc:
        return doc
    if isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]
    if isinstance(doc, dict):
        res = {}
        for k, v in doc.items():
            if k == '_id':
                res['_id'] = str(v)
            elif k == 'userId':
                res['userId'] = str(v)
            elif isinstance(v, (dict, list)):
                res[k] = serialize_mongo_doc(v)
            elif hasattr(v, 'isoformat'):
                res[k] = v.isoformat()
            else:
                res[k] = v
        return res
    return doc


def paginate_mongo(collection, filter_query=None, page=1, limit=10, sort=None, projection=None):
    """
    Standard pagination helper for MongoDB queries in Django views.
    Ensures optimal cursor skip/limit supported by indexes.
    """
    if filter_query is None:
        filter_query = {}

    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = min(100, max(1, int(limit)))
    except (ValueError, TypeError):
        limit = 10

    if sort is None:
        sort = [("createdAt", DESCENDING)]

    skip = (page - 1) * limit

    cursor = collection.find(filter_query, projection).sort(sort).skip(skip).limit(limit)
    data = [serialize_mongo_doc(doc) for doc in cursor]

    total_count = collection.count_documents(filter_query)
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    return {
        "success": True,
        "data": data,
        "pagination": {
            "totalCount": total_count,
            "currentPage": page,
            "totalPages": total_pages,
            "limit": limit,
            "hasNextPage": page < total_pages,
            "hasPrevPage": page > 1,
        }
    }
