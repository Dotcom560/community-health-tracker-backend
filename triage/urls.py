from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_view),
    path('register/', views.register_view),
    path('token/', views.token_view),
    path('analyze/', views.analyze_view),
]