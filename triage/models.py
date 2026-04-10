from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    """Extended user profile model"""
    USER_ROLES = (
        ('patient', 'Patient'),
        ('health_worker', 'Health Worker'),
        ('admin', 'Administrator'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES, default='patient')
    phone_number = models.CharField(max_length=15, blank=True)
    region = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    age_group = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class SymptomLog(models.Model):
    """Store user symptom reports"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='symptom_logs')
    symptoms_text = models.TextField(help_text="User's description of symptoms")
    temperature = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(35.0), MaxValueValidator(42.0)]
    )
    duration_days = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(30)]
    )
    age_group = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional symptoms in structured format (optional)
    has_fever = models.BooleanField(default=False)
    has_cough = models.BooleanField(default=False)
    has_headache = models.BooleanField(default=False)
    has_fatigue = models.BooleanField(default=False)
    has_body_aches = models.BooleanField(default=False)
    has_sore_throat = models.BooleanField(default=False)
    has_difficulty_breathing = models.BooleanField(default=False)
    has_nausea = models.BooleanField(default=False)
    has_diarrhea = models.BooleanField(default=False)
    has_rash = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Symptom log by {self.user.username} on {self.created_at.date()}"

class TriageResult(models.Model):
    """Store AI triage results"""
    RECOMMENDATIONS = (
        ('home', 'Rest at Home'),
        ('clinic', 'Visit Clinic'),
        ('emergency', 'Emergency Care'),
    )
    
    symptom_log = models.OneToOneField(SymptomLog, on_delete=models.CASCADE, related_name='triage_result')
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATIONS)
    confidence_score = models.FloatField()
    possible_condition = models.CharField(max_length=200, blank=True)
    ai_analysis = models.TextField(blank=True, help_text="Detailed AI analysis")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Triage for {self.symptom_log.user.username}: {self.recommendation}"

class Medication(models.Model):
    """Medication knowledge base"""
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=100, blank=True)
    common_uses = models.TextField(help_text="Common conditions this medication is used for")
    description = models.TextField(blank=True)
    dosage_note = models.TextField(help_text="General dosage guidance")
    side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    is_over_the_counter = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class MedicationRecommendation(models.Model):
    """Link medications to symptoms/conditions"""
    triage_result = models.ForeignKey(TriageResult, on_delete=models.CASCADE, related_name='medication_recommendations')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, help_text="Specific notes for this recommendation")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['triage_result', 'medication']

class OutbreakAlert(models.Model):
    """Disease outbreak alerts"""
    ALERT_LEVELS = (
        ('info', 'Information'),
        ('watch', 'Watch'),
        ('warning', 'Warning'),
        ('emergency', 'Emergency'),
    )
    
    disease_name = models.CharField(max_length=200)
    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    alert_level = models.CharField(max_length=20, choices=ALERT_LEVELS)
    description = models.TextField()
    symptoms = models.TextField(blank=True)
    prevention_tips = models.TextField(blank=True)
    source = models.CharField(max_length=500, blank=True)
    date_reported = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_reported']
    
    def __str__(self):
        return f"{self.disease_name} - {self.region} ({self.alert_level})"

