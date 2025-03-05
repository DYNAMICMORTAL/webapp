from django.contrib import admin
from .models import Customer, Branch, Account, Loan, CreditCard

admin.site.register(Customer)
admin.site.register(Branch)
admin.site.register(Account)
admin.site.register(Loan)
admin.site.register(CreditCard)
