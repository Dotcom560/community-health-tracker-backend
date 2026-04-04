import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

@csrf_exempt
def test_view(request):
    return JsonResponse({'message': 'API is working!'})

@csrf_exempt
def register_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username exists'}, status=400)
        User.objects.create_user(username=username, password=password)
        return JsonResponse({'success': True}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def token_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        user = authenticate(username=data.get('username'), password=data.get('password'))
        if user:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            return JsonResponse({'access': str(refresh.access_token)})
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def analyze_view(request):
    return JsonResponse({'success': True, 'triage_level': 'non_urgent'})