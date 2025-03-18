from django.db import models

# ──────────────────────────────── Customers Table ────────────────────────────────
class Customer(models.Model):
    CustomerID = models.AutoField(primary_key=True)
    FirstName = models.CharField(max_length=50)
    LastName = models.CharField(max_length=50)
    Email = models.EmailField(unique=True)
    PhoneNumber = models.CharField(max_length=15, unique=True)
    Address = models.TextField()
    DateOfBirth = models.DateField()
    AadharNumber = models.CharField(max_length=12, unique=True)
    PANNumber = models.CharField(max_length=10, unique=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.FirstName} {self.LastName}"

    class Meta:
        db_table = 'Customers'

# ──────────────────────────────── Branches Table ────────────────────────────────
class Branch(models.Model):
    BranchID = models.AutoField(primary_key=True)
    IFSC_Code = models.CharField(max_length=20, unique=True, default="TEMP0000000")
    BranchName = models.CharField(max_length=255)
    Address = models.TextField()
    # City = models.CharField(max_length=100)
    City = models.CharField(max_length=100, default="Unknown")
    State = models.CharField(max_length=100, default="Unknown")

    def __str__(self):
        return f"{self.BranchName} ({self.IFSC_Code})"

# ──────────────────────────────── Accounts Table ────────────────────────────────
class Account(models.Model):
    ACCOUNT_TYPES = [
        ('Savings', 'Savings'),
        ('Current', 'Current'),
        ('Fixed Deposit', 'Fixed Deposit'),
        ('Recurring Deposit', 'Recurring Deposit')
    ]

    account_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    opened_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_type} - {self.customer.FirstName} {self.customer.LastName}"

# ──────────────────────────────── Transactions Table ────────────────────────────────
# class Transaction(models.Model):
#     TRANSACTION_TYPES = [
#         ('Deposit', 'Deposit'),
#         ('Withdrawal', 'Withdrawal'),
#         ('Transfer', 'Transfer'),
#         ('Bill Payment', 'Bill Payment')
#     ]

#     MODES = [
#         ('UPI', 'UPI'),
#         ('Card', 'Card'),
#         ('NEFT', 'NEFT'),
#         ('IMPS', 'IMPS'),
#         ('RTGS', 'RTGS')
#     ]

#     transaction_id = models.AutoField(primary_key=True)
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)
#     transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
#     mode_of_transaction = models.CharField(max_length=10, choices=MODES)
#     amount = models.DecimalField(max_digits=15, decimal_places=2)
#     transaction_date = models.DateTimeField(auto_now_add=True)
#     description = models.TextField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.transaction_type} - {self.amount} - {self.mode_of_transaction}"

# ──────────────────────────────── Loans Table ────────────────────────────────
class Loan(models.Model):
    LOAN_TYPES = [
        ('Home Loan', 'Home Loan'),
        ('Car Loan', 'Car Loan'),
        ('Education Loan', 'Education Loan'),
        ('Personal Loan', 'Personal Loan')
    ]

    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tenure_years = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.loan_type} - {self.customer.FirstName} {self.customer.LastName}"

# ──────────────────────────────── Credit Cards Table ────────────────────────────────
class CreditCard(models.Model):
    CARD_TYPES = [
        ('Visa', 'Visa'),
        ('MasterCard', 'MasterCard'),
        ('Amex', 'Amex'),
        ('Rupay', 'Rupay')
    ]

    card_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16, unique=True)
    card_type = models.CharField(max_length=15, choices=CARD_TYPES)
    expiry_date = models.DateField()
    cvv = models.IntegerField()
    credit_limit = models.IntegerField()  # Updated from Decimal to Integer

    def __str__(self):
        return f"{self.card_type} - {self.customer.FirstName} {self.customer.LastName}"

class EmployeeLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    employee_id = models.CharField(max_length=10)
    role = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    accessed_module = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    access_duration = models.IntegerField()
    affected_customer = models.CharField(max_length=50, blank=True, null=True)
    data_extracted = models.TextField(blank=True, null=True)
    transaction_details = models.TextField(blank=True, null=True)
    device = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    notes = models.TextField()
    risk_score = models.IntegerField()
    risk_level = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.employee_id} - {self.risk_level}"