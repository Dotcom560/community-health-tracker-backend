# backend/community_health_tracker/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        'message': 'Community Health Tracker API',
        'status': 'running',
        'endpoints': {
            'POST /api/token/': 'Login - Get access token',
            'POST /api/register/': 'Register new user', 
            'POST /api/analyze/': 'Analyze symptoms',
            'GET /health/': 'Health check',
        }
    })

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'message': 'API is running properly'
    })

urlpatterns = [
    path('', home, name='home'),
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path('api/', include('triage.urls')),  # This includes your triage/urls.py
]