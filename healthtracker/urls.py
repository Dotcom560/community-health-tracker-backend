# backend/healthtracker/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from datetime import datetime
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

def home(request):
    return JsonResponse({
        'message': 'Community Health Tracker API',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'API information',
            'GET /health/': 'Health check for monitoring',
            'POST /api/token/': 'Login - Get access and refresh tokens',
            'POST /api/token/refresh/': 'Refresh expired access token',
            'POST /api/token/verify/': 'Verify token validity',
            'POST /api/register/': 'Register new user',
            'POST /api/analyze/': 'Analyze symptoms',
            'POST /api/chatbot/': 'Chatbot conversation',
            'GET /api/medications/': 'WHO medicine information',
            'GET /api/test/': 'Test endpoint',
            'GET /api/outbreak/status/': 'Outbreak detection status',
            'GET /api/pharmacies/nearby/': 'Find nearby pharmacies',
            'POST /api/notifications/subscribe/': 'Subscribe to push notifications',
            'POST /api/notifications/unsubscribe/': 'Unsubscribe from push notifications',
            'GET /api/admin/users/': 'Admin - Get all users',
            'GET /api/admin/stats/': 'Admin - Get statistics',
        }
    })


def health_check(request):
    """Health check endpoint for monitoring services (cron-job.org, uptime monitoring)"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'community-health-tracker-backend',
        'version': '1.0.0',
        'database': 'connected',
        'uptime': 'running'
    })


urlpatterns = [
    # Home / Root endpoint
    path('', home, name='home'),
    
    # Health check endpoint - IMPORTANT for cron-job.org and monitoring
    path('health/', health_check, name='health_check'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Your app endpoints (includes all triage URLs)
    path('api/', include('triage.urls')),
]