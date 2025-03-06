from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Customer
from .models import Branch

def search_customer(request):
    query = request.GET.get('q')
    print(f"Search query: {query}")  # Debug print
    if query:
        query_parts = query.strip().split()
        print(f"Query parts: {query_parts}")  # Debug print
        if len(query_parts) == 1:
            results = Customer.objects.filter(
                FirstName__icontains=query_parts[0]
            ) | Customer.objects.filter(
                LastName__icontains=query_parts[0]
            )
        else:
            results = Customer.objects.filter(
                FirstName__icontains=query_parts[0]
            ) & Customer.objects.filter(
                LastName__icontains=query_parts[1]
            )
        print(f"Results: {results}")  # Debug print
    else:
        results = []
    return render(request, 'search.html', {'results': results})

def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, CustomerID=customer_id)
    return render(request, 'customer_detail.html', {'customer': customer})

def landing_page(request):
    """ Renders the branch input landing page """
    return render(request, 'index.html')

def login_page(request):
    """ Handles branch number validation from AWS RDS """
    branch_number = request.GET.get('branch_number', '')

    # Fetch branch from AWS RDS MySQL
    try:
        branch = Branch.objects.get(IFSC_Code=branch_number)
        branch_name = branch.BranchName
    except Branch.DoesNotExist:
        return HttpResponse("Invalid Branch Number", status=400)

    return render(request, 'login.html', {'branch_name': branch_name})

def employee_search(request):
    """ Handles employee login and redirects to search """
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        password = request.POST.get('password')

        if employee_id == "ubi" and password == "ubi":
            return redirect('/customers/search/')  # Redirect to search page
        else:
            return HttpResponse("Invalid Credentials", status=401)

    return redirect('/')