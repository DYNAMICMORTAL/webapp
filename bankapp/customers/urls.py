from django.urls import path
from .views import search_customer, customer_detail

urlpatterns = [
    path('search/', search_customer, name='search_customer'),
    path('customer/<int:customer_id>/', customer_detail, name='customer_detail'),
]
