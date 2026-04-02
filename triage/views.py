from django.shortcuts import render

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import SymptomLog, TriageResult, Medication, OutbreakAlert
from .serializers import (
    UserRegistrationSerializer, UserSerializer, SymptomLogSerializer,
    TriageResultSerializer, MedicationSerializer, OutbreakAlertSerializer
)
from .triage_engine import TriageEngine
from .medication_engine import MedicationEngine

logger = logging.getLogger(__name__)

# Initialize engines
triage_engine = TriageEngine()
medication_engine = MedicationEngine()

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_symptoms(request):
    """
    Analyze symptoms and provide triage recommendation
    """
    try:
        # Extract data from request
        symptoms_text = request.data.get('symptoms_text', '')
        temperature = request.data.get('temperature')
        duration_days = request.data.get('duration_days')
        
        if not symptoms_text:
            return Response({
                'error': 'Please provide symptom description'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create symptom log
        symptom_log = SymptomLog.objects.create(
            user=request.user,
            symptoms_text=symptoms_text,
            temperature=temperature if temperature else None,
            duration_days=duration_days if duration_days else None,
            age_group=request.user.profile.age_group if hasattr(request.user, 'profile') else ''
        )
        
        # Analyze symptoms with AI
        analysis_result = triage_engine.analyze_symptoms(symptoms_text)
        
        # Create triage result
        triage_result = TriageResult.objects.create(
            symptom_log=symptom_log,
            recommendation=analysis_result['recommendation'],
            confidence_score=analysis_result['confidence'],
            possible_condition=analysis_result['possible_condition'],
            ai_analysis=analysis_result['analysis']
        )
        
        # Get medication recommendations
        medications = medication_engine.get_medications_for_symptoms(
            symptoms_text, 
            analysis_result['possible_condition']
        )
        
        # Format response
        response_data = {
            'symptom_log': SymptomLogSerializer(symptom_log).data,
            'triage_result': TriageResultSerializer(triage_result).data,
            'medication_recommendations': medication_engine.format_medication_response(
                medications, triage_result
            ),
            'analysis_method': analysis_result.get('method', 'rule_based')
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in analyze_symptoms: {str(e)}")
        return Response({
            'error': 'An error occurred while analyzing symptoms',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_history(request):
    """Get user's symptom check history"""
    symptom_logs = SymptomLog.objects.filter(user=request.user).order_by('-created_at')
    
    # Add triage results to each log
    data = []
    for log in symptom_logs:
        log_data = SymptomLogSerializer(log).data
        try:
            log_data['triage_result'] = TriageResultSerializer(log.triage_result).data
        except TriageResult.DoesNotExist:
            log_data['triage_result'] = None
        data.append(log_data)
    
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_outbreak_alerts(request):
    """Get active outbreak alerts"""
    region = request.query_params.get('region', None)
    
    alerts = OutbreakAlert.objects.filter(is_active=True)
    if region:
        alerts = alerts.filter(region__icontains=region)
    
    serializer = OutbreakAlertSerializer(alerts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_medications(request):
    """Get list of medications (optional filtering)"""
    medications = Medication.objects.all()
    
    # Filter by category if provided
    category = request.query_params.get('category', None)
    if category:
        medications = medications.filter(category__icontains=category)
    
    serializer = MedicationSerializer(medications, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analytics(request):
    """
    Get analytics data for health workers/admin
    Only accessible to health workers and admins
    """
    # Check user role
    if not hasattr(request.user, 'profile') or request.user.profile.role not in ['health_worker', 'admin']:
        return Response({
            'error': 'You do not have permission to access analytics'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get date range
    days = int(request.query_params.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # Basic analytics
    total_logs = SymptomLog.objects.filter(created_at__gte=start_date).count()
    
    # Symptoms by recommendation
    triage_counts = TriageResult.objects.filter(
        symptom_log__created_at__gte=start_date
    ).values('recommendation').annotate(
        count=Count('id')
    )
    
    # Common symptoms (word frequency)
    all_symptoms = SymptomLog.objects.filter(
        created_at__gte=start_date
    ).values_list('symptoms_text', flat=True)
    
    # Simple word frequency (you can make this more sophisticated)
    word_count = {}
    for text in all_symptoms:
        words = text.lower().split()
        for word in words:
            if len(word) > 3:  # Skip small words
                word_count[word] = word_count.get(word, 0) + 1
    
    top_symptoms = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return Response({
        'period_days': days,
        'total_symptom_logs': total_logs,
        'triage_distribution': triage_counts,
        'top_symptoms': [{'symptom': k, 'count': v} for k, v in top_symptoms],
        'timestamp': timezone.now()
    })
