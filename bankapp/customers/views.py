# from django.shortcuts import render, get_object_or_404
# from django.shortcuts import render, redirect
# from django.http import HttpResponse
# from .models import Customer
# from .models import Branch
# import logging
# from django.core.cache import cache
# from django.core.mail import send_mail
# from django.conf import settings
# from datetime import datetime, timedelta
# import logging
# logger = logging.getLogger(__name__)

# def test_log(request):
#     logger.info("This is a test log message.")
#     return HttpResponse("Check logs!")


# logger = logging.getLogger('django')

# SEARCH_LIMIT = 10  # Maximum allowed searches in TIME_WINDOW
# TIME_WINDOW = 5 * 60  # 5 minutes in seconds

# def search_customers(request):
#     if request.method == "GET":
#         employee_id = request.session.get('employee_id', 'Unknown')
#         query = request.GET.get('query', 'N/A')  # Capture search input
#         ip = request.META.get('REMOTE_ADDR')

#         logger.info(f"Employee ID: {employee_id} searched for: {query} from IP: {ip}")

#         current_time = datetime.now()

#         # Cache key for employee search tracking
#         cache_key = f"search_count_{employee_id}"

#         # Get current search count
#         search_data = cache.get(cache_key, {"count": 0, "first_search_time": current_time})

#         # Check time window
#         if (current_time - search_data["first_search_time"]).seconds > TIME_WINDOW:
#             # Reset the counter if time window has passed
#             search_data = {"count": 1, "first_search_time": current_time}
#         else:
#             # Otherwise, increment the count
#             search_data["count"] += 1

#         # Save back to cache
#         cache.set(cache_key, search_data, timeout=TIME_WINDOW)

#         # Log the search activity
#         logger.info(f"Employee ID: {employee_id} searched for: {query} from IP: {ip}. Total Searches in 5 min: {search_data['count']}")

#         # Trigger alert if search limit is exceeded
#         if search_data["count"] > SEARCH_LIMIT:
#             alert_message = f"🚨 ALERT: Employee ID {employee_id} at IP {ip} has searched for {search_data['count']} customers in 5 minutes! 🚨"
            
#             # Log alert
#             logger.warning(alert_message)

#             # Send email alert to security team
#             send_mail(
#                 subject="Insider Threat Alert - Unusual Search Activity",
#                 message=alert_message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=['mihiramin86@apsit.edu.in'],  # Change this to actual security email
#             )

#         # Proceed with your customer search logic
#         return render(request, 'customers/search.html')

# def search_customer(request):
#     query = request.GET.get('q')
#     print(f"Search query: {query}")  # Debug print
#     if query:
#         query_parts = query.strip().split()
#         print(f"Query parts: {query_parts}")  # Debug print
#         if len(query_parts) == 1:
#             results = Customer.objects.filter(
#                 FirstName__icontains=query_parts[0]
#             ) | Customer.objects.filter(
#                 LastName__icontains=query_parts[0]
#             )
#         else:
#             results = Customer.objects.filter(
#                 FirstName__icontains=query_parts[0]
#             ) & Customer.objects.filter(
#                 LastName__icontains=query_parts[1]
#             )
#         print(f"Results: {results}")  # Debug print
#     else:
#         results = []
#     return render(request, 'search.html', {'results': results})

# def customer_detail(request, customer_id):
#     customer = get_object_or_404(Customer, CustomerID=customer_id)
#     return render(request, 'customer_detail.html', {'customer': customer})

# def landing_page(request):
#     """ Renders the branch input landing page """
#     return render(request, 'index.html')

# def login_page(request):
#     """ Handles branch number validation from AWS RDS """
#     branch_number = request.GET.get('branch_number', '')

#     # Fetch branch from AWS RDS MySQL
#     try:
#         branch = Branch.objects.get(IFSC_Code=branch_number)
#         branch_name = branch.BranchName
#     except Branch.DoesNotExist:
#         return HttpResponse("Invalid Branch Number", status=400)

#     return render(request, 'login.html', {'branch_name': branch_name})

# def employee_search(request):
#     """ Handles employee login and redirects to search """
#     if request.method == 'POST':
#         employee_id = request.POST.get('employee_id')
#         password = request.POST.get('password')

#         if employee_id == "ubi" and password == "ubi":
#             return redirect('/customers/search/')  # Redirect to search page
#         else:
#             return HttpResponse("Invalid Credentials", status=401)

#     return redirect('/')




# webapp/bankapp/customers/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Customer, Branch
import logging
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

SEARCH_LIMIT = 10
TIME_WINDOW = 5 * 60

def test_log(request):
    logger.info("This is a test log message.")
    return HttpResponse("Check logs!")

def search_customers(request):
    employee_id = request.session.get('employee_id', 'Unknown')
    query = request.GET.get('query', 'N/A')
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    url = request.build_absolute_uri()
    http_method = request.method

    logger.info(
        "Customer Search: "
        f"Employee ID: {employee_id}, "
        f"Search Query: '{query}', "
        f"IP: {ip}, "
        f"URL: {url}, "
        f"Method: {http_method}, "
        f"User-Agent: {user_agent}"
    )

    current_time = datetime.now()
    cache_key = f"search_count_{employee_id}"
    search_data = cache.get(cache_key, {"count": 0, "first_search_time": current_time})

    if (current_time - search_data["first_search_time"]).seconds > TIME_WINDOW:
        search_data = {"count": 1, "first_search_time": current_time}
    else:
        search_data["count"] += 1

    cache.set(cache_key, search_data, timeout=TIME_WINDOW)

    logger.info(
        "Customer Search Activity: "
        f"Employee ID: {employee_id}, "
        f"Search Query: '{query}', "
        f"IP: {ip}. "
        f"Total Searches in 5 min: {search_data['count']}"
    )

    if search_data["count"] > SEARCH_LIMIT:
        alert_message = (
            "Insider Threat Alert: "
            f"Employee ID: {employee_id}, "
            f"IP: {ip}, "
            f"Searched {search_data['count']} times in 5 minutes."
        )
        logger.warning(alert_message)

        send_mail(
            subject="Insider Threat Alert - Unusual Search Activity",
            message=alert_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['mihiramin86@apsit.edu.in'],
        )

    return render(request, 'customers/search.html')

def search_customer(request):
    query = request.GET.get('q')
    if query:
        query_parts = query.strip().split()
        if len(query_parts) == 1:
            results = Customer.objects.filter(FirstName__icontains=query_parts[0]) | Customer.objects.filter(LastName__icontains=query_parts[0])
        else:
            results = Customer.objects.filter(FirstName__icontains=query_parts[0]) & Customer.objects.filter(LastName__icontains=query_parts[1])
    else:
        results = []
    return render(request, 'search.html', {'results': results})

def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, CustomerID=customer_id)
    return render(request, 'customer_detail.html', {'customer': customer})

def landing_page(request):
    return render(request, 'index.html')

def login_page(request):
    branch_number = request.GET.get('branch_number', '')
    try:
        branch = Branch.objects.get(IFSC_Code=branch_number)
        branch_name = branch.BranchName
    except Branch.DoesNotExist:
        return HttpResponse("Invalid Branch Number", status=400)
    return render(request, 'login.html', {'branch_name': branch_name})

def employee_search(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        password = request.POST.get('password')
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        url = request.build_absolute_uri()
        http_method = request.method

        if employee_id == "ubi" and password == "ubi":
            logger.info(f"Successful Login: Employee ID: {employee_id}, IP: {ip}, URL: {url}, Method: {http_method}, User-Agent: {user_agent}")
            return redirect('/customers/search/')
        else:
            logger.warning(f"Failed Login Attempt: Employee ID: {employee_id}, IP: {ip}, URL: {url}, Method: {http_method}, User-Agent: {user_agent}")
            return HttpResponse("Invalid Credentials", status=401)
    return redirect('/')