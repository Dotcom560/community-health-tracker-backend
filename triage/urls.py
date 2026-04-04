from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import json

@csrf_exempt
def token_view(request):
    """Custom token view that returns JSON"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(username=username, password=password)
            if user:
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                })
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email', '')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({'error': 'Username and password required'}, status=400)
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            return JsonResponse({
                'message': 'User created successfully',
                'username': username
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def analyze_view(request):
    """Symptom analysis view"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symptoms = data.get('symptoms_text', '')
            temperature = data.get('temperature', 0)
            duration = data.get('duration_days', 1)
            
            # Simple analysis logic
            symptoms_lower = symptoms.lower()
            
            if 'chest pain' in symptoms_lower or 'difficulty breathing' in symptoms_lower:
                triage_level = 'emergency'
                triage_display = 'Emergency'
                recommendation = '⚠️ SEEK IMMEDIATE MEDICAL ATTENTION! Call emergency services.'
            elif 'fever' in symptoms_lower and 'headache' in symptoms_lower:
                triage_level = 'urgent'
                triage_display = 'Urgent'
                recommendation = 'Consult a doctor within 24 hours. Rest and stay hydrated.'
            elif 'fever' in symptoms_lower:
                triage_level = 'urgent'
                triage_display = 'Urgent'
                recommendation = f'Monitor your temperature. Current: {temperature}°C. Seek care if fever persists >3 days.'
            else:
                triage_level = 'non_urgent'
                triage_display = 'Non-Urgent'
                recommendation = 'Rest, stay hydrated, and monitor symptoms. Consult a doctor if symptoms worsen.'
            
            return JsonResponse({
                'success': True,
                'triage_level': triage_level,
                'triage_display': triage_display,
                'possible_condition': 'Symptom analysis based on description',
                'recommendation': recommendation,
                'confidence_score': 0.85,
                'temperature': temperature,
                'duration_days': duration,
                'medications': []
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

urlpatterns = [
    path('token/', token_view, name='token'),
    path('register/', register_view, name='register'),
    path('analyze/', analyze_view, name='analyze'),
]