from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@csrf_exempt
def analyze_symptoms(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symptoms = data.get('symptoms_text', '')
            
            # Simple rule-based analysis
            symptoms_lower = symptoms.lower()
            
            if 'chest pain' in symptoms_lower or 'difficulty breathing' in symptoms_lower:
                triage_level = 'emergency'
                triage_display = 'Emergency'
                recommendation = 'Seek immediate medical attention!'
            elif 'fever' in symptoms_lower and 'headache' in symptoms_lower:
                triage_level = 'urgent'
                triage_display = 'Urgent'
                recommendation = 'Consult a doctor within 24 hours.'
            else:
                triage_level = 'non_urgent'
                triage_display = 'Non-Urgent'
                recommendation = 'Rest and stay hydrated. Monitor symptoms.'
            
            return JsonResponse({
                'success': True,
                'triage_level': triage_level,
                'triage_display': triage_display,
                'possible_condition': 'General symptoms',
                'recommendation': recommendation,
                'confidence_score': 0.85,
                'medications': []
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)