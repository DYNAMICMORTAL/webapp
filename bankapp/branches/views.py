from django.shortcuts import render, redirect
from django.db import connection  # Connect to MySQL RDS
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
import pandas as pd
import os
from django.core.paginator import Paginator
from .graph_utils import get_transaction_statistics
from .neo4j_utils import Neo4jConnection, load_transaction_data, create_transaction_graph, get_neo4j_browser_url, generate_static_visualization, generate_standalone_visualization

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

def customers_page(request):
    return render(request, 'customers_page.html')

def logout_view(request):
    logout(request)
    return redirect('branch_login')

def transactions(request):
    # Path to the CSV file
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'branches', 'data', 'final_synthetic_transactions.csv')
    
    # Get customer ID from request or use default
    customer_id = int(request.GET.get('customer_id', 20917))
    
    try:
        # Read all transactions data
        df = pd.read_csv(csv_path)
        
        # Filter transactions for the specific customer
        filtered_df = df[df['customer_account_number'] == customer_id]
        all_transactions = filtered_df.to_dict('records')
        
        # Get transaction statistics
        stats = get_transaction_statistics(customer_id)
        
        # Pagination - 10 transactions per page for display
        page_number = request.GET.get('page', 1)
        paginator = Paginator(all_transactions, 10)
        page_obj = paginator.get_page(page_number)
        
        # Prepare chart data as JSON
        import json
        
        # Methods chart data
        methods_labels = list(stats.get('transaction_methods', {}).keys())
        methods_data = list(stats.get('transaction_methods', {}).values())
        
        # Status chart data
        status_data = [
            stats.get('normal_transactions', 0),
            stats.get('fraud_transactions', 0)
        ]
        
        chart_data = {
            'methods': {
                'labels': methods_labels,
                'data': methods_data
            },
            'status': {
                'data': status_data
            }
        }
        
        # Graph data statistics
        graph_data = {
            'statistics': {
                'total_transactions': len(all_transactions),
                'fraud_transactions': sum(1 for t in all_transactions if t.get('label_for_fraud') == 1),
                'normal_transactions': sum(1 for t in all_transactions if t.get('label_for_fraud') == 0)
            }
        }
        
        # Calculate fraud percentage
        if graph_data['statistics']['total_transactions'] > 0:
            graph_data['statistics']['fraud_percentage'] = (
                graph_data['statistics']['fraud_transactions'] / 
                graph_data['statistics']['total_transactions'] * 100
            )
        else:
            graph_data['statistics']['fraud_percentage'] = 0
        
        context = {
            'page_obj': page_obj,
            'total_transactions': len(all_transactions),
            'customer_id': customer_id,
            'graph_data': graph_data,
            'stats': stats,
            'chart_data_json': json.dumps(chart_data),
            'all_transactions_json': json.dumps(all_transactions)
        }
        
        return render(request, 'transactions.html', context)
    
    except Exception as e:
        return render(request, 'transactions.html', {'error': str(e)})