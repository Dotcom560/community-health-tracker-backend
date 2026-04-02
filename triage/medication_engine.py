import logging
from .models import Medication, MedicationRecommendation

logger = logging.getLogger(__name__)

class MedicationEngine:
    """
    Engine to recommend medications based on symptoms and triage results
    """
    
    def __init__(self):
        self.symptom_medication_map = {
            'fever': ['Paracetamol', 'Ibuprofen'],
            'headache': ['Paracetamol', 'Ibuprofen'],
            'cough': ['Dextromethorphan', 'Guaifenesin', 'Honey-based cough syrup'],
            'runny nose': ['Cetirizine', 'Loratadine', 'Diphenhydramine'],
            'sore throat': ['Throat lozenges', 'Salt water gargle', 'Ibuprofen'],
            'body ache': ['Ibuprofen', 'Paracetamol'],
            'diarrhea': ['Oral Rehydration Salts', 'Loperamide'],
            'nausea': ['Ginger', 'Dimenhydrinate'],
            'allergy': ['Cetirizine', 'Loratadine', 'Fexofenadine'],
            'rash': ['Hydrocortisone cream', 'Calamine lotion', 'Cetirizine'],
            'dehydration': ['Oral Rehydration Salts', 'Electrolyte solutions'],
            'indigestion': ['Antacids', 'Calcium carbonate'],
        }
        
        self.condition_medication_map = {
            'Malaria': ['Artemisinin-based combination therapy', 'Paracetamol for fever'],
            'Common Cold': ['Paracetamol', 'Decongestants', 'Cough syrup'],
            'Influenza': ['Paracetamol', 'Ibuprofen', 'Cough suppressants'],
            'Allergy': ['Cetirizine', 'Loratadine', 'Antihistamine eye drops'],
            'Gastroenteritis': ['Oral Rehydration Salts', 'Anti-diarrheal medication'],
            'Dehydration': ['Oral Rehydration Salts', 'Electrolyte solutions'],
        }
    
    def get_medications_for_symptoms(self, symptoms_text, possible_condition=None):
        """
        Recommend medications based on symptoms and possible condition
        """
        symptoms_lower = symptoms_text.lower()
        recommended_medications = []
        
        # Check for specific condition first
        if possible_condition and possible_condition in self.condition_medication_map:
            for med in self.condition_medication_map[possible_condition]:
                recommended_medications.append({
                    'name': med,
                    'reason': f"Recommended for {possible_condition}",
                    'type': 'condition_based'
                })
        
        # Check for individual symptoms
        for symptom, meds in self.symptom_medication_map.items():
            if symptom in symptoms_lower:
                for med in meds:
                    # Avoid duplicates
                    if not any(r['name'] == med for r in recommended_medications):
                        recommended_medications.append({
                            'name': med,
                            'reason': f"Helps with {symptom}",
                            'type': 'symptom_based'
                        })
        
        # If no medications found, suggest general
        if not recommended_medications:
            recommended_medications.append({
                'name': 'Consult healthcare provider',
                'reason': 'For proper diagnosis and treatment',
                'type': 'general_advice'
            })
        
        # Limit to top 5
        return recommended_medications[:5]
    
    def get_detailed_medication_info(self, medication_name):
        """
        Get detailed information about a specific medication
        """
        try:
            # Try to get from database first
            medication = Medication.objects.filter(name__icontains=medication_name).first()
            if medication:
                return {
                    'name': medication.name,
                    'generic_name': medication.generic_name,
                    'category': medication.category,
                    'common_uses': medication.common_uses,
                    'dosage_note': medication.dosage_note,
                    'side_effects': medication.side_effects,
                    'contraindications': medication.contraindications,
                    'is_over_the_counter': medication.is_over_the_counter,
                }
        except Exception as e:
            logger.error(f"Error fetching medication from DB: {str(e)}")
        
        # Return basic info if not in database
        return {
            'name': medication_name,
            'generic_name': '',
            'category': 'General',
            'common_uses': 'Varies based on condition',
            'dosage_note': 'Follow package instructions or healthcare provider advice',
            'side_effects': 'May vary',
            'contraindications': 'Consult healthcare provider',
            'is_over_the_counter': True,
        }
    
    def format_medication_response(self, medications, triage_result):
        """
        Format medication recommendations for API response
        """
        disclaimer = "IMPORTANT: These suggestions are for informational purposes only. Always consult a qualified healthcare professional before taking any medication."
        
        formatted_meds = []
        for med in medications:
            detailed_info = self.get_detailed_medication_info(med['name'])
            formatted_meds.append({
                **med,
                **detailed_info
            })
        
        return {
            'disclaimer': disclaimer,
            'triage_recommendation': triage_result.recommendation if triage_result else 'unknown',
            'medications': formatted_meds,
            'note': 'This is not a prescription. Please consult a healthcare provider.'
        }