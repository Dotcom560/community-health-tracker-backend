import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class OutbreakDetector:
    """Detects potential disease outbreaks using statistical analysis"""
    
    def __init__(self):
        # Threshold values for alert levels
        self.thresholds = {
            'emergency': 5.0,      # 5x normal rate
            'warning': 3.0,        # 3x normal rate
            'watch': 1.5           # 1.5x normal rate
        }
        
        # Symptoms that indicate reportable conditions
        self.reportable_symptoms = {
            'fever': ['fever', 'high temperature', 'pyrexia'],
            'respiratory': ['cough', 'difficulty breathing', 'shortness of breath'],
            'gastrointestinal': ['diarrhea', 'vomiting', 'nausea', 'stomach pain'],
            'neurological': ['headache', 'confusion', 'seizure'],
            'rash': ['rash', 'skin lesions', 'hives']
        }
    
    def analyze_symptom_trends(self, recent_reports, baseline_data=None):
        """
        Analyze symptom trends for outbreak detection
        
        Args:
            recent_reports: List of symptom reports from recent period
            baseline_data: Historical data for comparison
        
        Returns:
            dict: Outbreak analysis results
        """
        if not recent_reports:
            return {'status': 'insufficient_data', 'alerts': []}
        
        # Count symptom occurrences
        symptom_counts = defaultdict(int)
        for report in recent_reports:
            symptoms = report.get('symptoms', '').lower()
            for category, keywords in self.reportable_symptoms.items():
                for keyword in keywords:
                    if keyword in symptoms:
                        symptom_counts[category] += 1
                        break
        
        # Calculate rates
        total_reports = len(recent_reports)
        rates = {
            category: (count / total_reports) * 100 
            for category, count in symptom_counts.items()
        }
        
        # Compare with baseline (if available)
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
        
        # Check for spatial clustering (if location data available)
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
        
        # Group reports by location
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
        
        # Identify hotspots
        for location, data in location_counts.items():
            if data['total'] >= 5:  # Minimum threshold for investigation
                for category, count in data['symptoms'].items():
                    if count >= 3:  # Multiple cases of same symptom type
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
        """
        Predict outbreak risk based on current data
        
        Returns risk score and recommended actions
        """
        risk_score = 0
        factors = []
        
        # Factor 1: Symptom diversity
        unique_symptoms = set()
        for report in symptom_data:
            symptoms = report.get('symptoms', '').lower()
            for category in self.reportable_symptoms.keys():
                if category in symptoms:
                    unique_symptoms.add(category)
        
        diversity_score = min(len(unique_symptoms) / 5, 1.0) * 30
        risk_score += diversity_score
        
        # Factor 2: Report volume increase
        if len(symptom_data) > 20:
            risk_score += 20
        
        # Factor 3: Seasonal factors (if environmental data available)
        if environmental_factors:
            season = environmental_factors.get('season', '')
            if season == 'monsoon' or season == 'flu_season':
                risk_score += 15
                factors.append(f'{season} increases transmission risk')
        
        # Determine risk level
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

# Singleton instance
outbreak_detector = OutbreakDetector()


def analyze_outbreak_risk(recent_reports):
    """Wrapper function for outbreak analysis"""
    if not recent_reports:
        return {
            'status': 'no_data',
            'message': 'Insufficient data for outbreak detection',
            'alerts': []
        }
    
    # Get baseline data (last 30 days average)
    baseline = calculate_baseline(recent_reports)
    
    # Run detection
    result = outbreak_detector.analyze_symptom_trends(recent_reports, baseline)
    
    # Add prediction
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