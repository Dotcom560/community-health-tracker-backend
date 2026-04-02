from django.core.management.base import BaseCommand
from triage.models import Medication, OutbreakAlert
from datetime import date, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Load initial medication and outbreak data'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Loading initial data...')
        
        # Load medications
        medications = [
            # Pain and Fever
            {
                'name': 'Paracetamol',
                'generic_name': 'Acetaminophen',
                'category': 'Pain Relief',
                'common_uses': 'Fever, headache, mild pain',
                'dosage_note': 'Adults: 500-1000mg every 4-6 hours (max 4000mg/day)',
                'side_effects': 'Generally well-tolerated; liver damage with overdose',
                'contraindications': 'Liver disease, alcohol abuse',
                'is_over_the_counter': True
            },
            {
                'name': 'Ibuprofen',
                'generic_name': 'Ibuprofen',
                'category': 'Anti-inflammatory',
                'common_uses': 'Fever, pain, inflammation, body aches',
                'dosage_note': 'Adults: 200-400mg every 6-8 hours with food',
                'side_effects': 'Stomach upset, heartburn',
                'contraindications': 'Stomach ulcers, kidney disease, pregnancy',
                'is_over_the_counter': True
            },
            
            # Cold and Allergy
            {
                'name': 'Cetirizine',
                'generic_name': 'Cetirizine Hydrochloride',
                'category': 'Antihistamine',
                'common_uses': 'Allergies, hay fever, hives',
                'dosage_note': 'Adults: 10mg once daily',
                'side_effects': 'Drowsiness, dry mouth',
                'contraindications': 'Kidney disease',
                'is_over_the_counter': True
            },
            {
                'name': 'Loratadine',
                'generic_name': 'Loratadine',
                'category': 'Antihistamine',
                'common_uses': 'Allergies, runny nose, sneezing',
                'dosage_note': 'Adults: 10mg once daily',
                'side_effects': 'Less drowsy than other antihistamines',
                'contraindications': 'Liver disease',
                'is_over_the_counter': True
            },
            
            # Cough
            {
                'name': 'Dextromethorphan',
                'generic_name': 'Dextromethorphan',
                'category': 'Cough Suppressant',
                'common_uses': 'Dry cough',
                'dosage_note': 'Adults: 10-20mg every 4 hours',
                'side_effects': 'Drowsiness, dizziness',
                'contraindications': 'Asthma, taking MAO inhibitors',
                'is_over_the_counter': True
            },
            {
                'name': 'Guaifenesin',
                'generic_name': 'Guaifenesin',
                'category': 'Expectorant',
                'common_uses': 'Chest congestion, productive cough',
                'dosage_note': 'Adults: 200-400mg every 4 hours',
                'side_effects': 'Nausea, vomiting',
                'contraindications': 'None significant',
                'is_over_the_counter': True
            },
            
            # Digestive
            {
                'name': 'Oral Rehydration Salts',
                'generic_name': 'ORS',
                'category': 'Rehydration',
                'common_uses': 'Diarrhea, vomiting, dehydration',
                'dosage_note': 'Mix with clean water as directed; sip frequently',
                'side_effects': 'None when used correctly',
                'contraindications': 'Severe dehydration requiring IV',
                'is_over_the_counter': True
            },
            {
                'name': 'Loperamide',
                'generic_name': 'Loperamide',
                'category': 'Anti-diarrheal',
                'common_uses': 'Diarrhea',
                'dosage_note': 'Adults: 4mg initially, then 2mg after each loose stool',
                'side_effects': 'Constipation, dizziness',
                'contraindications': 'Bloody diarrhea, high fever',
                'is_over_the_counter': True
            },
            
            # Topical
            {
                'name': 'Hydrocortisone Cream',
                'generic_name': 'Hydrocortisone',
                'category': 'Topical Steroid',
                'common_uses': 'Rash, itching, eczema',
                'dosage_note': 'Apply thin layer to affected area 1-2 times daily',
                'side_effects': 'Skin thinning with prolonged use',
                'contraindications': 'Infected skin, broken skin',
                'is_over_the_counter': True
            },
            {
                'name': 'Calamine Lotion',
                'generic_name': 'Calamine',
                'category': 'Topical',
                'common_uses': 'Itching, poison ivy, insect bites',
                'dosage_note': 'Apply to affected area as needed',
                'side_effects': 'Minor skin irritation',
                'contraindications': 'Broken skin',
                'is_over_the_counter': True
            },
        ]
        
        for med_data in medications:
            obj, created = Medication.objects.get_or_create(
                name=med_data['name'],
                defaults=med_data
            )
            if created:
                self.stdout.write(f'  Created medication: {med_data["name"]}')
            else:
                self.stdout.write(f'  Medication already exists: {med_data["name"]}')
        
        # Load outbreak alerts
        alerts = [
            {
                'disease_name': 'Malaria',
                'region': 'Northern Region',
                'alert_level': 'warning',
                'description': 'Increased malaria cases reported during rainy season',
                'symptoms': 'Fever, chills, headache, body aches',
                'prevention_tips': 'Use insecticide-treated bed nets, eliminate standing water',
                'date_reported': date.today() - timedelta(days=5),
                'is_active': True
            },
            {
                'disease_name': 'Influenza',
                'region': 'Greater Accra',
                'alert_level': 'watch',
                'description': 'Seasonal flu cases increasing',
                'symptoms': 'Fever, cough, sore throat, body aches',
                'prevention_tips': 'Wash hands frequently, avoid close contact with sick individuals',
                'date_reported': date.today() - timedelta(days=2),
                'is_active': True
            },
            {
                'disease_name': 'Cholera',
                'region': 'Central Region',
                'alert_level': 'info',
                'description': 'Few cases reported, practice good hygiene',
                'symptoms': 'Watery diarrhea, vomiting, dehydration',
                'prevention_tips': 'Drink safe water, wash hands with soap, cook food thoroughly',
                'date_reported': date.today() - timedelta(days=10),
                'is_active': True
            },
        ]
        
        for alert_data in alerts:
            obj, created = OutbreakAlert.objects.get_or_create(
                disease_name=alert_data['disease_name'],
                region=alert_data['region'],
                date_reported=alert_data['date_reported'],
                defaults=alert_data
            )
            if created:
                self.stdout.write(f'  Created outbreak alert: {alert_data["disease_name"]} in {alert_data["region"]}')
            else:
                self.stdout.write(f'  Outbreak alert already exists: {alert_data["disease_name"]}')
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded initial data'))