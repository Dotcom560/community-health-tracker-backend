from django.contrib import admin
from .models import (
    UserProfile, SymptomLog, TriageResult, 
    Medication, MedicationRecommendation, OutbreakAlert
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'region', 'created_at']
    list_filter = ['role', 'region']
    search_fields = ['user__username', 'user__email']

@admin.register(SymptomLog)
class SymptomLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'temperature', 'duration_days']
    list_filter = ['created_at', 'has_fever', 'has_cough']
    search_fields = ['user__username', 'symptoms_text']
    readonly_fields = ['created_at']

@admin.register(TriageResult)
class TriageResultAdmin(admin.ModelAdmin):
    list_display = ['symptom_log', 'recommendation', 'confidence_score', 'created_at']
    list_filter = ['recommendation', 'created_at']
    search_fields = ['symptom_log__user__username']

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_over_the_counter']
    list_filter = ['category', 'is_over_the_counter']
    search_fields = ['name', 'generic_name']

@admin.register(MedicationRecommendation)
class MedicationRecommendationAdmin(admin.ModelAdmin):
    list_display = ['triage_result', 'medication', 'created_at']
    list_filter = ['created_at']

@admin.register(OutbreakAlert)
class OutbreakAlertAdmin(admin.ModelAdmin):
    list_display = ['disease_name', 'region', 'alert_level', 'date_reported', 'is_active']
    list_filter = ['alert_level', 'region', 'is_active']
    search_fields = ['disease_name', 'region']
