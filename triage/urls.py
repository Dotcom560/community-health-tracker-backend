from django.urls import path
from django.http import JsonResponse
from . import views

def register_view(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            return JsonResponse({'message': 'User created successfully', 'username': username}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

urlpatterns = [
    path('register/', register_view, name='register'),
    path('analyze/', views.analyze_symptoms, name='analyze'),
]