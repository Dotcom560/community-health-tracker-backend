from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('test/', views.test_view, name='test'),
    path('register/', views.register_view, name='register'),
    path('token/', views.token_view, name='token'),
    path('analyze/', views.analyze_view, name='analyze'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('medications/', views.medications_view, name='medications'),
    path('pharmacies/nearby/', views.nearby_pharmacies_view, name='nearby_pharmacies'),
    
    # Outbreak detection endpoint
    path('outbreak/status/', views.outbreak_status_view, name='outbreak_status'),
    
    # ========== PUSH NOTIFICATION ENDPOINTS ==========
    path('notifications/subscribe/', views.subscribe_notifications, name='subscribe_notifications'),
    path('notifications/unsubscribe/', views.unsubscribe_notifications, name='unsubscribe_notifications'),
    path('notifications/test/', views.send_test_notification, name='send_test_notification'),
    path('notifications/stats/', views.get_subscriptions_stats, name='get_subscriptions_stats'),
    
    # Admin endpoints
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/stats/', views.admin_stats_view, name='admin_stats'),
    path('admin/reports/<str:triage_type>/', views.admin_reports_view, name='admin_reports'),
    path('admin/users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
]