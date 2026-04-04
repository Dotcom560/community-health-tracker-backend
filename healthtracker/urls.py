from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        'message': 'Community Health Tracker API',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/token/': 'Login - Get access token',
            'POST /api/register/': 'Register new user',
            'POST /api/analyze/': 'Analyze symptoms',
        }
    })

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('triage.urls')),
]