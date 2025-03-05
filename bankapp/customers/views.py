from django.shortcuts import render, get_object_or_404
from .models import Customer

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
