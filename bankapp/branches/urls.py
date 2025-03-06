from django.urls import path
from . import views

urlpatterns = [
    path('input/', views.branch_input, name='branch_input'),  # Branch input page
]
