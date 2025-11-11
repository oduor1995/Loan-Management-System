# from django.db import models
# from django.contrib.auth.models import AbstractUser
# from django.conf import settings
# from django.db.models import Sum
# # Custom user model for lender-based access
# class Lender(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     address = models.TextField(blank=True, null=True)
#     contact_email = models.EmailField(blank=True, null=True)
#     contact_phone = models.CharField(max_length=20, blank=True, null=True)
#     license_number = models.CharField(max_length=100, blank=True, null=True, help_text="Lending license number")

#     def __str__(self):
#         return self.name

# class CustomUser(AbstractUser):
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='users', null=True, blank=True)

#     def __str__(self):
#         return self.username

# # Create your models here.

# class Borrower(models.Model):
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='borrowers')
#     user = models.OneToOneField('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='borrower_profile')
#     # Personal Info
#     full_name = models.CharField(max_length=255, null=True, blank=True)
#     gender = models.CharField(max_length=10, choices=[("Male", "Male"), ("Female", "Female")])
#     date_of_birth = models.DateField(null=True, blank=True)
#     phone = models.CharField(max_length=20)
#     email = models.EmailField(blank=True, null=True)
#     address = models.TextField(blank=True, null=True)

#     # Borrower Info
#     borrower_id = models.CharField(max_length=50, unique=True)
#     date_registered = models.DateField(auto_now_add=True)
#     credit_score = models.PositiveIntegerField(default=0, help_text="Credit score out of 1000")
#     employment_status = models.CharField(max_length=50, blank=True, null=True, choices=[
#         ('EMPLOYED', 'Employed'),
#         ('SELF_EMPLOYED', 'Self Employed'),
#         ('UNEMPLOYED', 'Unemployed'),
#         ('STUDENT', 'Student'),
#         ('RETIRED', 'Retired'),
#     ])
#     monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

#     # Loan History
#     total_loans_taken = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     total_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

#     def update_credit_score(self):
#         """Update borrower's credit score"""
#         self.credit_score = LoanCalculator.calculate_credit_score(self)
#         self.save(update_fields=['credit_score'])

#     # Notes
#     notes = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.full_name

# class LoanApplication(models.Model):
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='loan_applications')
#     borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE, related_name='loan_applications')

#     # Application Details
#     application_date = models.DateField(auto_now_add=True)
#     requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
#     purpose = models.TextField(blank=True, help_text="Purpose of the loan")
#     loan_term_months = models.PositiveIntegerField(help_text="Requested loan term in months")

#     # Application Status
#     STATUS_CHOICES = [
#         ('PENDING', 'Pending Review'),
#         ('APPROVED', 'Approved'),
#         ('REJECTED', 'Rejected'),
#         ('WITHDRAWN', 'Withdrawn'),
#     ]
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

#     # Review Information
#     reviewed_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)
#     reviewed_date = models.DateTimeField(null=True, blank=True)
#     review_notes = models.TextField(blank=True)

#     # Supporting Documents
#     id_document = models.FileField(upload_to='applications/id/', blank=True, null=True)
#     income_proof = models.FileField(upload_to='applications/income/', blank=True, null=True)
#     address_proof = models.FileField(upload_to='applications/address/', blank=True, null=True)

#     # Additional Info
#     notes = models.TextField(blank=True)

#     def __str__(self):
#         return f"{self.borrower.full_name} - {self.requested_amount} ({self.status})"

#     class Meta:
#         ordering = ['-application_date']

# class Loan(models.Model):
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='loans')
#     borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE, related_name='loans')
#     application = models.OneToOneField('LoanApplication', on_delete=models.SET_NULL, null=True, blank=True, related_name='loan')

#     # Loan Details
#     loan_number = models.CharField(max_length=50, unique=True)
#     principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
#     interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate in %")
#     loan_term_months = models.PositiveIntegerField()
#     disbursement_date = models.DateField(null=True, blank=True)

#     # Interest Calculation
#     INTEREST_TYPES = [
#         ('SIMPLE', 'Simple Interest'),
#         ('COMPOUND', 'Compound Interest'),
#     ]
#     interest_type = models.CharField(max_length=10, choices=INTEREST_TYPES, default='SIMPLE')

#     # Loan Status
#     STATUS_CHOICES = [
#         ('PENDING_DISBURSEMENT', 'Pending Disbursement'),
#         ('ACTIVE', 'Active'),
#         ('PAID_OFF', 'Paid Off'),
#         ('DEFAULTED', 'Defaulted'),
#         ('WRITTEN_OFF', 'Written Off'),
#     ]
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_DISBURSEMENT')

#     # Financial Tracking
#     total_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     total_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

#     # Due Dates
#     first_payment_date = models.DateField(null=True, blank=True)
#     maturity_date = models.DateField(null=True, blank=True)

#     # Processing
#     approved_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
#     disbursed_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='disbursed_loans')

#     # Notes
#     notes = models.TextField(blank=True)

#     def save(self, *args, **kwargs):
#         if not self.loan_number:
#             # Generate loan number
#             import uuid
#             self.loan_number = f"LN{uuid.uuid4().hex[:8].upper()}"

#         # Calculate total interest if not set
#         if not self.total_interest and self.principal_amount and self.interest_rate and self.loan_term_months:
#             calculator = LoanCalculator()
#             if self.interest_type == 'SIMPLE':
#                 self.total_interest = calculator.calculate_simple_interest(
#                     float(self.principal_amount),
#                     float(self.interest_rate),
#                     self.loan_term_months
#                 )
#             else:
#                 # For compound interest, calculate based on monthly payments
#                 monthly_payment = calculator.calculate_monthly_payment(
#                     float(self.principal_amount),
#                     float(self.interest_rate),
#                     self.loan_term_months
#                 )
#                 self.total_interest = (monthly_payment * self.loan_term_months) - float(self.principal_amount)

#         # Set outstanding balance if not set
#         if self.outstanding_balance is None:
#             self.outstanding_balance = self.principal_amount

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.loan_number} - {self.borrower.full_name} - {self.principal_amount}"

# class Collateral(models.Model):
#     loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='collaterals')

#     COLLATERAL_TYPES = [
#         ('REAL_ESTATE', 'Real Estate'),
#         ('VEHICLE', 'Vehicle'),
#         ('EQUIPMENT', 'Equipment'),
#         ('INVENTORY', 'Inventory'),
#         ('SECURITIES', 'Securities'),
#         ('OTHER', 'Other'),
#     ]
#     collateral_type = models.CharField(max_length=20, choices=COLLATERAL_TYPES)
#     description = models.TextField()
#     estimated_value = models.DecimalField(max_digits=12, decimal_places=2)
#     document = models.FileField(upload_to='collaterals/', blank=True, null=True, help_text="Collateral document/proof")

#     def __str__(self):
#         return f"{self.collateral_type} - {self.estimated_value}"

# class OperatingExpense(models.Model):
#     EXPENSE_CATEGORIES = [
#         ('ADMINISTRATIVE', 'Administrative'),
#         ('MARKETING', 'Marketing'),
#         ('LEGAL', 'Legal & Compliance'),
#         ('TECHNOLOGY', 'Technology'),
#         ('OFFICE', 'Office Expenses'),
#         ('TRAVEL', 'Travel'),
#         ('OTHER', 'Other'),
#     ]

#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='operating_expenses')
#     category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
#     description = models.CharField(max_length=255)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     date = models.DateField()
#     payment_method = models.CharField(max_length=20, choices=[
#         ('CASH', 'Cash'),
#         ('BANK_TRANSFER', 'Bank Transfer'),
#         ('CREDIT_CARD', 'Credit Card'),
#         ('CHECK', 'Check'),
#     ], default='CASH')
#     receipt = models.FileField(upload_to='expenses/', blank=True, null=True)
#     approved_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)

#     def __str__(self):
#         return f"{self.category} - {self.amount} on {self.date}"
# class LoanRepayment(models.Model):
#     loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='repayments')
#     borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE, related_name='repayments')

#     # Payment Details
#     payment_date = models.DateField(auto_now_add=True)
#     amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
#     principal_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     interest_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

#     # Payment Method
#     PAYMENT_METHODS = [
#         ('CASH', 'Cash'),
#         ('BANK_TRANSFER', 'Bank Transfer'),
#         ('MOBILE_MONEY', 'Mobile Money'),
#         ('CHECK', 'Check'),
#     ]
#     payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS, default='CASH')
#     reference_number = models.CharField(max_length=100, blank=True, null=True)

#     # Processing
#     received_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)
#     receipt_number = models.CharField(max_length=50, blank=True, null=True)

#     # Status
#     STATUS_CHOICES = [
#         ('PENDING', 'Pending'),
#         ('CONFIRMED', 'Confirmed'),
#         ('FAILED', 'Failed'),
#     ]
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

#     # Notes
#     notes = models.TextField(blank=True)

#     def save(self, *args, **kwargs):
#         if self.pk is None:  # New repayment
#             self.loan.total_repaid += self.amount_paid
#             self.loan.outstanding_balance -= self.principal_paid
#             self.borrower.total_repaid += self.amount_paid
#             self.borrower.outstanding_balance -= self.principal_paid
#         else:  # Updating existing repayment
#             old = LoanRepayment.objects.get(pk=self.pk)
#             self.loan.total_repaid += (self.amount_paid - old.amount_paid)
#             self.loan.outstanding_balance -= (self.principal_paid - old.principal_paid)
#             self.borrower.total_repaid += (self.amount_paid - old.amount_paid)
#             self.borrower.outstanding_balance -= (self.principal_paid - old.principal_paid)

#         self.loan.save(update_fields=['total_repaid', 'outstanding_balance'])
#         self.borrower.save(update_fields=['total_repaid', 'outstanding_balance'])
#         super().save(*args, **kwargs)

#     def delete(self, *args, **kwargs):
#         self.loan.total_repaid -= self.amount_paid
#         self.loan.outstanding_balance += self.principal_paid
#         self.borrower.total_repaid -= self.amount_paid
#         self.borrower.outstanding_balance += self.principal_paid
#         self.loan.save(update_fields=['total_repaid', 'outstanding_balance'])
#         self.borrower.save(update_fields=['total_repaid', 'outstanding_balance'])
#         super().delete(*args, **kwargs)

#     def __str__(self):
#         return f"{self.loan.loan_number} - {self.amount_paid} on {self.payment_date}"

# class RepaymentSchedule(models.Model):
#     loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='repayment_schedule')

#     # Schedule Details
#     installment_number = models.PositiveIntegerField()
#     due_date = models.DateField()
#     principal_due = models.DecimalField(max_digits=12, decimal_places=2)
#     interest_due = models.DecimalField(max_digits=12, decimal_places=2)
#     total_due = models.DecimalField(max_digits=12, decimal_places=2)

#     # Payment Status
#     STATUS_CHOICES = [
#         ('PENDING', 'Pending'),
#         ('PAID', 'Paid'),
#         ('OVERDUE', 'Overdue'),
#         ('PARTIAL', 'Partial Payment'),
#     ]
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

#     # Actual Payment
#     amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     payment_date = models.DateField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.loan.loan_number} - Installment {self.installment_number} - {self.due_date}"

#     class Meta:
#         ordering = ['due_date']
#         unique_together = ['loan', 'installment_number']

# class LoanProduct(models.Model):
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='loan_products')

#     # Product Details
#     name = models.CharField(max_length=100)
#     description = models.TextField(blank=True)
#     min_amount = models.DecimalField(max_digits=12, decimal_places=2)
#     max_amount = models.DecimalField(max_digits=12, decimal_places=2)
#     min_term_months = models.PositiveIntegerField()
#     max_term_months = models.PositiveIntegerField()

#     # Interest Settings
#     interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate in %")
#     interest_type = models.CharField(max_length=10, choices=[('SIMPLE', 'Simple'), ('COMPOUND', 'Compound')], default='SIMPLE')

#     # Eligibility Criteria
#     min_credit_score = models.PositiveIntegerField(default=0)
#     requires_collateral = models.BooleanField(default=False)
#     max_debt_to_income_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0.50, help_text="Maximum debt-to-income ratio")

#     # Status
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.name} - {self.min_amount} to {self.max_amount}"

# class LoanPortfolio(models.Model):
#     lender = models.OneToOneField('Lender', on_delete=models.CASCADE, related_name='portfolio')

#     # Portfolio Metrics
#     total_loans_outstanding = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
#     total_principal_disbursed = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
#     total_interest_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
#     total_repayments_received = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

#     # Risk Metrics
#     active_loans_count = models.PositiveIntegerField(default=0)
#     overdue_loans_count = models.PositiveIntegerField(default=0)
#     defaulted_loans_count = models.PositiveIntegerField(default=0)
#     average_loan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

#     # Performance
#     portfolio_return_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Annual return rate in %")
#     delinquency_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage of loans overdue")

#     # Last Updated
#     last_updated = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.lender.name} Portfolio"

# # class Expense(models.Model):
# #     church = models.ForeignKey('Church', on_delete=models.CASCADE, related_name='financial_expenses')
# #     budget = models.ForeignKey(Budget, related_name="expenses", on_delete=models.CASCADE)
# #     vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
# #     description = models.CharField(max_length=255)
# #     amount = models.DecimalField(max_digits=12, decimal_places=2)
# #     expense_date = models.DateField()
# #     created_at = models.DateTimeField(auto_now_add=True)

# #     def __str__(self):
# #         return f"{self.church.name} - {self.description} - {self.amount}"

# # Remove old Payment and VendorPayment models as they're replaced by OperatingExpense

# class Staff(models.Model):
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='staff', null=True, blank=True)
#     user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name="staff_profile")
#     phone = models.CharField(max_length=20, blank=True, null=True)
#     position = models.CharField(max_length=100, blank=True, null=True)
#     hire_date = models.DateField(null=True, blank=True)
#     salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.user.get_full_name()} ({self.lender.name if self.lender else 'No Lender'})"

# class BankAccount(models.Model):
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='bank_accounts')
#     bank_name = models.CharField(max_length=100)
#     account_number = models.CharField(max_length=50)
#     account_name = models.CharField(max_length=100)
#     branch = models.CharField(max_length=100, blank=True)
#     is_primary = models.BooleanField(default=False)

#     class Meta:
#         unique_together = ('lender', 'account_number')

#     def __str__(self):
#         return f"{self.bank_name} - {self.account_number}"


# class CashTransaction(models.Model):
#     TRANSACTION_TYPES = [
#         ('DEPOSIT', 'Deposit'),
#         ('WITHDRAWAL', 'Withdrawal'),
#         ('LOAN_DISBURSEMENT', 'Loan Disbursement'),
#         ('REPAYMENT_RECEIVED', 'Repayment Received'),
#         ('EXPENSE', 'Operating Expense'),
#         ('OTHER', 'Other'),
#     ]

#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='cash_transactions')
#     transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     description = models.TextField(blank=True)
#     staff = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, related_name="cash_transactions")
#     date = models.DateTimeField(auto_now_add=True)
#     receipt = models.FileField(upload_to="cash_transactions/", blank=True, null=True)

#     def __str__(self):
#         return f"{self.lender.name} | {self.transaction_type} - {self.amount}"


# class BankTransaction(models.Model):
#     TRANSACTION_TYPES = [
#         ('DEPOSIT', 'Deposit'),
#         ('WITHDRAWAL', 'Withdrawal'),
#         ('TRANSFER_IN', 'Transfer In'),
#         ('TRANSFER_OUT', 'Transfer Out'),
#     ]

#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='bank_transactions')
#     bank_account = models.ForeignKey('BankAccount', on_delete=models.CASCADE, related_name="transactions")
#     transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     description = models.TextField(blank=True)
#     reference_number = models.CharField(max_length=100, blank=True)
#     staff = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, related_name="bank_transactions")
#     date = models.DateTimeField(auto_now_add=True)
#     receipt = models.FileField(upload_to="bank_transactions/", blank=True, null=True)

#     def __str__(self):
#         return f"{self.bank_account.bank_name} | {self.transaction_type} - {self.amount}"


# class LoanReport(models.Model):
#     """
#     Model for generating loan performance reports (not stored in DB).
#     """
#     lender = models.ForeignKey('Lender', on_delete=models.CASCADE)
#     start_date = models.DateField()
#     end_date = models.DateField()

#     class Meta:
#         verbose_name = "Loan Performance Report"
#         verbose_name_plural = "Loan Performance Reports"
#         managed = False

#     def total_loans_disbursed(self):
#         return Loan.objects.filter(
#             lender=self.lender,
#             disbursement_date__range=(self.start_date, self.end_date)
#         ).aggregate(total=Sum('principal_amount'))['total'] or 0

#     def total_repayments_received(self):
#         return LoanRepayment.objects.filter(
#             loan__lender=self.lender,
#             payment_date__range=(self.start_date, self.end_date)
#         ).aggregate(total=Sum('amount_paid'))['total'] or 0

#     def total_interest_earned(self):
#         return LoanRepayment.objects.filter(
#             loan__lender=self.lender,
#             payment_date__range=(self.start_date, self.end_date)
#         ).aggregate(total=Sum('interest_paid'))['total'] or 0

#     def outstanding_principal(self):
#         disbursed = self.total_loans_disbursed()
#         repaid_principal = LoanRepayment.objects.filter(
#             loan__lender=self.lender,
#             payment_date__range=(self.start_date, self.end_date)
#         ).aggregate(total=Sum('principal_paid'))['total'] or 0
#         return disbursed - repaid_principal

#     def net_profit(self):
#         return self.total_interest_earned() - OperatingExpense.objects.filter(
#             lender=self.lender,
#             date__range=(self.start_date, self.end_date)
#         ).aggregate(total=Sum('amount'))['total'] or 0

#     def __str__(self):
#         return f"{self.lender.name} | {self.start_date} to {self.end_date}"


# # ===========================
# # Loan Management Features
# # ===========================

# class LoanCalculator:
#     """Utility class for loan calculations"""

#     @staticmethod
#     def calculate_simple_interest(principal, rate, time_months):
#         """Calculate simple interest"""
#         rate_decimal = rate / 100
#         time_years = time_months / 12
#         return principal * rate_decimal * time_years

#     @staticmethod
#     def calculate_monthly_payment(principal, annual_rate, months):
#         """Calculate monthly payment using amortization formula"""
#         if annual_rate == 0:
#             return principal / months

#         monthly_rate = annual_rate / 100 / 12
#         payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
#         return payment

#     @staticmethod
#     def calculate_total_amount_payable(principal, annual_rate, months):
#         """Calculate total amount borrower will pay"""
#         monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, months)
#         return monthly_payment * months

#     @staticmethod
#     def calculate_due_dates(start_date, term_months):
#         """Generate list of due dates for loan repayments"""
#         from dateutil.relativedelta import relativedelta
#         due_dates = []
#         current_date = start_date
#         for month in range(term_months):
#             due_dates.append(current_date)
#             current_date += relativedelta(months=1)
#         return due_dates

#     @staticmethod
#     def generate_repayment_schedule(loan):
#         """Generate repayment schedule for a loan"""
#         from dateutil.relativedelta import relativedelta
#         from decimal import Decimal

#         schedule = []
#         principal_remaining = loan.principal_amount
#         monthly_rate = loan.interest_rate / 100 / 12
#         monthly_payment = LoanCalculator.calculate_monthly_payment(
#             float(loan.principal_amount), float(loan.interest_rate), loan.loan_term_months
#         )

#         current_date = loan.first_payment_date or loan.disbursement_date

#         for month in range(1, loan.loan_term_months + 1):
#             interest_due = principal_remaining * monthly_rate
#             principal_due = monthly_payment - interest_due

#             if principal_due > principal_remaining:
#                 principal_due = principal_remaining
#                 monthly_payment = principal_due + interest_due

#             schedule.append({
#                 'installment_number': month,
#                 'due_date': current_date,
#                 'principal_due': Decimal(str(round(principal_due, 2))),
#                 'interest_due': Decimal(str(round(interest_due, 2))),
#                 'total_due': Decimal(str(round(monthly_payment, 2))),
#                 'principal_remaining': principal_remaining - principal_due
#             })

#             principal_remaining -= principal_due
#             current_date += relativedelta(months=1)

#         return schedule

#     @staticmethod
#     def calculate_credit_score(borrower):
#         """Calculate credit score based on borrower's history"""
#         score = 500  # Base score

#         # Payment history (40% weight)
#         total_repayments = borrower.repayments.count()
#         on_time_payments = borrower.repayments.filter(status='CONFIRMED').count()
#         if total_repayments > 0:
#             payment_ratio = on_time_payments / total_repayments
#             score += int(payment_ratio * 200)  # 0-200 points

#         # Loan history (30% weight)
#         total_loans = borrower.loans.count()
#         completed_loans = borrower.loans.filter(status='PAID_OFF').count()
#         if total_loans > 0:
#             completion_ratio = completed_loans / total_loans
#             score += int(completion_ratio * 150)  # 0-150 points

#         # Outstanding balance ratio (20% weight)
#         if borrower.total_loans_taken > 0:
#             balance_ratio = borrower.outstanding_balance / borrower.total_loans_taken
#             score -= int(balance_ratio * 100)  # Deduct 0-100 points

#         # Employment stability (10% weight)
#         if borrower.employment_status in ['EMPLOYED', 'SELF_EMPLOYED']:
#             score += 50

#         return min(max(score, 300), 850)  # Cap between 300-850


# loans app - combined models, signals, and app config
# Save as: loans/models.py (signals imported from loans/signals.py via apps.py)

from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum, Q
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import AppConfig
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import uuid

# -----------------------------
# Models
# -----------------------------

class Lender(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='users', null=True, blank=True)

    def __str__(self):
        return self.username


class Borrower(models.Model):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='borrowers')

    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=[("Male", "Male"), ("Female", "Female")], default="Male")
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    borrower_id = models.CharField(max_length=50, unique=True)
    date_registered = models.DateField(auto_now_add=True)
    credit_score = models.PositiveIntegerField(default=500, help_text="Credit score (300-850)")
    employment_status = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('EMPLOYED', 'Employed'),
        ('SELF_EMPLOYED', 'Self Employed'),
        ('UNEMPLOYED', 'Unemployed'),
        ('STUDENT', 'Student'),
        ('RETIRED', 'Retired'),
    ])
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    total_loans_taken = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_repaid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True, null=True)

    def update_credit_score(self):
        from .models import LoanCalculator  # avoid circular import in some contexts
        # safe-guard: ensure numeric fields are Decimal
        try:
            self.credit_score = LoanCalculator.calculate_credit_score(self)
        except Exception:
            # keep existing score if calculation fails
            pass
        self.save(update_fields=['credit_score'])

    def __str__(self):
        return self.full_name


class Staff(models.Model):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='staff', null=True, blank=True)
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name="staff_profile")
    phone = models.CharField(max_length=20, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.lender.name if self.lender else 'No Lender'})"


class LoanProduct(models.Model):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='loan_products')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_term_months = models.PositiveIntegerField()
    max_term_months = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    interest_type = models.CharField(max_length=10, choices=[('SIMPLE', 'Simple'), ('COMPOUND', 'Compound')], default='SIMPLE')
    min_credit_score = models.PositiveIntegerField(default=0)
    requires_collateral = models.BooleanField(default=False)
    max_debt_to_income_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.50'))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.min_amount} to {self.max_amount}"


class LoanApplication(models.Model):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='loan_applications')
    borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE, related_name='loan_applications')
    application_date = models.DateField(auto_now_add=True)
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField(blank=True)
    loan_term_months = models.PositiveIntegerField()

    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    reviewed_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    id_document = models.FileField(upload_to='applications/id/', blank=True, null=True)
    income_proof = models.FileField(upload_to='applications/income/', blank=True, null=True)
    address_proof = models.FileField(upload_to='applications/address/', blank=True, null=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.borrower.full_name} - {self.requested_amount} ({self.status})"


class Loan(models.Model):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='loans')
    borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE, related_name='loans')
    application = models.OneToOneField('LoanApplication', on_delete=models.SET_NULL, null=True, blank=True, related_name='loan')

    loan_number = models.CharField(max_length=50, unique=True, blank=True)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate in %")
    loan_term_months = models.PositiveIntegerField()
    disbursement_date = models.DateField(null=True, blank=True)

    INTEREST_TYPES = [
        ('SIMPLE', 'Simple Interest'),
        ('COMPOUND', 'Compound Interest'),
    ]
    interest_type = models.CharField(max_length=10, choices=INTEREST_TYPES, default='SIMPLE')

    STATUS_CHOICES = [
        ('PENDING_DISBURSEMENT', 'Pending Disbursement'),
        ('ACTIVE', 'Active'),
        ('PAID_OFF', 'Paid Off'),
        ('DEFAULTED', 'Defaulted'),
        ('WRITTEN_OFF', 'Written Off'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_DISBURSEMENT')

    total_interest = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_repaid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    first_payment_date = models.DateField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)

    approved_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    disbursed_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='disbursed_loans')

    notes = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['status']), models.Index(fields=['disbursement_date'])]

    def save(self, *args, **kwargs):
        # generate loan number
        if not self.loan_number:
            self.loan_number = f"LN{uuid.uuid4().hex[:10].upper()}"

        # validate parameters
        try:
            LoanCalculator.validate_loan_parameters(float(self.principal_amount), float(self.interest_rate), self.loan_term_months)
        except ValueError as e:
            raise ValueError(f"Invalid loan parameters: {e}")

        # calculate total_interest for simple interest
        if self.interest_type == 'SIMPLE':
            self.total_interest = LoanCalculator.calculate_simple_interest(float(self.principal_amount), float(self.interest_rate), self.loan_term_months)
        else:
            # for compound interest, calculate initial estimate; will be updated dynamically via signals
            monthly_payment = LoanCalculator.calculate_monthly_payment(float(self.principal_amount), float(self.interest_rate), self.loan_term_months)
            total_payable = (monthly_payment * Decimal(str(self.loan_term_months))).quantize(Decimal('0.01'))
            self.total_interest = (total_payable - Decimal(str(self.principal_amount))).quantize(Decimal('0.01'))

        # default outstanding balance on creation
        if self._state.adding and (self.outstanding_balance is None or self.outstanding_balance == Decimal('0.00')):
            self.outstanding_balance = self.principal_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan_number} - {self.borrower.full_name} - {self.principal_amount}"


class Collateral(models.Model):
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='collaterals')
    COLLATERAL_TYPES = [
        ('REAL_ESTATE', 'Real Estate'),
        ('VEHICLE', 'Vehicle'),
        ('EQUIPMENT', 'Equipment'),
        ('INVENTORY', 'Inventory'),
        ('SECURITIES', 'Securities'),
        ('OTHER', 'Other'),
    ]
    collateral_type = models.CharField(max_length=20, choices=COLLATERAL_TYPES)
    description = models.TextField()
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2)
    document = models.FileField(upload_to='collaterals/', blank=True, null=True)

    def __str__(self):
        return f"{self.collateral_type} - {self.estimated_value}"


class OperatingExpense(models.Model):
    EXPENSE_CATEGORIES = [
        ('ADMINISTRATIVE', 'Administrative'),
        ('MARKETING', 'Marketing'),
        ('LEGAL', 'Legal & Compliance'),
        ('TECHNOLOGY', 'Technology'),
        ('OFFICE', 'Office Expenses'),
        ('TRAVEL', 'Travel'),
        ('OTHER', 'Other'),
    ]
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='operating_expenses')
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=[
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('CHECK', 'Check'),
    ], default='CASH')
    receipt = models.FileField(upload_to='expenses/', blank=True, null=True)
    approved_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.category} - {self.amount} on {self.date}"


class LoanRepayment(models.Model):
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='repayments')
    borrower = models.ForeignKey('Borrower', on_delete=models.CASCADE, related_name='repayments')

    payment_date = models.DateField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    principal_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    interest_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CHECK', 'Check'),
    ]
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS, default='CASH')
    reference_number = models.CharField(max_length=100, blank=True, null=True)

    received_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        """
        Automatically calculate principal and interest portions
        when repayment is saved, based on loan’s remaining interest balance.
        """
        if self.amount_paid and self.loan:
            if self.amount_paid < 0:
                raise ValueError("Amount paid cannot be negative.")
            # estimate interest due for this installment
            monthly_rate = Decimal(str(self.loan.interest_rate)) / Decimal('100') / Decimal('12')
            # interest on current outstanding principal
            expected_interest = (self.loan.outstanding_balance * monthly_rate).quantize(Decimal('0.01'))

            # allocate payment
            if self.amount_paid >= expected_interest:
                self.interest_paid = expected_interest
                self.principal_paid = (self.amount_paid - expected_interest).quantize(Decimal('0.01'))
            else:
                # partial interest payment
                self.interest_paid = self.amount_paid
                self.principal_paid = Decimal('0.00')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan.loan_number} - {self.amount_paid} on {self.payment_date}"



class RepaymentSchedule(models.Model):
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='repayment_schedule')
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    principal_due = models.DecimalField(max_digits=15, decimal_places=2)
    interest_due = models.DecimalField(max_digits=15, decimal_places=2)
    total_due = models.DecimalField(max_digits=15, decimal_places=2)

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('PARTIAL', 'Partial Payment'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']
        unique_together = ['loan', 'installment_number']

    def __str__(self):
        return f"{self.loan.loan_number} - Installment {self.installment_number} - {self.due_date}"


class BankAccount(models.Model):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('lender', 'account_number')

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class CashTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('LOAN_DISBURSEMENT', 'Loan Disbursement'),
        ('REPAYMENT_RECEIVED', 'Repayment Received'),
        ('EXPENSE', 'Operating Expense'),
        ('OTHER', 'Other'),
    ]
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='cash_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    staff = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, related_name="cash_transactions")
    date = models.DateTimeField(auto_now_add=True)
    receipt = models.FileField(upload_to="cash_transactions/", blank=True, null=True)

    def __str__(self):
        return f"{self.lender.name} | {self.transaction_type} - {self.amount}"


class BankTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER_IN', 'Transfer In'),
        ('TRANSFER_OUT', 'Transfer Out'),
    ]
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE, related_name='bank_transactions')
    bank_account = models.ForeignKey('BankAccount', on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    staff = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, related_name="bank_transactions")
    date = models.DateTimeField(auto_now_add=True)
    receipt = models.FileField(upload_to="bank_transactions/", blank=True, null=True)

    def __str__(self):
        return f"{self.bank_account.bank_name} | {self.transaction_type} - {self.amount}"


class LoanPortfolio(models.Model):
    lender = models.OneToOneField('Lender', on_delete=models.CASCADE, related_name='portfolio')

    total_loans_outstanding = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    total_principal_disbursed = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    total_interest_earned = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
    total_repayments_received = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))

    active_loans_count = models.PositiveIntegerField(default=0)
    overdue_loans_count = models.PositiveIntegerField(default=0)
    defaulted_loans_count = models.PositiveIntegerField(default=0)
    average_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    portfolio_return_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    delinquency_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    last_updated = models.DateTimeField(auto_now=True)

    def update_portfolio(self):
        lender = self.lender
        loans = Loan.objects.filter(lender=lender)
        self.total_loans_outstanding = loans.aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
        self.total_principal_disbursed = loans.aggregate(total=Sum('principal_amount'))['total'] or Decimal('0.00')
        self.total_repayments_received = LoanRepayment.objects.filter(loan__lender=lender).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        self.total_interest_earned = LoanRepayment.objects.filter(loan__lender=lender).aggregate(total=Sum('interest_paid'))['total'] or Decimal('0.00')
        self.active_loans_count = loans.filter(status='ACTIVE').count()
        self.overdue_loans_count = loans.filter(status='DEFAULTED').count()
        self.defaulted_loans_count = loans.filter(status='DEFAULTED').count()
        self.average_loan_amount = (self.total_principal_disbursed / self.active_loans_count) if self.active_loans_count else Decimal('0.00')
        # simple delinquency rate
        total_loans = loans.count()
        self.delinquency_rate = (Decimal(self.overdue_loans_count) / Decimal(total_loans) * Decimal('100')) if total_loans else Decimal('0.00')
        # portfolio_return_rate naive calc
        self.portfolio_return_rate = (Decimal(self.total_interest_earned) / (self.total_principal_disbursed or Decimal('1')) * Decimal('100')) if self.total_principal_disbursed else Decimal('0.00')
        self.save()

    def __str__(self):
        return f"{self.lender.name} Portfolio"


class LoanReport(models.Model):
    lender = models.ForeignKey('Lender', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = "Loan Performance Report"
        verbose_name_plural = "Loan Performance Reports"
        managed = False

    def total_loans_disbursed(self):
        return Loan.objects.filter(lender=self.lender, disbursement_date__range=(self.start_date, self.end_date)).aggregate(total=Sum('principal_amount'))['total'] or Decimal('0.00')

    def total_repayments_received(self):
        return LoanRepayment.objects.filter(loan__lender=self.lender, payment_date__range=(self.start_date, self.end_date)).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

    def total_interest_earned(self):
        return LoanRepayment.objects.filter(loan__lender=self.lender, payment_date__range=(self.start_date, self.end_date)).aggregate(total=Sum('interest_paid'))['total'] or Decimal('0.00')

    def outstanding_principal(self):
        disbursed = self.total_loans_disbursed()
        repaid_principal = LoanRepayment.objects.filter(loan__lender=self.lender, payment_date__range=(self.start_date, self.end_date)).aggregate(total=Sum('principal_paid'))['total'] or Decimal('0.00')
        return disbursed - repaid_principal

    def net_profit(self):
        expenses = OperatingExpense.objects.filter(lender=self.lender, date__range=(self.start_date, self.end_date)).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return self.total_interest_earned() - expenses

    def __str__(self):
        return f"{self.lender.name} | {self.start_date} to {self.end_date}"


# -----------------------------
# Loan Calculator (utility)
# -----------------------------

class LoanCalculator:
    @staticmethod
    def validate_loan_parameters(principal, annual_rate, months):
        """Validate loan parameters and raise ValueError if invalid."""
        if principal <= 0:
            raise ValueError("Principal amount must be positive.")
        if annual_rate < 0:
            raise ValueError("Interest rate cannot be negative.")
        if months <= 0:
            raise ValueError("Loan term must be positive.")

    @staticmethod
    def calculate_simple_interest(principal, rate, time_months):
        LoanCalculator.validate_loan_parameters(principal, rate, time_months)
        rate_decimal = Decimal(str(rate)) / Decimal('100')
        time_years = Decimal(str(time_months)) / Decimal('12')
        return (Decimal(str(principal)) * rate_decimal * time_years).quantize(Decimal('0.01'))

    @staticmethod
    def calculate_monthly_payment(principal, annual_rate, months):
        LoanCalculator.validate_loan_parameters(principal, annual_rate, months)
        principal = Decimal(str(principal))
        if annual_rate == 0:
            return (principal / Decimal(str(months))).quantize(Decimal('0.01'))
        monthly_rate = Decimal(str(annual_rate)) / Decimal('100') / Decimal('12')
        numerator = principal * (monthly_rate * (Decimal('1') + monthly_rate) ** months)
        denominator = ((Decimal('1') + monthly_rate) ** months) - Decimal('1')
        if denominator == 0:
            raise ValueError("Invalid calculation parameters.")
        payment = (numerator / denominator).quantize(Decimal('0.01'))
        return payment

    @staticmethod
    def calculate_total_amount_payable(principal, annual_rate, months):
        monthly_payment = LoanCalculator.calculate_monthly_payment(principal, annual_rate, months)
        return (monthly_payment * Decimal(str(months))).quantize(Decimal('0.01'))

    @staticmethod
    def calculate_due_dates(start_date, term_months):
        if term_months <= 0:
            raise ValueError("Term months must be positive.")
        due_dates = []
        current_date = start_date
        for _ in range(term_months):
            due_dates.append(current_date)
            current_date += relativedelta(months=1)
        return due_dates

    @staticmethod
    def generate_repayment_schedule_dict(loan):
        LoanCalculator.validate_loan_parameters(float(loan.principal_amount), float(loan.interest_rate), loan.loan_term_months)
        schedule = []
        principal_remaining = Decimal(str(loan.principal_amount))
        monthly_rate = Decimal(str(loan.interest_rate)) / Decimal('100') / Decimal('12')
        months = loan.loan_term_months
        monthly_payment = LoanCalculator.calculate_monthly_payment(float(loan.principal_amount), float(loan.interest_rate), months)
        current_date = loan.first_payment_date or loan.disbursement_date
        if not current_date:
            raise ValueError("Loan must have first_payment_date or disbursement_date set.")
        for i in range(1, months + 1):
            interest_due = (principal_remaining * monthly_rate).quantize(Decimal('0.01'))
            principal_due = (monthly_payment - interest_due).quantize(Decimal('0.01'))
            if principal_due > principal_remaining:
                principal_due = principal_remaining
                monthly_payment = (principal_due + interest_due).quantize(Decimal('0.01'))
            schedule.append({
                'installment_number': i,
                'due_date': current_date,
                'principal_due': principal_due,
                'interest_due': interest_due,
                'total_due': monthly_payment,
            })
            principal_remaining -= principal_due
            current_date += relativedelta(months=1)
        return schedule

    @staticmethod
    def calculate_credit_score(borrower):
        # Simple scoring between 300-850
        score = 500
        total_repayments = borrower.repayments.count()
        on_time_payments = borrower.repayments.filter(status='CONFIRMED').count()
        if total_repayments > 0:
            payment_ratio = on_time_payments / total_repayments
            score += int(payment_ratio * 200)

        total_loans = borrower.loans.count()
        completed_loans = borrower.loans.filter(status='PAID_OFF').count()
        if total_loans > 0:
            completion_ratio = completed_loans / total_loans
            score += int(completion_ratio * 150)

        if borrower.total_loans_taken and borrower.total_loans_taken > 0:
            balance_ratio = float(borrower.outstanding_balance / borrower.total_loans_taken)
            score -= int(balance_ratio * 100)

        if borrower.employment_status in ['EMPLOYED', 'SELF_EMPLOYED']:
            score += 50

        return max(300, min(850, score))


# -----------------------------
# Signals - keep in same file for convenience. In production move to signals.py
# -----------------------------

@receiver(post_save, sender=LoanRepayment)
def update_related_on_repayment_save(sender, instance, created, **kwargs):
    """Recalculate loan and borrower aggregates atomically when a repayment is saved."""
    with transaction.atomic():
        loan = instance.loan
        borrower = instance.borrower

        # Recompute totals from DB to avoid drift
        loan_totals = loan.repayments.aggregate(total_paid=Sum('amount_paid'), total_principal=Sum('principal_paid'), total_interest=Sum('interest_paid'))
        total_paid = loan_totals['total_paid'] or Decimal('0.00')
        total_principal = loan_totals['total_principal'] or Decimal('0.00')
        total_interest_paid = loan_totals['total_interest'] or Decimal('0.00')

        loan.total_repaid = total_paid
        loan.outstanding_balance = max(Decimal(str(loan.principal_amount)) - Decimal(str(total_principal)), Decimal('0.00'))

        # update total_interest dynamically for compound interest loans
        if loan.interest_type == 'COMPOUND':
            loan.total_interest = total_interest_paid

        # update loan status when fully paid
        if loan.outstanding_balance <= Decimal('0.00'):
            loan.status = 'PAID_OFF'
            loan.maturity_date = loan.maturity_date or instance.payment_date
        elif loan.status == 'PENDING_DISBURSEMENT':
            loan.status = 'ACTIVE'

        loan.save(update_fields=['total_repaid', 'outstanding_balance', 'total_interest', 'status', 'maturity_date'])

        # Update borrower aggregates
        borrower_totals = borrower.repayments.aggregate(total_paid=Sum('amount_paid'))
        borrower_total_paid = borrower_totals['total_paid'] or Decimal('0.00')
        borrower.total_repaid = borrower_total_paid
        # borrower outstanding balance is sum of outstanding balances across borrower's loans
        borrower_outstanding = borrower.loans.aggregate(total_out=Sum('outstanding_balance'))['total_out'] or Decimal('0.00')
        borrower.outstanding_balance = borrower_outstanding
        borrower.save(update_fields=['total_repaid', 'outstanding_balance'])

        # update credit score (non-blocking minimal risk)
        try:
            borrower.update_credit_score()
        except Exception:
            pass

        # update portfolio
        try:
            portfolio, _ = LoanPortfolio.objects.get_or_create(lender=loan.lender)
            portfolio.update_portfolio()
        except Exception:
            pass


@receiver(post_delete, sender=LoanRepayment)
def update_related_on_repayment_delete(sender, instance, **kwargs):
    with transaction.atomic():
        loan = instance.loan
        borrower = instance.borrower

        loan_totals = loan.repayments.aggregate(total_paid=Sum('amount_paid'), total_principal=Sum('principal_paid'), total_interest=Sum('interest_paid'))
        total_paid = loan_totals['total_paid'] or Decimal('0.00')
        total_principal = loan_totals['total_principal'] or Decimal('0.00')
        total_interest_paid = loan_totals['total_interest'] or Decimal('0.00')

        loan.total_repaid = total_paid
        loan.outstanding_balance = max(Decimal(str(loan.principal_amount)) - Decimal(str(total_principal)), Decimal('0.00'))

        # update total_interest dynamically for compound interest loans
        if loan.interest_type == 'COMPOUND':
            loan.total_interest = total_interest_paid

        if loan.outstanding_balance > 0 and loan.status == 'PAID_OFF':
            loan.status = 'ACTIVE'
        loan.save(update_fields=['total_repaid', 'outstanding_balance', 'total_interest', 'status'])

        borrower_totals = borrower.repayments.aggregate(total_paid=Sum('amount_paid'))
        borrower_total_paid = borrower_totals['total_paid'] or Decimal('0.00')
        borrower.total_repaid = borrower_total_paid
        borrower_outstanding = borrower.loans.aggregate(total_out=Sum('outstanding_balance'))['total_out'] or Decimal('0.00')
        borrower.outstanding_balance = borrower_outstanding
        borrower.save(update_fields=['total_repaid', 'outstanding_balance'])

        try:
            borrower.update_credit_score()
        except Exception:
            pass

        try:
            portfolio, _ = LoanPortfolio.objects.get_or_create(lender=loan.lender)
            portfolio.update_portfolio()
        except Exception:
            pass


# -----------------------------
# Auto-generate repayment schedule when loan is disbursed/activated
# -----------------------------

@receiver(post_save, sender=Loan)
def generate_schedule_on_loan_activation(sender, instance, created, **kwargs):
    """When a loan becomes ACTIVE (disbursed), generate repayment schedule if none exists."""
    try:
        if instance.status == 'ACTIVE':
            # if schedule already exists skip
            if instance.repayment_schedule.exists():
                return
            schedule = LoanCalculator.generate_repayment_schedule_dict(instance)
            with transaction.atomic():
                for item in schedule:
                    RepaymentSchedule.objects.create(
                        loan=instance,
                        installment_number=item['installment_number'],
                        due_date=item['due_date'],
                        principal_due=item['principal_due'],
                        interest_due=item['interest_due'],
                        total_due=item['total_due']
                    )
    except Exception:
        # never bubble up schedule generation errors to avoid blocking loan save
        pass


# -----------------------------
# AppConfig to wire signals automatically when app ready
# -----------------------------

class LoansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'loans'

    def ready(self):
        # import signals by referencing module (signals are defined above in this single-file layout)
        # If you separate signals.py, import it here: import loans.signals
        # Signals are already imported at the top of this file, so they should be connected
        pass

