import joblib
import numpy as np
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class TriageEngine:
    """
    AI-powered triage engine that loads and uses the trained model
    """
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.symptom_categories = {
            'emergency': ['chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious', 'severe injury'],
            'clinic': ['fever > 3 days', 'persistent vomiting', 'severe headache', 'dehydration'],
            'home': ['mild fever', 'runny nose', 'mild headache', 'fatigue', 'mild cough']
        }
        
        # Load the trained model
        self.load_model()
    
    def load_model(self):
        """Load the trained model from the ai-model folder"""
        try:
            # Path to your model file
            model_path = os.path.join(settings.BASE_DIR, '..', 'ai-model', 'models', 'triage_model.pkl')
            
            # If model exists, load it
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info(f"Model loaded successfully from {model_path}")
                
                # Extract vectorizer if it's a pipeline
                if hasattr(self.model, 'named_steps'):
                    self.vectorizer = self.model.named_steps.get('vectorizer')
                    self.classifier = self.model.named_steps.get('classifier')
                else:
                    logger.warning("Loaded model is not a pipeline with named_steps")
            else:
                logger.warning(f"Model not found at {model_path}. Using rule-based fallback.")
                self.model = None
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
    
    def preprocess_symptoms(self, symptoms_text):
        """Preprocess symptom text for the model"""
        if not symptoms_text:
            return ""
        
        # Basic preprocessing
        symptoms_text = symptoms_text.lower().strip()
        return symptoms_text
    
    def predict_with_model(self, symptoms_text):
        """Use the ML model to predict triage category"""
        if self.model is None:
            return None, None
        
        try:
            # Preprocess
            processed_text = self.preprocess_symptoms(symptoms_text)
            
            # Make prediction
            if hasattr(self.model, 'predict'):
                # For pipeline models
                prediction = self.model.predict([processed_text])[0]
                
                # Get probability if available
                if hasattr(self.model, 'predict_proba'):
                    probabilities = self.model.predict_proba([processed_text])[0]
                    confidence = float(max(probabilities))
                    
                    # Map prediction to recommendation
                    recommendation_map = {
                        0: 'emergency',
                        1: 'clinic',
                        2: 'home'
                    }
                    
                    # Try to get class from model
                    if hasattr(self.model, 'classes_'):
                        class_idx = list(self.model.classes_).index(prediction)
                        recommendation = recommendation_map.get(class_idx, 'clinic')
                    else:
                        # If prediction is already a string
                        if prediction in ['home', 'clinic', 'emergency']:
                            recommendation = prediction
                        else:
                            recommendation = 'clinic'
                    
                    return recommendation, confidence
                else:
                    # Without probabilities
                    if prediction in ['home', 'clinic', 'emergency']:
                        return prediction, 0.7
                    else:
                        return 'clinic', 0.5
            else:
                return None, None
                
        except Exception as e:
            logger.error(f"Error in model prediction: {str(e)}")
            return None, None
    
    def rule_based_triage(self, symptoms_text):
        """Fallback rule-based triage when model fails"""
        symptoms_lower = symptoms_text.lower()
        
        # Check for emergency symptoms
        for symptom in self.symptom_categories['emergency']:
            if symptom in symptoms_lower:
                return 'emergency', 0.8
        
        # Check for clinic symptoms
        for symptom in self.symptom_categories['clinic']:
            if symptom in symptoms_lower:
                return 'clinic', 0.7
        
        # Check for fever duration
        if 'fever' in symptoms_lower:
            # Try to extract duration
            import re
            duration_match = re.search(r'(\d+)\s*(day|days)', symptoms_lower)
            if duration_match:
                days = int(duration_match.group(1))
                if days > 3:
                    return 'clinic', 0.75
                else:
                    return 'home', 0.6
        
        # Default to home for mild symptoms
        return 'home', 0.5
    
    def analyze_symptoms(self, symptoms_text):
        """
        Main method to analyze symptoms and return triage result
        """
        if not symptoms_text:
            return {
                'recommendation': 'clinic',
                'confidence': 0.5,
                'possible_condition': 'Unknown',
                'analysis': 'No symptoms provided for analysis.',
                'method': 'error'
            }
        
        # Try model prediction first
        recommendation, confidence = self.predict_with_model(symptoms_text)
        
        method_used = 'ml_model'
        if recommendation is None:
            # Fallback to rule-based
            recommendation, confidence = self.rule_based_triage(symptoms_text)
            method_used = 'rule_based'
        
        # Determine possible condition (simplified)
        possible_condition = self.determine_condition(symptoms_text, recommendation)
        
        # Generate analysis text
        analysis = self.generate_analysis(symptoms_text, recommendation, possible_condition)
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'possible_condition': possible_condition,
            'analysis': analysis,
            'method': method_used
        }
    
    def determine_condition(self, symptoms_text, recommendation):
        """Determine possible condition based on symptoms"""
        symptoms_lower = symptoms_text.lower()
        
        condition_map = [
            ('malaria', ['fever', 'chills', 'sweating', 'headache', 'body ache']),
            ('common cold', ['runny nose', 'sneezing', 'sore throat', 'cough']),
            ('influenza', ['fever', 'cough', 'body ache', 'fatigue', 'headache']),
            ('covid-19', ['fever', 'cough', 'loss of taste', 'loss of smell', 'difficulty breathing']),
            ('typhoid', ['fever', 'headache', 'constipation', 'diarrhea', 'stomach pain']),
            ('gastroenteritis', ['diarrhea', 'vomiting', 'nausea', 'stomach pain']),
            ('allergy', ['sneezing', 'itchy eyes', 'runny nose', 'rash']),
            ('dehydration', ['thirst', 'dry mouth', 'dark urine', 'fatigue'])
        ]
        
        # Count matches for each condition
        best_match = None
        max_matches = 0
        
        for condition, keywords in condition_map:
            matches = sum(1 for keyword in keywords if keyword in symptoms_lower)
            if matches > max_matches:
                max_matches = matches
                best_match = condition
        
        if max_matches >= 2:
            return best_match.title()
        elif recommendation == 'emergency':
            return 'Potential Emergency Condition'
        else:
            return 'General Symptoms'
    
    def generate_analysis(self, symptoms, recommendation, condition):
        """Generate human-readable analysis"""
        analyses = {
            'home': f"Based on your symptoms ({symptoms[:100]}...), this appears to be a mild condition ({condition}). You can manage this at home with rest and over-the-counter medications.",
            'clinic': f"Your symptoms ({symptoms[:100]}...) suggest {condition} which may require medical attention. Please visit a clinic for proper diagnosis.",
            'emergency': f"Your symptoms ({symptoms[:100]}...) indicate a potentially serious condition ({condition}). Please seek emergency medical care immediately!"
        }
        
        return analyses.get(recommendation, "Please consult a healthcare provider for proper diagnosis.")