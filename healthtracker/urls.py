from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({'message': 'API is running', 'status': 'ok'})

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/', include('triage.urls')),
]