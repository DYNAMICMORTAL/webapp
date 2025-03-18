"""
URL configuration for bankapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from branches.views import branch_login, employee_login, compliance_login, dashboard, fraud_detection, risk_scoring, pattern_analysis, insider_threat, reports, mail, crm, compliance_dashboard, customer_experience, get_subcategories, get_segmentation_data, customers_page  # Import the views
from branches.views import (
    branch_login, employee_login, compliance_login, dashboard,
    fraud_detection, risk_scoring, pattern_analysis, insider_threat,
    reports, mail, crm, compliance_dashboard, customer_experience,
    get_subcategories, get_segmentation_data, customers_page,
    logout_view, transactions, transaction_chat, risk_assessment_api,  # Add risk_assessment_api import
    insider_threat_logs_api  # Import the insider threat logs API
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('customers/', include('customers.urls')),
    path('', branch_login, name='home'),  # Set branch input page as home
    path('employee_login/', employee_login, name='employee_login'),  # Add URL pattern for employee login
    path('compliance_login/', compliance_login, name='compliance_login'),  # Add URL pattern for compliance login
    path('dashboard/', dashboard, name='dashboard'),  # Add URL pattern for dashboard
    path('fraud_detection/', fraud_detection, name='fraud_detection'),  # Add URL pattern for fraud detection
    path('risk_scoring/', risk_scoring, name='risk_scoring'),  # Add URL pattern for risk scoring
    path('pattern_analysis/', pattern_analysis, name='pattern_analysis'),  # Add URL pattern for pattern analysis
    path('insider_threat/', insider_threat, name='insider_threat'),  # Add URL pattern for insider threat
    path('reports/', reports, name='reports'),  # Add URL pattern for reports
    path('mail/', mail, name='mail'),  # Add URL pattern for mail
    path('crm/', crm, name='crm'),  # Add URL pattern for CRM
    path('compliance_dashboard/', compliance_dashboard, name='compliance_dashboard'),  # Add URL pattern for compliance dashboard
    path('customer_experience/', customer_experience, name='customer_experience'),  # Add URL pattern for customer experience
    path('crm/segmentation/<str:segment_type>/', get_subcategories, name='get_subcategories'),  # Add URL pattern for subcategories
    path('customer-experience/segmentation/<str:segment_type>/<str:subcategory>/', get_segmentation_data, name='get_segmentation_data'),  # Add URL pattern for segmentation data
    path('customers_page/', customers_page, name='customers_page'),  # Add URL pattern for CustomersPage
    path('customers/search/', include('customers.urls')),  # Add URL pattern for customer search
    path('logout/', logout_view, name='logout'),
    path('transactions/', transactions, name='transactions'),  # Add URL pattern for transactions
    path('transaction_chat/', transaction_chat, name='transaction_chat'),  # Add URL pattern for transaction chat
    path('api/risk-assessment/', risk_assessment_api, name='risk_assessment_api'),  # Add URL pattern for risk assessment API
    path('api/insider-threat/logs/', insider_threat_logs_api, name='insider_threat_logs_api'),  # Add URL pattern for insider threat logs API
]
