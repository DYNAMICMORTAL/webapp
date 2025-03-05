from django.shortcuts import render
from .models import Customer

def search_customer(request):
    query = request.GET.get('q')
    results = Customer.objects.filter(full_name__icontains=query) if query else []
    return render(request, 'search.html', {'results': results})
