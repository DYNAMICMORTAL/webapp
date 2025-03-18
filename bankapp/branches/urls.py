from django.urls import path
from . import views

urlpatterns = [
    path('input/', views.branch_input, name='branch_input'),  # Branch input page
    path('transactions/', views.transactions, name='transactions'),  # Transactions page
    path('risk-scoring/', views.risk_scoring, name='risk_scoring'),  # Risk scoring page
    path('insider-threat/', views.insider_threat, name='insider_threat'),  # Insider threat page
    path('api/risk-assessment/', views.risk_assessment_api, name='risk_assessment_api'),  # Risk assessment API endpoint
    path('api/insider-threat/logs/', views.insider_threat_logs_api, name='insider_threat_logs_api'),  # Insider threat logs API
]
