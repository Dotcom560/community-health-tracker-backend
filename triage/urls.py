# backend/triage/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('token/', views.token_view, name='token'),
    path('analyze/', views.analyze_view, name='analyze'),
]