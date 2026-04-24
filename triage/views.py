import json
import re
import requests
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from django.core.mail import send_mail
from django.conf import settings

# ========== PUSH NOTIFICATION SUBSCRIPTION MODEL (In-memory for now) ==========
push_subscriptions = []  # List to store active subscriptions

# ========== WHO ESSENTIAL MEDICINES LIST ==========
WHO_MEDICINES = {
    'fever': [
        {'name': 'Paracetamol (Acetaminophen)', 'dosage': '500mg every 4-6 hours', 'max_daily': '3000mg', 'indication': 'Fever and mild to moderate pain', 'warning': 'Do not exceed recommended dose. Can cause liver damage.'},
        {'name': 'Ibuprofen', 'dosage': '200-400mg every 6-8 hours', 'max_daily': '1200mg', 'indication': 'Fever and inflammation', 'warning': 'Take with food. Not for people with stomach ulcers.'}
    ],
    'headache': [
        {'name': 'Paracetamol', 'dosage': '500mg as needed', 'max_daily': '3000mg', 'indication': 'Tension headaches and mild pain'},
        {'name': 'Aspirin', 'dosage': '300-600mg every 4-6 hours', 'max_daily': '3600mg', 'indication': 'Migraine and inflammation', 'warning': 'Not for children under 12 years'}
    ],
    'cough': [
        {'name': 'Honey (natural remedy)', 'dosage': '1-2 teaspoons as needed', 'indication': 'Cough relief', 'warning': 'Not for infants under 1 year'},
        {'name': 'Guaifenesin', 'dosage': '200-400mg every 4 hours', 'max_daily': '2400mg', 'indication': 'Chest congestion and phlegm'}
    ],
    'cold': [
        {'name': 'Rest and hydration', 'dosage': '8-10 glasses of water daily', 'indication': 'Recovery support'},
        {'name': 'Vitamin C', 'dosage': '500-1000mg daily', 'indication': 'Immune support'},
        {'name': 'Zinc lozenges', 'dosage': '10-20mg daily', 'indication': 'Reduce cold duration', 'max_daily': '7 days'}
    ],
    'diarrhea': [
        {'name': 'Oral Rehydration Solution (ORS)', 'dosage': 'As needed', 'indication': 'Prevent dehydration'},
        {'name': 'Zinc supplements', 'dosage': '10-20mg daily for 10-14 days', 'indication': 'Reduce severity and duration'},
        {'name': 'Probiotics', 'dosage': 'As directed', 'indication': 'Restore gut health'}
    ],
    'nausea': [
        {'name': 'Ginger', 'dosage': '1g fresh or 500mg capsule', 'indication': 'Nausea relief'},
        {'name': 'Peppermint tea', 'dosage': '1-2 cups as needed', 'indication': 'Settle stomach'}
    ],
    'pain': [
        {'name': 'Paracetamol', 'dosage': '500mg every 4-6 hours', 'max_daily': '3000mg', 'indication': 'General pain relief'},
        {'name': 'Ibuprofen', 'dosage': '200-400mg every 6-8 hours', 'max_daily': '1200mg', 'indication': 'Inflammatory pain', 'warning': 'Take with food'}
    ],
    'allergy': [
        {'name': 'Cetirizine', 'dosage': '10mg once daily', 'indication': 'Allergy relief', 'warning': 'May cause drowsiness'},
        {'name': 'Loratadine', 'dosage': '10mg once daily', 'indication': 'Non-drowsy allergy relief'}
    ]
}

# ========== HOME REMEDIES DATABASE ==========
HOME_REMEDIES = {
    'fever': ['Rest and stay hydrated', 'Use cool compress on forehead', 'Take lukewarm bath'],
    'cough': ['Drink warm fluids like honey lemon tea', 'Use a humidifier', 'Gargle with salt water'],
    'headache': ['Rest in a dark, quiet room', 'Apply cold or warm compress', 'Stay hydrated'],
    'cold': ['Get plenty of rest', 'Drink warm fluids', 'Use saline nasal spray'],
    'sore_throat': ['Gargle with warm salt water', 'Drink honey tea', 'Use throat lozenges']
}

# ========== WARNING SIGNS DATABASE ==========
WARNING_SIGNS = {
    'emergency': [
        'Chest pain or pressure',
        'Difficulty breathing or shortness of breath',
        'Severe bleeding',
        'Loss of consciousness',
        'Sudden severe headache',
        'Difficulty speaking or confusion',
        'Severe allergic reaction (swelling of face/tongue)'
    ],
    'urgent': [
        'Fever above 39.5°C (103°F)',
        'Severe pain not relieved by medication',
        'Persistent vomiting (can\'t keep liquids down)',
        'Signs of dehydration (dark urine, dry mouth)',
        'Symptoms lasting more than 5 days'
    ]
}

# ========== MOCK REPORTS DATA ==========
MOCK_REPORTS = {
    'emergency': [
        {'id': 1, 'date': '2026-04-06', 'symptoms': 'Chest pain with shortness of breath', 'patient': 'John Doe', 'status': 'Resolved'},
        {'id': 2, 'date': '2026-04-05', 'symptoms': 'Difficulty breathing, wheezing', 'patient': 'Jane Smith', 'status': 'In Progress'},
        {'id': 3, 'date': '2026-04-04', 'symptoms': 'Severe allergic reaction', 'patient': 'Mike Johnson', 'status': 'Resolved'},
    ],
    'urgent': [
        {'id': 4, 'date': '2026-04-06', 'symptoms': 'High fever 40°C with severe headache', 'patient': 'Sarah Williams', 'status': 'Under Review'},
        {'id': 5, 'date': '2026-04-05', 'symptoms': 'Persistent vomiting, dehydration', 'patient': 'Tom Brown', 'status': 'Resolved'},
        {'id': 6, 'date': '2026-04-04', 'symptoms': 'Severe abdominal pain', 'patient': 'Emily Davis', 'status': 'In Progress'},
    ],
    'non_urgent': [
        {'id': 7, 'date': '2026-04-06', 'symptoms': 'Mild cough and cold', 'patient': 'Chris Wilson', 'status': 'Resolved'},
        {'id': 8, 'date': '2026-04-05', 'symptoms': 'Minor headache', 'patient': 'Patricia Lee', 'status': 'Resolved'},
    ]
}

# ========== OUTBREAK DETECTION SYSTEM ==========

class OutbreakDetector:
    """Detects potential disease outbreaks using statistical analysis"""
    
    def __init__(self):
        self.thresholds = {
            'emergency': 5.0,
            'warning': 3.0,
            'watch': 1.5
        }
        
        self.reportable_symptoms = {
            'fever': ['fever', 'high temperature', 'pyrexia'],
            'respiratory': ['cough', 'difficulty breathing', 'shortness of breath'],
            'gastrointestinal': ['diarrhea', 'vomiting', 'nausea', 'stomach pain'],
            'neurological': ['headache', 'confusion', 'seizure'],
            'rash': ['rash', 'skin lesions', 'hives']
        }
    
    def analyze_symptom_trends(self, recent_reports, baseline_data=None):
        """Analyze symptom trends for outbreak detection"""
        if not recent_reports:
            return {'status': 'insufficient_data', 'alerts': []}
        
        symptom_counts = defaultdict(int)
        for report in recent_reports:
            symptoms = report.get('symptoms', '').lower()
            for category, keywords in self.reportable_symptoms.items():
                for keyword in keywords:
                    if keyword in symptoms:
                        symptom_counts[category] += 1
                        break
        
        total_reports = len(recent_reports)
        rates = {category: (count / total_reports) * 100 for category, count in symptom_counts.items()}
        
        alerts = []
        if baseline_data:
            for category, current_rate in rates.items():
                baseline_rate = baseline_data.get(category, 1.0)
                if baseline_rate > 0:
                    ratio = current_rate / baseline_rate
                    
                    if ratio >= self.thresholds['emergency']:
                        alerts.append({
                            'level': 'emergency',
                            'category': category,
                            'message': f'EMERGENCY: {category} symptoms at {ratio:.1f}x normal rate',
                            'current_rate': round(current_rate, 1),
                            'baseline_rate': round(baseline_rate, 1),
                            'action_required': 'IMMEDIATE INVESTIGATION REQUIRED'
                        })
                    elif ratio >= self.thresholds['warning']:
                        alerts.append({
                            'level': 'warning',
                            'category': category,
                            'message': f'WARNING: {category} symptoms at {ratio:.1f}x normal rate',
                            'current_rate': round(current_rate, 1),
                            'baseline_rate': round(baseline_rate, 1),
                            'action_required': 'Alert health authorities'
                        })
                    elif ratio >= self.thresholds['watch']:
                        alerts.append({
                            'level': 'watch',
                            'category': category,
                            'message': f'WATCH: Elevated {category} symptoms detected',
                            'current_rate': round(current_rate, 1),
                            'baseline_rate': round(baseline_rate, 1),
                            'action_required': 'Monitor closely'
                        })
        
        spatial_alerts = self._check_spatial_clustering(recent_reports)
        alerts.extend(spatial_alerts)
        
        return {
            'status': 'analyzed',
            'total_reports': total_reports,
            'symptom_rates': rates,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat(),
            'requires_action': len([a for a in alerts if a['level'] in ['emergency', 'warning']]) > 0
        }
    
    def _check_spatial_clustering(self, reports):
        """Check for geographic clustering of symptoms"""
        alerts = []
        location_counts = defaultdict(lambda: {'total': 0, 'symptoms': Counter()})
        
        for report in reports:
            location = report.get('location', 'unknown')
            if location != 'unknown':
                location_counts[location]['total'] += 1
                symptoms = report.get('symptoms', '').lower()
                for category, keywords in self.reportable_symptoms.items():
                    for keyword in keywords:
                        if keyword in symptoms:
                            location_counts[location]['symptoms'][category] += 1
                            break
        
        for location, data in location_counts.items():
            if data['total'] >= 5:
                for category, count in data['symptoms'].items():
                    if count >= 3:
                        alerts.append({
                            'level': 'warning',
                            'type': 'spatial_cluster',
                            'location': location,
                            'category': category,
                            'case_count': count,
                            'message': f'Cluster of {category} cases detected in {location}',
                            'action_required': 'Investigate local conditions'
                        })
        
        return alerts
    
    def predict_outbreak_risk(self, symptom_data, environmental_factors=None):
        """Predict outbreak risk based on current data"""
        risk_score = 0
        factors = []
        
        unique_symptoms = set()
        for report in symptom_data:
            symptoms = report.get('symptoms', '').lower()
            for category in self.reportable_symptoms.keys():
                if category in symptoms:
                    unique_symptoms.add(category)
        
        diversity_score = min(len(unique_symptoms) / 5, 1.0) * 30
        risk_score += diversity_score
        
        if len(symptom_data) > 20:
            risk_score += 20
        
        if environmental_factors:
            season = environmental_factors.get('season', '')
            if season in ['monsoon', 'flu_season']:
                risk_score += 15
                factors.append(f'{season} increases transmission risk')
        
        if risk_score >= 70:
            risk_level = 'HIGH'
            recommended_action = 'Activate emergency response protocol'
        elif risk_score >= 40:
            risk_level = 'MEDIUM'
            recommended_action = 'Increase surveillance and public awareness'
        else:
            risk_level = 'LOW'
            recommended_action = 'Continue routine monitoring'
        
        return {
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'contributing_factors': factors,
            'recommended_action': recommended_action,
            'monitoring_frequency': 'daily' if risk_score > 50 else 'weekly'
        }


outbreak_detector = OutbreakDetector()


def analyze_outbreak_risk(recent_reports):
    """Wrapper function for outbreak analysis"""
    if not recent_reports:
        return {
            'status': 'no_data',
            'message': 'Insufficient data for outbreak detection',
            'alerts': []
        }
    
    baseline = calculate_baseline(recent_reports)
    result = outbreak_detector.analyze_symptom_trends(recent_reports, baseline)
    prediction = outbreak_detector.predict_outbreak_risk(recent_reports)
    result['prediction'] = prediction
    
    return result


def calculate_baseline(reports):
    """Calculate baseline rates from historical data"""
    if len(reports) < 7:
        return None
    
    baseline = defaultdict(float)
    total = len(reports)
    
    for report in reports:
        symptoms = report.get('symptoms', '').lower()
        for category, keywords in outbreak_detector.reportable_symptoms.items():
            for keyword in keywords:
                if keyword in symptoms:
                    baseline[category] += 1
                    break
    
    for category in baseline:
        baseline[category] = (baseline[category] / total) * 100
    
    return baseline


# ========== HELPER FUNCTIONS ==========

def extract_symptoms_data(text):
    """Extract symptoms and measurements from text"""
    text_lower = text.lower()
    
    temp_patterns = [
        r'(\d{2,3}(?:\.\d+)?)\s*°?\s*c',
        r'(\d{2,3}(?:\.\d+)?)\s*(?:degree|degrees)',
        r'temperature\s*(?:is|of)?\s*(\d{2,3}(?:\.\d+)?)'
    ]
    
    temperature = None
    for pattern in temp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            temp = float(match.group(1))
            if 30 <= temp <= 45:
                temperature = temp
            break
    
    duration_patterns = [
        r'(\d+)\s*(?:day|days)',
        r'(\d+)\s*(?:week|weeks)',
        r'for\s*(\d+)\s*(?:day|days)'
    ]
    
    duration_days = 1
    for pattern in duration_patterns:
        match = re.search(pattern, text_lower)
        if match:
            duration_days = int(match.group(1))
            if 'week' in pattern:
                duration_days *= 7
            break
    
    return temperature, duration_days


def determine_triage_level(symptoms_text, temperature):
    """Determine triage level based on symptoms and temperature"""
    text = symptoms_text.lower()
    
    emergency_keywords = [
        'chest pain', 'difficulty breathing', 'shortness of breath',
        'severe bleeding', 'unconscious', 'stroke', 'heart attack',
        'cannot breathe', 'choking', 'severe allergic reaction',
        'suicidal', 'head injury', 'seizure'
    ]
    
    for keyword in emergency_keywords:
        if keyword in text:
            return {
                'level': 'emergency',
                'display': '🚨 EMERGENCY 🚨',
                'color': '#dc3545'
            }
    
    if temperature and temperature >= 39.5:
        return {
            'level': 'urgent',
            'display': '⚠️ URGENT ⚠️',
            'color': '#fd7e14'
        }
    
    urgent_keywords = ['fever', 'vomiting', 'diarrhea', 'dehydration', 'infection']
    urgent_count = sum(1 for kw in urgent_keywords if kw in text)
    
    if urgent_count >= 2 or (temperature and temperature > 39.0):
        return {
            'level': 'urgent',
            'display': '⚠️ URGENT ⚠️',
            'color': '#fd7e14'
        }
    
    return {
        'level': 'non_urgent',
        'display': '💚 Non-Urgent',
        'color': '#28a745'
    }


def get_medications_for_symptoms(symptoms_text):
    """Get relevant medications based on symptoms"""
    text = symptoms_text.lower()
    medications = []
    added_meds = set()
    
    for condition, meds in WHO_MEDICINES.items():
        if condition in text:
            for med in meds:
                if med['name'] not in added_meds:
                    medications.append(med)
                    added_meds.add(med['name'])
    
    return medications


def get_home_remedies(symptoms_text):
    """Get home remedies based on symptoms"""
    text = symptoms_text.lower()
    remedies = []
    
    for condition, remedy_list in HOME_REMEDIES.items():
        if condition in text:
            remedies.extend(remedy_list)
    
    return list(set(remedies))


def get_recommendation(triage_level, symptoms_text, temperature, duration):
    """Generate appropriate recommendation based on analysis"""
    if triage_level == 'emergency':
        return "⚠️ SEEK IMMEDIATE MEDICAL ATTENTION! Call emergency services or go to the nearest hospital immediately. Do not wait."
    
    recommendations = []
    
    if temperature:
        if temperature >= 39.0:
            recommendations.append(f"Your temperature is {temperature}°C. Monitor every 4 hours. Seek care if it rises above 39.5°C.")
        elif temperature >= 38.0:
            recommendations.append(f"Your temperature is {temperature}°C. Rest and stay hydrated.")
    
    if duration > 3:
        recommendations.append(f"Symptoms persisting for {duration} days. Consider consulting a healthcare provider if no improvement.")
    
    if triage_level == 'urgent':
        recommendations.append("Consult a healthcare provider within 24 hours.")
    else:
        recommendations.append("Rest, stay hydrated, and monitor symptoms. Consult a doctor if symptoms worsen or persist.")
    
    return " ".join(recommendations)


def get_warning_signs(symptoms_text, triage_level):
    """Get relevant warning signs based on symptoms"""
    warnings = []
    
    if triage_level == 'emergency':
        warnings.extend(WARNING_SIGNS['emergency'])
    
    text = symptoms_text.lower()
    if 'fever' in text:
        warnings.append("Fever above 39.5°C (103°F) requires medical attention")
    if 'headache' in text:
        warnings.append("Severe headache with stiff neck or confusion - seek immediate care")
    if 'cough' in text:
        warnings.append("Cough with bloody phlegm or difficulty breathing - urgent care needed")
    
    return list(set(warnings))


# ========== PUBLIC VIEW FUNCTIONS ==========

@csrf_exempt
@require_http_methods(["GET"])
def test_view(request):
    """Simple test endpoint"""
    return JsonResponse({
        'message': 'API is working!',
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    })


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
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        if len(username) < 3:
            return JsonResponse({'error': 'Username must be at least 3 characters'}, status=400)
        
        if len(password) < 6:
            return JsonResponse({'error': 'Password must be at least 6 characters'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        
        return JsonResponse({
            'success': True,
            'message': 'User created successfully',
            'username': username
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
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
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'success': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'username': user.username,
                'is_admin': user.is_staff or user.is_superuser
            })
        
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_view(request):
    """Symptom analysis endpoint with WHO medicines, disclaimers, and outbreak detection"""
    try:
        data = json.loads(request.body)
        symptoms_text = data.get('symptoms_text', '')
        temperature = data.get('temperature', 0)
        duration = data.get('duration_days', 1)
        location = data.get('location', '')  # Capture location for outbreak detection
        
        if temperature == 0 and symptoms_text:
            extracted_temp, extracted_duration = extract_symptoms_data(symptoms_text)
            if extracted_temp:
                temperature = extracted_temp
            if extracted_duration:
                duration = extracted_duration
        
        triage = determine_triage_level(symptoms_text, temperature)
        medications = get_medications_for_symptoms(symptoms_text)
        home_remedies = get_home_remedies(symptoms_text)
        warning_signs = get_warning_signs(symptoms_text, triage['level'])
        recommendation = get_recommendation(triage['level'], symptoms_text, temperature, duration)
        
        possible_condition = "General symptoms"
        if 'fever' in symptoms_text.lower() and 'cough' in symptoms_text.lower():
            possible_condition = "Possible respiratory infection"
        elif 'fever' in symptoms_text.lower() and 'headache' in symptoms_text.lower():
            possible_condition = "Possible viral infection"
        elif 'headache' in symptoms_text.lower():
            possible_condition = "Possible tension headache"
        elif 'diarrhea' in symptoms_text.lower():
            possible_condition = "Possible gastrointestinal issue"
        
        confidence = 0.85
        if medications:
            confidence = min(0.95, confidence + 0.05)
        if warning_signs:
            confidence = max(0.75, confidence - 0.05)
        
        # ========== OUTBREAK DETECTION INTEGRATION ==========
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        recent_reports = [
            {
                'symptoms': symptoms_text,
                'location': location,
                'timestamp': timezone.now().isoformat()
            }
        ]
        
        mock_reports = [
            {'symptoms': 'fever and cough', 'location': 'Accra', 'timestamp': '2026-04-05'},
            {'symptoms': 'headache and fever', 'location': 'Kumasi', 'timestamp': '2026-04-04'},
            {'symptoms': 'difficulty breathing', 'location': 'Accra', 'timestamp': '2026-04-03'},
            {'symptoms': 'chest pain', 'location': 'Takoradi', 'timestamp': '2026-04-02'},
        ]
        recent_reports.extend(mock_reports)
        
        outbreak_analysis = analyze_outbreak_risk(recent_reports)
        
        response_data = {
            'success': True,
            'triage_level': triage['level'],
            'triage_display': triage['display'],
            'possible_condition': possible_condition,
            'recommendation': recommendation,
            'confidence_score': round(confidence, 2),
            'temperature': temperature,
            'duration_days': duration,
            'medications': medications,
            'home_remedies': home_remedies,
            'warning_signs': warning_signs,
            'disclaimer': {
                'text': '⚠️ IMPORTANT: This is for informational purposes only. Always consult a healthcare professional before taking any medication. This is not a substitute for professional medical advice.',
                'emergency_contact': 'If you experience severe symptoms, difficulty breathing, or chest pain, seek immediate medical attention.',
                'who_reference': 'Medication recommendations based on WHO Essential Medicines List'
            },
            'when_to_seek_care': [
                'Symptoms worsen or become severe',
                'Fever persists for more than 3 days',
                'Difficulty breathing or chest pain',
                'Unable to keep liquids down',
                'Confusion or disorientation'
            ],
            'outbreak_detection': outbreak_analysis
        }
        
        if triage['level'] == 'emergency':
            response_data['emergency_action'] = 'Call emergency services immediately or go to the nearest hospital. Do not drive yourself.'
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def medications_view(request):
    """Get medications for a specific condition"""
    condition = request.GET.get('condition', '').lower()
    if condition:
        for cond, meds in WHO_MEDICINES.items():
            if condition in cond or cond in condition:
                return JsonResponse({
                    'success': True,
                    'condition': cond,
                    'medications': meds,
                    'source': 'WHO Essential Medicines List'
                })
    
    return JsonResponse({
        'success': True,
        'medicines': WHO_MEDICINES,
        'source': 'WHO Essential Medicines List'
    })


# ========== CHATBOT VIEW ==========

@csrf_exempt
@require_http_methods(["POST"])
def chatbot_view(request):
    """Chatbot endpoint for conversational health assistance"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message:
            return JsonResponse({'error': 'Message required'}, status=400)
        
        message_lower = message.lower()
        
        # Emergency detection
        emergency_keywords = ['chest pain', 'difficulty breathing', 'severe bleeding', 
                              'unconscious', 'heart attack', 'stroke', 'suicidal']
        for keyword in emergency_keywords:
            if keyword in message_lower:
                return JsonResponse({
                    'reply': "🚨 **EMERGENCY ALERT** 🚨\n\nPlease seek immediate medical attention!\nCall emergency services or go to the nearest hospital.\n\nDo not wait. This could be life-threatening.",
                    'is_emergency': True,
                    'requires_action': True
                })
        
        # Medicine information from WHO_MEDICINES
        for condition, medicines in WHO_MEDICINES.items():
            if condition in message_lower:
                response = f"📋 **{condition.capitalize()} Medications (WHO Essential List):**\n\n"
                for med in medicines:
                    response += f"💊 **{med['name']}**\n"
                    response += f"   Dosage: {med['dosage']}\n"
                    if 'max_daily' in med:
                        response += f"   Max Daily: {med['max_daily']}\n"
                    if 'indication' in med:
                        response += f"   For: {med['indication']}\n"
                    if 'warning' in med:
                        response += f"   ⚠️ {med['warning']}\n"
                    response += '\n'
                return JsonResponse({'reply': response, 'is_medical_info': True})
        
        # Symptom analysis request
        if len(message) > 30 or any(word in message_lower for word in ['symptom', 'sick', 'feel', 'pain']):
            return JsonResponse({
                'reply': "I can help analyze your symptoms. Please tell me:\n\n• What symptoms are you experiencing?\n• How long have you had them?\n• Do you have a fever? (if yes, what temperature?)\n\nI'll provide guidance based on WHO recommendations.",
                'requires_follow_up': True
            })
        
        # End conversation
        if any(word in message_lower for word in ['end', 'bye', 'goodbye', 'stop']):
            return JsonResponse({
                'reply': "🔚 **Conversation Ended** 🔚\n\nThank you for using the Health Assistant!\n\n📋 **Session Summary:**\n• Your health concerns have been noted\n• Always consult a doctor for persistent symptoms\n\n💡 **Next Steps:**\n• Type 'hello' to start a new conversation\n• Stay healthy and take care!\n\n🌟 Goodbye!",
                'is_end_message': True
            })
        
        # Default response
        return JsonResponse({
            'reply': "👋 I'm your health assistant. I can help with:\n\n• 💊 Medicine information (WHO Essential List)\n• 🤒 Symptom analysis\n• 🏥 When to seek medical care\n• 💡 Health advice\n\nWhat would you like to know?",
            'is_welcome': True
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def outbreak_status_view(request):
    """Get current outbreak status for dashboard"""
    try:
        recent_reports = [
            {'symptoms': 'fever and cough', 'location': 'Accra', 'timestamp': '2026-04-05'},
            {'symptoms': 'headache and fever', 'location': 'Kumasi', 'timestamp': '2026-04-04'},
            {'symptoms': 'difficulty breathing', 'location': 'Accra', 'timestamp': '2026-04-03'},
            {'symptoms': 'chest pain', 'location': 'Takoradi', 'timestamp': '2026-04-02'},
            {'symptoms': 'fever and headache', 'location': 'Accra', 'timestamp': '2026-04-01'},
            {'symptoms': 'cough and fever', 'location': 'Kumasi', 'timestamp': '2026-03-31'},
        ]
        
        analysis = analyze_outbreak_risk(recent_reports)
        
        return JsonResponse({
            'success': True,
            'data': analysis,
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== PHARMACY LOCATOR ==========

@csrf_exempt
@require_http_methods(["GET"])
def nearby_pharmacies_view(request):
    """Get nearby pharmacies based on user location"""
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius = request.GET.get('radius', 5000)
    
    if not lat or not lng:
        return JsonResponse({'error': 'Location parameters required'}, status=400)
    
    try:
        lat = float(lat)
        lng = float(lng)
        radius = int(radius)
    except ValueError:
        return JsonResponse({'error': 'Invalid location parameters'}, status=400)
    
    # Mock pharmacy data (you can integrate Google Places API later)
    pharmacies = [
        {
            'id': 'pharm_1',
            'name': 'Community Pharmacy',
            'address': '123 Main Street, Accra',
            'location': {'lat': lat + 0.01, 'lng': lng + 0.01},
            'rating': 4.5,
            'user_ratings_total': 120,
            'open_now': True,
            'photo_reference': ''
        },
        {
            'id': 'pharm_2',
            'name': 'HealthPlus Pharmacy',
            'address': '456 Market Road, Accra',
            'location': {'lat': lat - 0.008, 'lng': lng + 0.005},
            'rating': 4.2,
            'user_ratings_total': 89,
            'open_now': True,
            'photo_reference': ''
        },
        {
            'id': 'pharm_3',
            'name': 'MediCare Pharmacy',
            'address': '789 Hospital Avenue, Accra',
            'location': {'lat': lat + 0.005, 'lng': lng - 0.012},
            'rating': 4.8,
            'user_ratings_total': 200,
            'open_now': False,
            'photo_reference': ''
        },
    ]
    
    return JsonResponse({
        'success': True,
        'pharmacies': pharmacies,
        'count': len(pharmacies)
    })


# ========== TEST EMAIL VIEW (NEW - ADDED) ==========

@csrf_exempt
@require_http_methods(["POST"])
def send_test_email_notification(request):
    """Send a test email notification"""
    try:
        data = json.loads(request.body)
        to_email = data.get('email')
        subject = data.get('subject', 'Test Notification from Community Health Tracker')
        message = data.get('message', 'This is a test email to verify that email notifications are working correctly.\n\nIf you received this email, your notification system is configured properly!\n\n---\nCommunity Health Tracker\nYour personal health assistant')
        
        if not to_email:
            return JsonResponse({'error': 'Email address required'}, status=400)
        
        # Check if user is admin
        auth_header = request.headers.get('Authorization', '')
        is_admin = False
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                decoded_token = AccessToken(token)
                user_id = decoded_token['user_id']
                user = User.objects.get(id=user_id)
                is_admin = user.is_staff or user.is_superuser
            except (InvalidToken, User.DoesNotExist):
                pass
        
        if not is_admin:
            return JsonResponse({'error': 'Admin access required'}, status=403)
        
        # Send email using Django's mail system
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            return JsonResponse({
                'success': True,
                'message': f'Test email sent successfully to {to_email}'
            })
        except Exception as email_error:
            print(f"Email error: {email_error}")
            return JsonResponse({
                'success': False,
                'error': str(email_error)
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== PUSH NOTIFICATION API ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["POST"])
def subscribe_notifications(request):
    """Save push notification subscription"""
    try:
        data = json.loads(request.body)
        
        auth_header = request.headers.get('Authorization', '')
        user_id = None
        username = None
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                decoded_token = AccessToken(token)
                user_id = decoded_token['user_id']
                user = User.objects.get(id=user_id)
                username = user.username
            except (InvalidToken, User.DoesNotExist):
                pass
        
        subscription = {
            'endpoint': data.get('endpoint'),
            'keys': data.get('keys'),
            'user_id': user_id,
            'username': username,
            'created_at': datetime.now().isoformat()
        }
        
        existing = None
        for sub in push_subscriptions:
            if sub.get('endpoint') == subscription['endpoint']:
                existing = sub
                break
        
        if existing:
            existing.update(subscription)
            message = 'Subscription updated successfully'
        else:
            push_subscriptions.append(subscription)
            message = 'Subscription created successfully'
        
        print(f'Push subscription saved for user: {username or "anonymous"}')
        
        return JsonResponse({
            'success': True,
            'message': message,
            'subscription_count': len(push_subscriptions)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f'Error saving push subscription: {e}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def unsubscribe_notifications(request):
    """Remove push notification subscription"""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return JsonResponse({'error': 'Endpoint required'}, status=400)
        
        global push_subscriptions
        removed = False
        for i, sub in enumerate(push_subscriptions):
            if sub.get('endpoint') == endpoint:
                push_subscriptions.pop(i)
                removed = True
                break
        
        return JsonResponse({
            'success': True,
            'message': 'Unsubscribed successfully' if removed else 'Subscription not found'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_subscriptions(request):
    """Get all push subscriptions (admin only)"""
    auth_header = request.headers.get('Authorization', '')
    is_admin = False
    
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            decoded_token = AccessToken(token)
            user_id = decoded_token['user_id']
            user = User.objects.get(id=user_id)
            is_admin = user.is_staff or user.is_superuser
        except (InvalidToken, User.DoesNotExist):
            pass
    
    if not is_admin:
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    safe_subscriptions = []
    for sub in push_subscriptions:
        safe_subscriptions.append({
            'endpoint': sub.get('endpoint')[:50] + '...',
            'user_id': sub.get('user_id'),
            'username': sub.get('username'),
            'created_at': sub.get('created_at')
        })
    
    return JsonResponse({
        'success': True,
        'count': len(push_subscriptions),
        'subscriptions': safe_subscriptions
    })


@csrf_exempt
@require_http_methods(["POST"])
def send_test_notification(request):
    """Send a test push notification to all subscribers"""
    auth_header = request.headers.get('Authorization', '')
    is_admin = False
    
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            decoded_token = AccessToken(token)
            user_id = decoded_token['user_id']
            user = User.objects.get(id=user_id)
            is_admin = user.is_staff or user.is_superuser
        except (InvalidToken, User.DoesNotExist):
            pass
    
    if not is_admin:
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    data = json.loads(request.body)
    title = data.get('title', 'Test Notification')
    body = data.get('body', 'This is a test notification from Community Health Tracker')
    
    results = send_push_notification_to_all(title, body)
    
    return JsonResponse({
        'success': True,
        'message': f'Sent to {results["sent"]} subscribers, {results["failed"]} failed',
        'details': results
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_subscriptions_stats(request):
    """Get statistics about push subscriptions"""
    auth_header = request.headers.get('Authorization', '')
    is_admin = False
    
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            decoded_token = AccessToken(token)
            user_id = decoded_token['user_id']
            user = User.objects.get(id=user_id)
            is_admin = user.is_staff or user.is_superuser
        except (InvalidToken, User.DoesNotExist):
            pass
    
    if not is_admin:
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    user_subscriptions = {}
    for sub in push_subscriptions:
        username = sub.get('username', 'anonymous')
        user_subscriptions[username] = user_subscriptions.get(username, 0) + 1
    
    return JsonResponse({
        'success': True,
        'total_subscriptions': len(push_subscriptions),
        'unique_users': len(user_subscriptions),
        'by_user': user_subscriptions,
        'timestamp': datetime.now().isoformat()
    })


def send_push_notification_to_all(title, body, url='/'):
    """Send push notification to all subscribed users"""
    results = {
        'sent': 0,
        'failed': 0,
        'errors': []
    }
    
    for subscription in push_subscriptions:
        try:
            print(f'Sending push to: {subscription.get("endpoint")[:50]}...')
            results['sent'] += 1
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(str(e))
    
    return results


# ========== ADMIN ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["GET"])
def admin_users_view(request):
    """Get all users (admin only) - For Admin Dashboard"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                decoded_token = AccessToken(token)
                user_id = decoded_token['user_id']
                current_user = User.objects.get(id=user_id)
                if not current_user.is_staff:
                    return JsonResponse({'error': 'Admin access required'}, status=403)
            except (InvalidToken, User.DoesNotExist):
                pass
        
        users = []
        for user in User.objects.all():
            users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email or '',
                'date_joined': user.date_joined.strftime('%Y-%m-%d'),
                'report_count': 0,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            })
        return JsonResponse(users, safe=False)
    except Exception as e:
        users = [
            {'id': 1, 'username': 'Dotcom', 'email': 'adunorgbedzicharlesalmighty@gmail.com', 
             'date_joined': '2024-01-01', 'report_count': 5, 'is_staff': True, 'is_superuser': True},
        ]
        return JsonResponse(users, safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def admin_stats_view(request):
    """Get admin dashboard statistics"""
    try:
        total_users = User.objects.count()
    except:
        total_users = 1
    
    stats = {
        'total_users': total_users,
        'total_admins': 1,
        'emergency_cases': 12,
        'urgent_cases': 45,
        'non_urgent': 99,
        'daily_active_users': 34,
        'weekly_active_users': 156,
        'monthly_active_users': 423,
        'emergency_rate': 7.7,
        'avg_response_time': '24 min',
        'top_symptoms': [
            {'symptom': 'Fever', 'count': 78},
            {'symptom': 'Headache', 'count': 65},
            {'symptom': 'Cough', 'count': 52},
            {'symptom': 'Fatigue', 'count': 43},
            {'symptom': 'Sore Throat', 'count': 38}
        ],
        'recent_reports': [
            {'id': 1, 'date': '2024-04-06', 'symptoms': 'Fever and cough', 'triage': 'non_urgent'},
            {'id': 2, 'date': '2024-04-05', 'symptoms': 'Headache', 'triage': 'non_urgent'},
            {'id': 3, 'date': '2024-04-05', 'symptoms': 'Chest pain', 'triage': 'emergency'},
            {'id': 4, 'date': '2024-04-04', 'symptoms': 'High fever', 'triage': 'urgent'},
        ],
        'user_growth': {
            'last_7_days': 12,
            'last_30_days': 45,
            'total': total_users
        },
        'system_health': {
            'status': 'healthy',
            'uptime': '99.9%',
            'api_response_time': '120ms'
        }
    }
    
    return JsonResponse(stats)


@csrf_exempt
@require_http_methods(["GET"])
def admin_reports_view(request, triage_type):
    """Get reports filtered by triage type"""
    valid_types = ['emergency', 'urgent', 'non_urgent']
    
    if triage_type not in valid_types:
        return JsonResponse({'error': 'Invalid report type. Use: emergency, urgent, non_urgent'}, status=400)
    
    reports = MOCK_REPORTS.get(triage_type, [])
    
    return JsonResponse({
        'success': True,
        'type': triage_type,
        'count': len(reports),
        'reports': reports
    })


@csrf_exempt
@require_http_methods(["GET"])
def admin_user_detail_view(request, user_id):
    """Get detailed information for a specific user"""
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email or '',
                'date_joined': user.date_joined.strftime('%Y-%m-%d'),
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'report_count': 0
            }
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== AUTO-CREATE ADMIN USER ==========

def create_admin_user():
    """Create admin user if it doesn't exist"""
    admin_username = 'Dotcom'
    admin_email = 'adunorgbedzicharlesalmighty@gmail.com'
    admin_password = '0205038008@Dott'
    
    try:
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            print(f'✅ Admin user "{admin_username}" created successfully with email: {admin_email}')
        else:
            print(f'ℹ️ Admin user "{admin_username}" already exists')
    except Exception as e:
        print(f'⚠️ Could not create admin user: {e}')


@receiver(post_migrate)
def create_admin_on_migration(sender, **kwargs):
    """Create admin user after migrations"""
    create_admin_user()