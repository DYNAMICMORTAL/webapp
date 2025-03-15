from django.shortcuts import render, redirect
from django.db import connection  # Connect to MySQL RDS
from django.contrib import messages
from django.http import JsonResponse

def branch_login(request):
    BranchName = None
    if request.method == "POST":
        if "IFSC_CODE" in request.POST:
            # Fetch branch details
            IFSC_CODE = request.POST.get("IFSC_CODE")

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT BranchName FROM Branches WHERE IFSC_Code = %s",
                    [IFSC_CODE]
                )
                result = cursor.fetchone()

            if result:
                BranchName = result[0]  # Fetch branch name
                request.session['BranchName'] = BranchName
                request.session['IFSC_CODE'] = IFSC_CODE
            else:
                messages.error(request, "Invalid IFSC Code")
                return render(request, "branch_login.html")

    return render(request, "branch_login.html", {"BranchName": BranchName})

def employee_login(request):
    BranchName = request.session.get('BranchName')
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        password = request.POST.get("password")

        if employee_id == "ubi" and password == "ubi":
            request.session['user_role'] = 'employee'
            return redirect("/dashboard/")
        else:
            messages.error(request, "Invalid Employee Credentials")

    return render(request, "employee_login.html", {"BranchName": BranchName})

def compliance_login(request):
    BranchName = request.session.get('BranchName')
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        password = request.POST.get("password")

        if employee_id == "transactionteam" and password == "ubi":
            request.session['user_role'] = 'compliance'
            return redirect("/dashboard/")
        else:
            messages.error(request, "Invalid Compliance Team Credentials")

    return render(request, "compliance_login.html", {"BranchName": BranchName})

def dashboard(request):
    user_role = request.session.get('user_role')
    return render(request, 'dashboard.html', {'user_role': user_role})

def compliance_dashboard(request):
    return render(request, 'compliance_dashboard.html')

def fraud_detection(request):
    return render(request, 'fraud_detection.html')

def risk_scoring(request):
    return render(request, 'risk_scoring.html')

def pattern_analysis(request):
    return render(request, 'pattern_analysis.html')

def insider_threat(request):
    return render(request, 'insider_threat.html')

def reports(request):
    return render(request, 'reports.html')

def mail(request):
    return render(request, 'mail.html')

def crm(request):
    user_role = request.session.get('user_role')
    return render(request, 'crm.html', {'user_role': user_role})

from .queries import AGE_GROUP_QUERY, GEOGRAPHIC_QUERY, REGIONAL_STATE_QUERY, ACCOUNT_TYPE_QUERY, MULTI_PRODUCT_QUERY, BALANCE_TIERS_QUERY, CREDIT_CARD_USERS_QUERY, LOAN_PORTFOLIO_QUERY, CREDIT_CARD_PREFERENCES_QUERY, CREDIT_LIMIT_UTILIZATION_QUERY, CUSTOMER_LIFETIME_VALUE_QUERY, HIGH_NET_WORTH_INDIVIDUALS_QUERY, CROSS_SELLING_POTENTIAL_QUERY, LOAN_STATUS_PROFILE_QUERY, CREDIT_RISK_CATEGORIES_QUERY, RELATIONSHIP_TENURE_QUERY, BRANCH_RELATIONSHIP_QUERY, PRODUCT_ADOPTION_TIMELINE_QUERY, RFM_SEGMENTATION_QUERY

# Dictionary storing segmentation queries with subcategories
SEGMENTATION_QUERIES = {
    "Demographic": {
        "Age Group": AGE_GROUP_QUERY,
        "Geographic": GEOGRAPHIC_QUERY,
        "Regional (State)": REGIONAL_STATE_QUERY,
    },
    "Financial Behaviour": {
        "Account Type": ACCOUNT_TYPE_QUERY,
        "Multi-Product Relationship": MULTI_PRODUCT_QUERY,
        "Balance Tiers": BALANCE_TIERS_QUERY,
        "Credit Card Users vs Non-Users": CREDIT_CARD_USERS_QUERY,
    },
    "Relationship Value": {
        "Customer Lifetime Value": CUSTOMER_LIFETIME_VALUE_QUERY,
        "High Net Worth Individuals": HIGH_NET_WORTH_INDIVIDUALS_QUERY,
        "Cross-Selling Potential": CROSS_SELLING_POTENTIAL_QUERY,
    },
    "Product Usage": {
        "Loan Portfolio Analysis": LOAN_PORTFOLIO_QUERY,
        "Credit Card Preferences": CREDIT_CARD_PREFERENCES_QUERY,
        "Credit Limit Utilization": CREDIT_LIMIT_UTILIZATION_QUERY,
    },
    "Risk Profile": {
        "Loan Status Profile": LOAN_STATUS_PROFILE_QUERY,
        "Credit Risk Categories": CREDIT_RISK_CATEGORIES_QUERY,
    },
    "Customer Lifecycle": {
        "Relationship Tenure": RELATIONSHIP_TENURE_QUERY,
        "Branch Relationship Analysis": BRANCH_RELATIONSHIP_QUERY,
        "Product Adoption Timeline": PRODUCT_ADOPTION_TIMELINE_QUERY,
    },
    "RFM Segmentation": {
        "RFM Segmentation": RFM_SEGMENTATION_QUERY,
    },
}

def customer_experience(request):
    """Renders Compliance Portal Homepage with segmentation options"""
    return render(request, 'crm.html', {"segment_types": SEGMENTATION_QUERIES})

def get_subcategories(request, segment_type):
    """Returns available subcategories for a given segmentation type"""
    segment_data = SEGMENTATION_QUERIES.get(segment_type)
    
    if not segment_data:
        return JsonResponse({"error": "Invalid segmentation type"}, status=400)
    
    return JsonResponse({"segment": segment_type, "subcategories": list(segment_data.keys())})

def get_segmentation_data(request, segment_type, subcategory):
    """Executes SQL query for the selected subcategory"""
    segment_data = SEGMENTATION_QUERIES.get(segment_type, {})
    query = segment_data.get(subcategory)

    if not query:
        return JsonResponse({"error": "Invalid segmentation subcategory"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]  # Extract column names
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]  # Convert result into dictionary

    return JsonResponse({"segment": segment_type, "subcategory": subcategory, "data": data})