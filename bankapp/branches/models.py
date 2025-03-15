from django.db import models

class Customer(models.Model):
    customer_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    state = models.CharField(max_length=100)
    account_type = models.CharField(max_length=50)
    balance_tier = models.CharField(max_length=50)
    credit_card_user = models.BooleanField(default=False)
    loan_status = models.CharField(max_length=50)
    relationship_tenure = models.CharField(max_length=50)

    def __str__(self):
        return self.name