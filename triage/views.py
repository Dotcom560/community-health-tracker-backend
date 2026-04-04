# backend/triage/views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def token_view(request):
    """Custom JWT token view - Login endpoint"""
    try:
        # Parse request body
        body = json.loads(request.body.decode('utf-8'))
        username = body.get('username', '').strip()
        password = body.get('password', '')
        
        # Validate input
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required'
            }, status=400)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            # Try to get user to check if exists
            try:
                user_obj = User.objects.get(username=username)
                if not user_obj.check_password(password):
                    return JsonResponse({
                        'error': 'Invalid password'
                    }, status=401)
            except User.DoesNotExist:
                return JsonResponse({
                    'error': 'User does not exist'
                }, status=401)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return JsonResponse({
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.username,
            'is_admin': user.is_staff or user.is_superuser
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON body'
        }, status=400)
    except Exception as e:
        logger.error(f"Token view error: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    """User registration endpoint"""
    try:
        # Parse request body
        body = json.loads(request.body.decode('utf-8'))
        username = body.get('username', '').strip()
        email = body.get('email', '').strip()
        password = body.get('password', '')
        
        # Validate input
        if not username:
            return JsonResponse({
                'error': 'Username is required'
            }, status=400)
        
        if not password:
            return JsonResponse({
                'error': 'Password is required'
            }, status=400)
        
        if len(password) < 6:
            return JsonResponse({
                'error': 'Password must be at least 6 characters'
            }, status=400)
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'error': 'Username already exists'
            }, status=400)
        
        # Check if email exists (if provided)
        if email and User.objects.filter(email=email).exists():
            return JsonResponse({
                'error': 'Email already registered'
            }, status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Set as admin if username is Dotcom
        if username.lower() == 'dotcom':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User created successfully',
            'username': username,
            'email': email
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON body'
        }, status=400)
    except Exception as e:
        logger.error(f"Register view error: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_view(request):
    """Symptom analysis endpoint"""
    try:
        # Parse request body
        body = json.loads(request.body.decode('utf-8'))
        symptoms_text = body.get('symptoms_text', '').strip()
        temperature = body.get('temperature', 0)
        duration_days = body.get('duration_days', 1)
        
        # Validate input
        if not symptoms_text:
            return JsonResponse({
                'error': 'Symptoms description is required'
            }, status=400)
        
        # Simple rule-based analysis
        symptoms_lower = symptoms_text.lower()
        
        # Emergency keywords
        emergency_keywords = [
            'chest pain', 'difficulty breathing', 'shortness of breath',
            'severe bleeding', 'unconscious', 'stroke', 'heart attack',
            'cannot breathe', 'choking', 'severe allergic reaction'
        ]
        
        # Urgent keywords
        urgent_keywords = [
            'fever', 'high temperature', 'headache', 'vomiting',
            'diarrhea', 'dehydration', 'infection', 'pain'
        ]
        
        # Check for emergency
        for keyword in emergency_keywords:
            if keyword in symptoms_lower:
                return JsonResponse({
                    'success': True,
                    'triage_level': 'emergency',
                    'triage_display': '🚨 EMERGENCY 🚨',
                    'possible_condition': 'Potential emergency condition detected',
                    'recommendation': '⚠️ SEEK IMMEDIATE MEDICAL ATTENTION! Call emergency services or go to the nearest hospital immediately.',
                    'confidence_score': 0.95,
                    'temperature': temperature,
                    'duration_days': duration_days,
                    'medications': []
                })
        
        # Check for urgent
        urgent_score = 0
        for keyword in urgent_keywords:
            if keyword in symptoms_lower:
                urgent_score += 1
        
        if urgent_score >= 2 or temperature > 38.5:
            return JsonResponse({
                'success': True,
                'triage_level': 'urgent',
                'triage_display': '⚠️ URGENT ⚠️',
                'possible_condition': 'Condition requiring prompt medical attention',
                'recommendation': 'Consult a healthcare provider within 24 hours. Monitor your symptoms closely.',
                'confidence_score': 0.85,
                'temperature': temperature,
                'duration_days': duration_days,
                'medications': [
                    {
                        'name': 'Acetaminophen (Paracetamol)',
                        'dosage': '500mg every 4-6 hours as needed',
                        'note': 'Do not exceed 3000mg per day'
                    }
                ] if temperature > 38.0 else []
            })
        
        # Non-urgent
        return JsonResponse({
            'success': True,
            'triage_level': 'non_urgent',
            'triage_display': '💚 Non-Urgent',
            'possible_condition': 'General symptoms',
            'recommendation': 'Rest, stay hydrated, and monitor your symptoms. If symptoms worsen or persist for more than 3 days, consult a healthcare provider.',
            'confidence_score': 0.75,
            'temperature': temperature,
            'duration_days': duration_days,
            'medications': [
                {
                    'name': 'Rest and Hydration',
                    'dosage': 'Drink 8-10 glasses of water daily',
                    'note': 'Get adequate sleep and rest'
                }
            ]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON body'
        }, status=400)
    except Exception as e:
        logger.error(f"Analyze view error: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Community Health Tracker API is running',
        'version': '1.0.0',
        'timestamp': str(datetime.now())
    })


def home(request):
    """Home endpoint - API information"""
    return JsonResponse({
        'name': 'Community Health Tracker API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'POST /api/token/': 'Login - Get access token',
            'POST /api/register/': 'Register new user',
            'POST /api/analyze/': 'Analyze symptoms',
            'GET /health/': 'Health check',
        },
        'authentication': 'Bearer token required for /api/analyze/'
    })