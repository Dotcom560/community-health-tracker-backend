from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        'message': 'Community Health Tracker API',
        'status': 'running',
        'endpoints': {
            'token': '/api/token/',
            'refresh': '/api/token/refresh/',
            'verify': '/api/token/verify/',
            'register': '/api/register/',
            'analyze': '/api/analyze/'
        }
    })

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Your app endpoints
    path('api/', include('triage.urls')),
]