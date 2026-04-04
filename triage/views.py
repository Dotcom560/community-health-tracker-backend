# backend/triage/views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    """User registration endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse(
                {'error': 'Username and password required'}, 
                status=400
            )
        
        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {'error': 'Username already exists'}, 
                status=400
            )
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        return JsonResponse(
            {
                'success': True,
                'message': 'User created successfully',
                'username': username
            },
            status=201
        )
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def token_view(request):
    """Login endpoint - returns JWT token"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse(
                {'error': 'Username and password required'}, 
                status=400
            )
        
        user = authenticate(username=username, password=password)
        
        if user:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            return JsonResponse(
                {
                    'success': True,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'username': user.username
                }
            )
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Token error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_view(request):
    """Symptom analysis endpoint"""
    try:
        data = json.loads(request.body)
        symptoms = data.get('symptoms_text', '')
        
        # Simple analysis logic
        symptoms_lower = symptoms.lower()
        
        if 'chest pain' in symptoms_lower or 'difficulty breathing' in symptoms_lower:
            triage_level = 'emergency'
            triage_display = 'Emergency'
            recommendation = 'SEEK IMMEDIATE MEDICAL ATTENTION! Call emergency services.'
        elif 'fever' in symptoms_lower and 'headache' in symptoms_lower:
            triage_level = 'urgent'
            triage_display = 'Urgent'
            recommendation = 'Consult a doctor within 24 hours. Rest and stay hydrated.'
        elif 'fever' in symptoms_lower:
            triage_level = 'urgent'
            triage_display = 'Urgent'
            recommendation = 'Monitor your temperature. Seek care if fever persists for more than 3 days.'
        else:
            triage_level = 'non_urgent'
            triage_display = 'Non-Urgent'
            recommendation = 'Rest, stay hydrated, and monitor symptoms. Consult a doctor if symptoms worsen.'
        
        return JsonResponse(
            {
                'success': True,
                'triage_level': triage_level,
                'triage_display': triage_display,
                'possible_condition': 'Based on symptoms',
                'recommendation': recommendation,
                'confidence_score': 0.85,
                'medications': []
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def test_view(request):
    """Simple test endpoint to verify API is working"""
    return JsonResponse({'message': 'API is working!', 'status': 'ok'})