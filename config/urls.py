from django.urls import path, include
from django.http import JsonResponse
from datetime import datetime

def health_check(request):
    return JsonResponse({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "DigiNote Django REST API",
        "framework": "Django + DRF + PyMongo"
    })

urlpatterns = [
    # Health check
    path('api/health/', health_check, name='health-check'),
    path('api/health', health_check),

    # App API routes
    path('api/', include('apps.authentication.urls')),
    path('api/', include('apps.notes.urls')),
    path('api/', include('apps.posts.urls')),
    path('api/', include('apps.aggregations.urls')),
]
