# backend/healthtracker/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        'message': 'Community Health Tracker API',
        'status': 'running',
        'endpoints': {
            'GET /': 'API information',
            'GET /api/test/': 'Test endpoint',
            'POST /api/register/': 'Register new user',
            'POST /api/token/': 'Login - Get JWT token',
            'POST /api/analyze/': 'Analyze symptoms (requires auth)',
        }
    })

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('triage.urls')),
]