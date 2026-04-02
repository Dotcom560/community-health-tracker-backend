from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_user, name='register'),
    path('profile/', views.get_user_profile, name='profile'),
    
    # Symptom analysis
    path('analyze/', views.analyze_symptoms, name='analyze'),
    path('history/', views.get_user_history, name='history'),
    
    # Public data
    path('outbreaks/', views.get_outbreak_alerts, name='outbreaks'),
    path('medications/', views.get_medications, name='medications'),
    
    # Analytics (protected)
    path('analytics/', views.get_analytics, name='analytics'),
]