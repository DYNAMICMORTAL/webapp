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
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .transaction_chat import TransactionChatAssistant

# Import risk profiling modules
try:
    from .risk_profiling.agents.risk_assessment_agent import RiskAssessmentAgent
    from .risk_profiling.agents.kyc_agent import KYCAgent
    from .risk_profiling.utils.data_processor import load_sample_data
except ImportError:
    # Fallback imports if the relative import fails
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'branches', 'risk_profiling'))
    from agents.risk_assessment_agent import RiskAssessmentAgent
    from agents.kyc_agent import KYCAgent
    from utils.data_processor import load_sample_data

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
    # Path to the transactions CSV file
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'transactions_with_risk.csv')
    
    try:
        # Read the CSV file into a DataFrame
        transactions_df = pd.read_csv(csv_path)
        
        # Convert to list of dictionaries for template rendering
        transactions = transactions_df.to_dict('records')
        
        # For each transaction, determine the status based on risk score
        for transaction in transactions:
            risk_score = transaction.get('risk_score', 0)
            if risk_score < 30:
                transaction['status'] = 'Validated'
                transaction['status_class'] = 'bg-green-100 text-green-800'
            elif risk_score < 70:
                transaction['status'] = 'Under Review'
                transaction['status_class'] = 'bg-yellow-100 text-yellow-800'
            else:
                transaction['status'] = 'Frozen'
                transaction['status_class'] = 'bg-red-100 text-red-800'
                
            # Format the timestamp to a more readable format
            try:
                transaction['formatted_date'] = pd.to_datetime(transaction['timestamp']).strftime('%b %d, %Y')
                # Calculate time ago for display
                time_diff = pd.Timestamp.now() - pd.to_datetime(transaction['timestamp'])
                if time_diff.days > 0:
                    transaction['time_ago'] = f"{time_diff.days}d ago"
                else:
                    hours = time_diff.seconds // 3600
                    if hours > 0:
                        transaction['time_ago'] = f"{hours}h ago"
                    else:
                        minutes = time_diff.seconds // 60
                        transaction['time_ago'] = f"{minutes}m ago"
            except:
                transaction['formatted_date'] = 'N/A'
                transaction['time_ago'] = 'N/A'
                
            # Format the amount for better display
            try:
                transaction['formatted_amount'] = f"${float(transaction['transaction_amount']):,.2f}"
            except:
                transaction['formatted_amount'] = 'N/A'
        
        # Calculate stats for the cards
        high_risk_count = sum(1 for t in transactions if t.get('risk_score', 0) >= 70)
        avg_risk_score = sum(t.get('risk_score', 0) for t in transactions) / len(transactions) if transactions else 0
        pattern_anomalies = sum(1 for t in transactions if t.get('smurfing_indicator', 0) == 1)
        insider_threats = sum(1 for t in transactions if t.get('previous_fraud_flag', 0) == 1)
        
        # Prepare context for template
        context = {
            'transactions': transactions,
            'high_risk_count': high_risk_count,
            'avg_risk_score': round(avg_risk_score, 1),
            'pattern_anomalies': pattern_anomalies,
            'insider_threats': insider_threats,
            'total_transactions': len(transactions)
        }
        
        return render(request, 'compliance_dashboard.html', context)
    except Exception as e:
        # If there's an error, pass the error message to the template
        return render(request, 'compliance_dashboard.html', {'error': str(e)})

def fraud_detection(request):
    return render(request, 'fraud_detection.html')

def risk_scoring(request):
    """
    Render the risk scoring template
    """
    return render(request, 'risk_scoring.html')

def pattern_analysis(request):
    return render(request, 'pattern_analysis.html')

def insider_threat(request):
    return render(request, 'insider_threat.html')

def reports(request):
    return render(request, 'reports.html')

def mail(request):
    return render(request, 'mail.html', {"segment_types": SEGMENTATION_QUERIES})

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

@csrf_exempt
@require_POST
def transaction_chat(request):
    """
    API endpoint to process transaction-related queries using Gemini LLM.
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        query = data.get('query')
        customer_id = data.get('customer_id')
        
        if not query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        if not customer_id:
            return JsonResponse({'error': 'Customer ID is required'}, status=400)
        
        # Convert customer_id to integer if it's a string
        try:
            customer_id_int = int(customer_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid customer ID format'}, status=400)
        
        # Read all transaction data
        transactions_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'branches', 'data', 'final_synthetic_transactions.csv')
        
        if not os.path.exists(transactions_file):
            return JsonResponse({'error': f'Transaction data file not found: {transactions_file}'}, status=500)
        
        try:
            transactions_df = pd.read_csv(transactions_file)
        except Exception as e:
            print(f"Error reading CSV: {str(e)}")
            return JsonResponse({'error': f'Error reading transactions: {str(e)}'}, status=500)
        
        # First try to match on customer_account_number
        customer_transactions = transactions_df[transactions_df['customer_account_number'] == customer_id_int]
        
        # If no results, try matching on customer_id
        if len(customer_transactions) == 0:
            customer_transactions = transactions_df[transactions_df['customer_id'] == customer_id_int]
        
        # Convert to list of dictionaries for processing
        transactions_data = customer_transactions.to_dict('records')
        
        if not transactions_data:
            return JsonResponse({'response': f"I couldn't find any transaction data for customer ID {customer_id}. Please check the customer ID and try again."})
        
        # Initialize chat assistant and generate response
        try:
            chat_assistant = TransactionChatAssistant()
            response = chat_assistant.generate_response(query, transactions_data, customer_id)
            return JsonResponse({'response': response})
        except ValueError as e:
            # Handle missing API key
            print(f"Gemini API key error: {str(e)}")
            return JsonResponse({
                'response': "I'm unable to analyze your data right now because the AI service is not properly configured. Please contact technical support to set up the required API key."
            })
        except Exception as e:
            # Handle other errors with the chat assistant
            print(f"Chat assistant error: {str(e)}")
            return JsonResponse({
                'response': f"I encountered an error while analyzing your transaction data. Please try again later. (Error: {str(e)})"
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request'}, status=400)
    except Exception as e:
        print(f"Unexpected error in transaction_chat: {str(e)}")
        return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)

@csrf_exempt
@require_POST
def risk_assessment_api(request):
    """
    API endpoint to process risk assessment for a customer
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        
        if not customer_id:
            return JsonResponse({'error': 'Customer ID is required'}, status=400)
        
        # Initialize risk assessment agents
        risk_agent = RiskAssessmentAgent()
        kyc_agent = KYCAgent()
        
        # Get customer transaction data
        # Try multiple possible paths for the transaction data file
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       'branches', 'risk_profiling', 'final_synthetic_transactions.csv'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                       'risk_profiling', 'final_synthetic_transactions.csv'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                       'data', 'final_synthetic_transactions.csv')
        ]
        
        transactions_file = None
        for path in possible_paths:
            if os.path.exists(path):
                transactions_file = path
                break
        
        if not transactions_file:
            return JsonResponse({
                'error': 'Transaction data file not found. Tried: ' + ', '.join(possible_paths)
            }, status=500)
        
        # Load and filter transaction data
        transactions_df = pd.read_csv(transactions_file)
        
        # Try to match on customer_account_number
        customer_transactions = transactions_df[transactions_df['customer_account_number'] == int(customer_id)]
        
        # If no results, try matching on customer_id
        if len(customer_transactions) == 0:
            customer_transactions = transactions_df[transactions_df['customer_id'] == int(customer_id)]
        
        if len(customer_transactions) == 0:
            return JsonResponse({
                'error': f'No transaction data found for customer ID {customer_id}'
            }, status=404)
            
        # Get the most recent transaction 
        latest_transaction = customer_transactions.iloc[-1]
        
        # Convert to dictionary
        if hasattr(latest_transaction, 'to_dict'):
            transaction_dict = latest_transaction.to_dict()
        else:
            # If it's already a dictionary, use it directly
            transaction_dict = latest_transaction
        
        # Print out transaction data for debugging
        print(f"Transaction data: {json.dumps(transaction_dict, default=str)[:200]}...")
        
        # Process KYC profile assessment
        try:
            profile_assessment = kyc_agent.analyze_customer_profile(customer_id)
            print(f"Profile assessment completed: {profile_assessment is not None}")
        except Exception as e:
            print(f"Error in KYC profile assessment: {str(e)}")
            profile_assessment = {"profile_risk": {"risk_score": 50}}
        
        # Process transaction risk assessment
        try:
            # Make sure we're passing a dict, not a pandas Series
            transaction_assessment = risk_agent.assess_risk(transaction_dict)
            print(f"Transaction assessment completed: {transaction_assessment is not None}")
        except Exception as e:
            print(f"Error in transaction risk assessment: {str(e)}")
            transaction_assessment = {"risk_score": 50, "risk_category": "Medium", "risk_factors": ["Unable to process detailed risk factors"]}
        
        # Calculate combined risk (profile + transaction)
        try:
            combined_risk = risk_agent.assess_combined_risk(profile_assessment.get('profile_risk', {}), transaction_assessment)
        except Exception as e:
            print(f"Error in combined risk calculation: {str(e)}")
            # Use transaction assessment as fallback
            combined_risk = transaction_assessment
        
        # Prepare risk factors for display
        risk_factors = []
        if combined_risk and 'risk_factors' in combined_risk:
            risk_factors = combined_risk['risk_factors']
        
        # Format response for UI
        response = {
            'success': True,
            'customer_id': customer_id,
            'risk_score': combined_risk.get('risk_score', 0),
            'risk_category': combined_risk.get('risk_category', 'Unknown'),
            'risk_factors': risk_factors,
            'explanation': combined_risk.get('explanation', 'No detailed explanation available'),
            'total_transactions': len(customer_transactions),
            'risky_transactions': len(customer_transactions[customer_transactions['label_for_fraud'] == 1])
        }
        
        return JsonResponse(response)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request'}, status=400)
    except Exception as e:
        print(f"Error in risk_assessment_api: {str(e)}")
        return JsonResponse({'error': f'Error processing risk assessment: {str(e)}'}, status=500)


def insider_threat(request):
    """
    Renders the insider threat detection template
    """
    return render(request, 'insider_threat.html')

@csrf_exempt
@require_POST
def insider_threat_logs_api(request):
    """
    API endpoint to process insider threat logs and get AI analysis
    """
    try:
        # Get logs directory path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, 'insider_threat', 'logs')
        
        print(f"Accessing logs directory: {logs_dir}")
        
        if not os.path.exists(logs_dir):
            print(f"ERROR: Directory not found: {logs_dir}")
            return JsonResponse({'success': False, 'error': f'Logs directory not found: {logs_dir}'}, status=404)
        
        # Try to import log processing functions
        try:
            from .insider_threat.process_logs import load_logs_from_directory, prepare_prompt_for_gemini, call_gemini_llm
            
            # Load logs data from directory
            logs_data = load_logs_from_directory(logs_dir)
            print(f"Loaded logs data: {list(logs_data.keys())}")
            
            # Check if we have log data
            if not logs_data:
                return JsonResponse({'success': False, 'error': 'No log files found or could not be loaded'}, status=404)
            
            # Check for GOOGLE_API_KEY environment variable before proceeding
            if 'GOOGLE_API_KEY' not in os.environ:
                # Use fallback preprocessing without Gemini
                print("WARNING: GOOGLE_API_KEY not found. Using basic log processing without AI analysis.")
                
                # Get log data
                insider_threats = logs_data.get('insider_threat_logs', [])
                activity_logs = logs_data.get('activity_logs', [])
                
                # Combine logs
                all_logs = []
                if insider_threats:
                    # Add severity and risk score placeholders if not present
                    for log in insider_threats:
                        if 'severity' not in log:
                            log['severity'] = 'Medium'  # Default severity
                        if 'risk_score' not in log:
                            log['risk_score'] = 50  # Default risk score
                    all_logs.extend(insider_threats)
                    
                if activity_logs:
                    # Add severity and risk score placeholders if not present
                    for log in activity_logs:
                        if 'severity' not in log:
                            log['severity'] = 'Medium'  # Default severity
                        if 'risk_score' not in log:
                            log['risk_score'] = 50  # Default risk score
                    all_logs.extend(activity_logs)
            else:
                # Prepare prompt for Gemini LLM
                prompt = prepare_prompt_for_gemini(logs_data)
                
                # Call Gemini LLM
                print("Calling Gemini LLM for analysis...")
                response_text = call_gemini_llm(prompt)
                
                # Parse the response from Gemini
                try:
                    # Gemini might return a list directly instead of {"alerts": [...]}
                    response_data = json.loads(response_text)
                    
                    # Check if response is a list (direct array of alerts)
                    if isinstance(response_data, list):
                        all_logs = response_data
                    else:
                        # Otherwise try to get the alerts property
                        all_logs = response_data.get('alerts', [])
                        
                    print(f"Successfully parsed Gemini response, found {len(all_logs)} alerts")
                except json.JSONDecodeError as e:
                    print(f"Error parsing Gemini response: {str(e)}")
                    print(f"Response preview: {response_text[:200]}...")
                    
                    # Fallback to original log data if response parsing fails
                    insider_threats = logs_data.get('insider_threat_logs', [])
                    activity_logs = logs_data.get('activity_logs', [])
                    
                    # Combine logs
                    all_logs = []
                    if insider_threats:
                        for log in insider_threats:
                            if 'severity' not in log:
                                log['severity'] = 'Medium'
                            if 'risk_score' not in log:
                                log['risk_score'] = 50
                            # Add AI analysis placeholder
                            log['analysis'] = "AI analysis not available"
                            log['recommended_actions'] = ["Enable API key for AI analysis"]
                        all_logs.extend(insider_threats)
                        
                    if activity_logs:
                        for log in activity_logs:
                            if 'severity' not in log:
                                log['severity'] = 'Medium'
                            if 'risk_score' not in log:
                                log['risk_score'] = 50
                            # Add AI analysis placeholder
                            log['analysis'] = "AI analysis not available"
                            log['recommended_actions'] = ["Enable API key for AI analysis"]
                        all_logs.extend(activity_logs)
                        
        except ImportError as e:
            print(f"Error importing process_logs module: {str(e)}")
            return JsonResponse({'success': False, 'error': f'Failed to import process_logs module: {str(e)}'}, status=500)
        except Exception as e:
            print(f"Error processing logs: {str(e)}")
            return JsonResponse({'success': False, 'error': f'Error processing logs: {str(e)}'}, status=500)
        
        # Sort logs by risk score
        all_logs.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        # Calculate stats
        total_alerts = len(all_logs)
        critical_alerts = sum(1 for log in all_logs if log.get('severity') == 'Critical')
        high_alerts = sum(1 for log in all_logs if log.get('severity') == 'High')
        medium_alerts = sum(1 for log in all_logs if log.get('severity') == 'Medium')
        low_alerts = sum(1 for log in all_logs if log.get('severity') == 'Low')
        
        # Calculate average risk score
        if all_logs:
            avg_risk_score = sum(log.get('risk_score', 0) for log in all_logs) / len(all_logs)
        else:
            avg_risk_score = 0
            
        # Prepare response
        response = {
            'success': True,
            'alerts': all_logs,
            'stats': {
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'high_alerts': high_alerts,
                'medium_alerts': medium_alerts,
                'low_alerts': low_alerts,
                'avg_risk_score': round(avg_risk_score, 1)
            }
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        print(f"ERROR in insider_threat_logs_api: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error processing request: {str(e)}'}, status=500)

