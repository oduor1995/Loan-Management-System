from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Sum
from django.http import HttpResponse
from django.utils.html import format_html
from django.core.exceptions import ValidationError
import csv
import json
import datetime

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from .models import Borrower, LoanApplication, Loan, LoanRepayment, Collateral, OperatingExpense, LoanProduct, LoanPortfolio, CustomUser, Lender, Staff, BankAccount, CashTransaction, BankTransaction, RepaymentSchedule
from rangefilter.filters import DateRangeFilter
from .models import LoanReport
from django.utils.translation import gettext_lazy as _

from .models import LoanRepayment, OperatingExpense


# ===========================
# Custom AdminSite
# ===========================

class CustomAdminSite(admin.AdminSite):

    site_header = "Loan Management Admin"
    site_title = "Loan Admin Portal"
    index_title = "Welcome to the Loan Dashboard"

    def each_context(self, request):
        context = super().each_context(request)

        if request.user.is_superuser:
            context['site_header'] = "Superuser Dashboard"
            context['site_title'] = "Global Admin Portal"
            context['index_title'] = "Manage All Lenders"
        else:
            if hasattr(request.user, "lender") and request.user.lender:
                lender_name = request.user.lender.name
                context['site_header'] = f"{lender_name} Admin"
                context['site_title'] = f"{lender_name} Portal"
                context['index_title'] = f"Welcome to {lender_name} Dashboard"
            else:
                context['site_header'] = "Loan Admin"
                context['site_title'] = "Portal"
                context['index_title'] = "Welcome"

        return context

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Get lender
        lender = None
        if not request.user.is_superuser and hasattr(request.user, 'lender'):
            lender = request.user.lender

        now = datetime.datetime.now()
        year = now.year

        # Monthly loan performance
        disbursement_data = []
        repayment_data = []
        months = []
        for month in range(1, 13):
            month_start = datetime.date(year, month, 1)
            if month == 12:
                month_end = datetime.date(year+1, 1, 1) - datetime.timedelta(days=1)
            else:
                month_end = datetime.date(year, month+1, 1) - datetime.timedelta(days=1)

            months.append(month_start.strftime('%b'))

            disbursements = Loan.objects.filter(lender=lender, disbursement_date__range=(month_start, month_end)).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0
            repayments = LoanRepayment.objects.filter(loan__lender=lender, payment_date__range=(month_start, month_end)).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

            disbursement_data.append(float(disbursements))
            repayment_data.append(float(repayments))

        extra_context['months_json'] = json.dumps(months)
        extra_context['disbursement_data_json'] = json.dumps(disbursement_data)
        extra_context['repayment_data_json'] = json.dumps(repayment_data)

        # Loan status pie
        loan_statuses = Loan.objects.filter(lender=lender).values('status').annotate(count=Sum('principal_amount')).order_by('-count')
        extra_context['loan_labels_json'] = json.dumps([ls['status'] for ls in loan_statuses])
        extra_context['loan_data_json'] = json.dumps([float(ls['count']) for ls in loan_statuses])

        # Borrower count
        borrower_count = Borrower.objects.filter(lender=lender).count()
        extra_context['borrower_count'] = borrower_count

        # Additional loan metrics for charts
        total_loans_outstanding = Loan.objects.filter(
            lender=lender,
            status__in=['ACTIVE', 'PENDING_DISBURSEMENT']
        ).aggregate(Sum('outstanding_balance'))['outstanding_balance__sum'] or 0

        total_principal_disbursed = Loan.objects.filter(
            lender=lender,
            status__in=['ACTIVE', 'PAID_OFF']
        ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

        total_repayments_received = LoanRepayment.objects.filter(
            loan__lender=lender
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

        total_interest_earned = LoanRepayment.objects.filter(
            loan__lender=lender
        ).aggregate(Sum('interest_paid'))['interest_paid__sum'] or 0

        total_operating_expenses = OperatingExpense.objects.filter(
            lender=lender
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # Loan status counts
        active_loans = Loan.objects.filter(lender=lender, status='ACTIVE').count()
        pending_loans = Loan.objects.filter(lender=lender, status='PENDING_DISBURSEMENT').count()
        paid_off_loans = Loan.objects.filter(lender=lender, status='PAID_OFF').count()
        defaulted_loans = Loan.objects.filter(lender=lender, status='DEFAULTED').count()

        # Recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.datetime.now() - timedelta(days=30)

        recent_applications = LoanApplication.objects.filter(
            lender=lender,
            application_date__gte=thirty_days_ago
        ).count()

        recent_disbursements = Loan.objects.filter(
            lender=lender,
            disbursement_date__gte=thirty_days_ago
        ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

        recent_repayments = LoanRepayment.objects.filter(
            loan__lender=lender,
            payment_date__gte=thirty_days_ago
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

        # Add to context
        extra_context.update({
            'total_loans_outstanding': total_loans_outstanding,
            'total_principal_disbursed': total_principal_disbursed,
            'total_repayments_received': total_repayments_received,
            'total_interest_earned': total_interest_earned,
            'total_operating_expenses': total_operating_expenses,
            'active_loans': active_loans,
            'pending_loans': pending_loans,
            'paid_off_loans': paid_off_loans,
            'defaulted_loans': defaulted_loans,
            'recent_applications': recent_applications,
            'recent_disbursements': recent_disbursements,
            'recent_repayments': recent_repayments,
        })

        # Use custom template instead of default admin index
        from django.template.response import TemplateResponse
        return TemplateResponse(request, "admin/index.html", extra_context | self.each_context(request))

    def app_index(self, request, app_label, extra_context=None):
        extra_context = extra_context or {}

        # Get lender
        lender = None
        if not request.user.is_superuser and hasattr(request.user, 'lender'):
            lender = request.user.lender

        # Always add chart data for loans app
        now = datetime.datetime.now()
        year = now.year

        # Monthly loan performance
        disbursement_data = []
        repayment_data = []
        months = []
        for month in range(1, 13):
            month_start = datetime.date(year, month, 1)
            if month == 12:
                month_end = datetime.date(year+1, 1, 1) - datetime.timedelta(days=1)
            else:
                month_end = datetime.date(year, month+1, 1) - datetime.timedelta(days=1)

            months.append(month_start.strftime('%b'))

            disbursements = Loan.objects.filter(lender=lender, disbursement_date__range=(month_start, month_end)).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0
            repayments = LoanRepayment.objects.filter(loan__lender=lender, payment_date__range=(month_start, month_end)).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

            disbursement_data.append(float(disbursements))
            repayment_data.append(float(repayments))

        extra_context['months_json'] = json.dumps(months)
        extra_context['disbursement_data_json'] = json.dumps(disbursement_data)
        extra_context['repayment_data_json'] = json.dumps(repayment_data)

        # Loan status pie
        loan_statuses = Loan.objects.filter(lender=lender).values('status').annotate(count=Sum('principal_amount')).order_by('-count')
        extra_context['loan_labels_json'] = json.dumps([ls['status'] for ls in loan_statuses])
        extra_context['loan_data_json'] = json.dumps([float(ls['count']) for ls in loan_statuses])

        # Borrower count
        borrower_count = Borrower.objects.filter(lender=lender).count()
        extra_context['borrower_count'] = borrower_count

        # Additional loan metrics for charts
        total_loans_outstanding = Loan.objects.filter(
            lender=lender,
            status__in=['ACTIVE', 'PENDING_DISBURSEMENT']
        ).aggregate(Sum('outstanding_balance'))['outstanding_balance__sum'] or 0

        total_principal_disbursed = Loan.objects.filter(
            lender=lender,
            status__in=['ACTIVE', 'PAID_OFF']
        ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

        total_repayments_received = LoanRepayment.objects.filter(
            loan__lender=lender
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

        total_interest_earned = LoanRepayment.objects.filter(
            loan__lender=lender
        ).aggregate(Sum('interest_paid'))['interest_paid__sum'] or 0

        total_operating_expenses = OperatingExpense.objects.filter(
            lender=lender
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # Loan status counts
        active_loans = Loan.objects.filter(lender=lender, status='ACTIVE').count()
        pending_loans = Loan.objects.filter(lender=lender, status='PENDING_DISBURSEMENT').count()
        paid_off_loans = Loan.objects.filter(lender=lender, status='PAID_OFF').count()
        defaulted_loans = Loan.objects.filter(lender=lender, status='DEFAULTED').count()

        # Recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.datetime.now() - timedelta(days=30)

        recent_applications = LoanApplication.objects.filter(
            lender=lender,
            application_date__gte=thirty_days_ago
        ).count()

        recent_disbursements = Loan.objects.filter(
            lender=lender,
            disbursement_date__gte=thirty_days_ago
        ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

        recent_repayments = LoanRepayment.objects.filter(
            loan__lender=lender,
            payment_date__gte=thirty_days_ago
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

        # Add to context
        extra_context.update({
            'total_loans_outstanding': total_loans_outstanding,
            'total_principal_disbursed': total_principal_disbursed,
            'total_repayments_received': total_repayments_received,
            'total_interest_earned': total_interest_earned,
            'total_operating_expenses': total_operating_expenses,
            'active_loans': active_loans,
            'pending_loans': pending_loans,
            'paid_off_loans': paid_off_loans,
            'defaulted_loans': defaulted_loans,
            'recent_applications': recent_applications,
            'recent_disbursements': recent_disbursements,
            'recent_repayments': recent_repayments,
        })

        return super().app_index(request, app_label, extra_context)


custom_admin_site = CustomAdminSite(name="custom_admin")


# Override the template for the app index to use our custom template
custom_admin_site.app_index_template = 'admin/index.html'


# ===========================
# Forms
# ===========================

class BaseLenderRestrictedForm(forms.ModelForm):
    """Restrict lender dropdown to the logged-in user's lender"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'lender' in self.fields and hasattr(self, 'current_user') and getattr(self.current_user, 'lender', None):
            self.fields['lender'].queryset = Lender.objects.filter(id=self.current_user.lender.id)


class BorrowerAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = Borrower
        fields = '__all__'


class LoanApplicationAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = LoanApplication
        fields = '__all__'


class LoanAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = Loan
        fields = '__all__'


class LoanRepaymentAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = LoanRepayment
        fields = '__all__'


class OperatingExpenseAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = OperatingExpense
        fields = '__all__'


class CustomUserChangeForm(BaseLenderRestrictedForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

class LoanProductAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = LoanProduct
        fields = '__all__'

class StaffAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = Staff
        fields = '__all__'


class BankAccountAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = BankAccount
        fields = '__all__'


class CashTransactionAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = CashTransaction
        fields = '__all__'


class BankTransactionAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = BankTransaction
        fields = '__all__'

class LoanReportAdminForm(BaseLenderRestrictedForm):
    class Meta:
        model = LoanReport
        fields = '__all__'

class BorrowerRepaymentFilterForm(forms.Form):
    borrower = forms.ModelChoiceField(
        queryset=Borrower.objects.all(),
        required=True,
        label="Select Borrower"
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Start Date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="End Date"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # 🔒 Restrict borrowers by lender if not superuser
        if user and not user.is_superuser and hasattr(user, 'lender') and user.lender:
            self.fields['borrower'].queryset = Borrower.objects.filter(lender=user.lender)


# ===========================
# Resources (for import-export)
# ===========================

class BorrowerResource(resources.ModelResource):
    class Meta:
        model = Borrower
        fields = (
            'id', 'full_name', 'gender', 'date_of_birth', 'phone', 'email',
            'address', 'borrower_id', 'credit_score', 'employment_status', 'monthly_income',
            'total_loans_taken', 'total_repaid', 'outstanding_balance', 'notes', 'lender'
        )
        import_id_fields = ['phone']


class LoanRepaymentResource(resources.ModelResource):
    borrower = fields.Field(
        column_name='borrower_phone',
        attribute='borrower',
        widget=ForeignKeyWidget(Borrower, 'phone')
    )

    class Meta:
        model = LoanRepayment
        fields = ('id', 'loan', 'borrower', 'amount_paid', 'principal_paid', 'interest_paid', 'payment_method', 'reference_number', 'notes', 'payment_date')
        export_order = ('id', 'loan', 'borrower', 'amount_paid', 'principal_paid', 'interest_paid', 'payment_method', 'reference_number', 'notes', 'payment_date')
    


# ===========================
# Base Admin (shared restrictions)
# ===========================

class LenderRestrictedAdmin(ImportExportModelAdmin):
    """Base admin: restrict queryset + auto-assign lender"""
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(lender=request.user.lender)

    def save_model(self, request, obj, form, change):
        if not obj.lender and hasattr(request.user, 'lender') and request.user.lender:
            obj.lender = request.user.lender
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form


# ===========================
# Admin Classes
# ===========================

class CustomUserAdmin(UserAdmin, LenderRestrictedAdmin):
    form = CustomUserChangeForm
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('lender',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('lender',)}),)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(lender=request.user.lender)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the lender field to the current user's lender (for non-superusers)
        if db_field.name == "lender" and not request.user.is_superuser:
            kwargs["queryset"] = Lender.objects.filter(id=request.user.lender.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# members/admin.py
from django.db.models import Sum
from .models import Borrower

class BorrowerAdmin(LenderRestrictedAdmin):
    resource_class = BorrowerResource
    form = BorrowerAdminForm

    list_display = ("full_name", "phone", "borrower_id", "credit_score", "outstanding_balance", "lender")

    def total_loans(self, obj):
        return obj.loans.count()
    total_loans.short_description = "Total Loans"



class LoanApplicationAdmin(LenderRestrictedAdmin):
    form = LoanApplicationAdminForm

    list_display = ('borrower', 'requested_amount', 'status', 'application_date', 'lender')
    list_filter = ('status', ('application_date', admin.DateFieldListFilter))
    search_fields = ('borrower__full_name', 'borrower__phone')
    ordering = ('-application_date',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the borrower dropdown to the logged-in user's lender
        if db_field.name == "borrower" and not request.user.is_superuser:
            kwargs["queryset"] = Borrower.objects.filter(lender=request.user.lender)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class LoanAdmin(LenderRestrictedAdmin):
    form = LoanAdminForm

    list_display = ('loan_number', 'borrower', 'principal_amount', 'status', 'disbursement_date', 'lender')
    list_filter = ('status', ('disbursement_date', admin.DateFieldListFilter))
    search_fields = ('loan_number', 'borrower__full_name', 'borrower__phone')
    ordering = ('-disbursement_date',)

    def save_model(self, request, obj, form, change):
        # Validate borrower is not None
        if obj.borrower_id is None:
            raise ValidationError("Borrower is required.")

        # Validate borrower exists in database
        if not Borrower.objects.filter(id=obj.borrower_id).exists():
            raise ValidationError("The selected borrower does not exist.")

        # Validate that the borrower belongs to the user's lender (for non-superusers)
        if not request.user.is_superuser:
            borrower = Borrower.objects.get(id=obj.borrower_id)
            if borrower.lender != request.user.lender:
                raise ValidationError("The selected borrower does not belong to your lender.")

        # Ensure lender is set
        if obj.lender_id is None and hasattr(request.user, 'lender') and request.user.lender:
            obj.lender = request.user.lender

        # Validate lender is set and exists
        if obj.lender_id is None:
            raise ValidationError("Lender is required.")
        if not Lender.objects.filter(id=obj.lender_id).exists():
            raise ValidationError("The selected lender does not exist.")

        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the borrower dropdown to the logged-in user's lender
        if db_field.name == "borrower" and not request.user.is_superuser:
            kwargs["queryset"] = Borrower.objects.filter(lender=request.user.lender)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class LoanRepaymentAdmin(LenderRestrictedAdmin):
    resource_class = LoanRepaymentResource
    form = LoanRepaymentAdminForm

    list_display = ('loan', 'borrower', 'amount_paid', 'payment_date', 'status')
    list_filter = ('status', 'payment_method', ('payment_date', admin.DateFieldListFilter))
    search_fields = ('loan__loan_number', 'borrower__full_name', 'borrower__phone')
    ordering = ('-payment_date',)

    def get_queryset(self, request):
        qs = super(LenderRestrictedAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(loan__lender=request.user.lender)


    def save_model(self, request, obj, form, change):
        # LoanRepayment doesn't have a direct lender field, so skip lender assignment
        super(LenderRestrictedAdmin, self).save_model(request, obj, form, change)
        # Force update of related models after save
        from django.db.models.signals import post_save
        from .models import update_related_on_repayment_save
        post_save.send(sender=obj.__class__, instance=obj, created=not change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the loan and borrower dropdowns to the logged-in user's lender
        if db_field.name == "loan" and not request.user.is_superuser:
            kwargs["queryset"] = Loan.objects.filter(lender=request.user.lender)
        if db_field.name == "borrower" and not request.user.is_superuser:
            kwargs["queryset"] = Borrower.objects.filter(lender=request.user.lender)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)




class OperatingExpenseAdmin(LenderRestrictedAdmin):
    form = OperatingExpenseAdminForm
    list_display = ("category", "description", "amount", "date", "lender")
    list_filter = (
        "category",
        ("date", DateRangeFilter),  # <-- adds calendar pickers
    )
    search_fields = ("description",)
    ordering = ("-date",)


class StaffAdmin(LenderRestrictedAdmin):
    form = StaffAdminForm
    list_display = ('user', 'phone', 'position', 'lender')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Restrict the user field to users from the current user's lender
        if db_field.name == "user" and not request.user.is_superuser:
            kwargs["queryset"] = CustomUser.objects.filter(lender=request.user.lender)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BankAccountAdmin(LenderRestrictedAdmin):
    form = BankAccountAdminForm
    list_display = ('bank_name', 'account_number', 'account_name', 'is_primary', 'lender')
    search_fields = ('bank_name', 'account_number', 'account_name')


class CashTransactionAdmin(LenderRestrictedAdmin):
    form = CashTransactionAdminForm
    list_display = ('transaction_type', 'amount', 'description', 'staff', 'date', 'lender')
    list_filter = ('transaction_type', ('date', admin.DateFieldListFilter))
    search_fields = ('description', 'staff__user__username', 'staff__user__first_name', 'staff__user__last_name')
    ordering = ('-date',)


class BankTransactionAdmin(LenderRestrictedAdmin):
    form = BankTransactionAdminForm
    list_display = ('bank_account', 'transaction_type', 'amount', 'description', 'date', 'lender')
    list_filter = ('transaction_type', ('date', admin.DateFieldListFilter))
    search_fields = ('bank_account__bank_name', 'description')
    ordering = ('-date',)


class LoanProductAdmin(LenderRestrictedAdmin):
    form = LoanProductAdminForm
    list_display = ('name', 'min_amount', 'max_amount', 'interest_rate', 'is_active', 'lender')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


class CollateralAdmin(ImportExportModelAdmin):
    list_display = ('loan', 'collateral_type', 'description', 'estimated_value')
    search_fields = ('loan__loan_number', 'description')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(loan__lender=request.user.lender)

    def save_model(self, request, obj, form, change):
        # Collateral doesn't have a direct lender field, so no lender assignment needed
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "loan" and not request.user.is_superuser:
            kwargs["queryset"] = Loan.objects.filter(lender=request.user.lender)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RepaymentScheduleAdmin(LenderRestrictedAdmin):
    list_display = ('loan', 'installment_number', 'due_date', 'total_due', 'status')
    list_filter = ('status', ('due_date', admin.DateFieldListFilter))
    search_fields = ('loan__loan_number',)
    ordering = ('due_date',)
    def get_queryset(self, request):
        # Skip parent class lender filtering to avoid FieldError
        qs = super(LenderRestrictedAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter via related loan → lender
        return qs.filter(loan__lender=request.user.lender)


class LoanPortfolioAdmin(LenderRestrictedAdmin):
    list_display = ("lender", "total_loans_outstanding", "total_principal_disbursed", "total_interest_earned", "active_loans_count", "portfolio_return_rate")
    readonly_fields = ("total_loans_outstanding", "total_principal_disbursed", "total_interest_earned", "total_repayments_received", "active_loans_count", "overdue_loans_count", "defaulted_loans_count", "average_loan_amount", "portfolio_return_rate", "delinquency_rate", "last_updated")
    search_fields = ("lender__name",)

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


# ===========================
# Registrations
# ===========================

custom_admin_site.register(Lender)
custom_admin_site.register(CustomUser, CustomUserAdmin)
custom_admin_site.register(Borrower, BorrowerAdmin)
custom_admin_site.register(LoanApplication, LoanApplicationAdmin)
custom_admin_site.register(Loan, LoanAdmin)
custom_admin_site.register(LoanRepayment, LoanRepaymentAdmin)
custom_admin_site.register(OperatingExpense, OperatingExpenseAdmin)
custom_admin_site.register(Staff, StaffAdmin)
custom_admin_site.register(BankAccount, BankAccountAdmin)
custom_admin_site.register(CashTransaction, CashTransactionAdmin)
custom_admin_site.register(BankTransaction, BankTransactionAdmin)
custom_admin_site.register(LoanProduct, LoanProductAdmin)
custom_admin_site.register(Collateral, CollateralAdmin)
custom_admin_site.register(RepaymentSchedule, RepaymentScheduleAdmin)
custom_admin_site.register(LoanPortfolio, LoanPortfolioAdmin)


# ===========================
# Custom Admin Views & URLs
# ===========================

# ===========================
# Custom Admin Views & URLs
# ===========================

from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.db.models import Sum
from django.urls import path
from django.template.response import TemplateResponse

# ---------------------------
# Forms
# ---------------------------
class DateRangeForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

# ---------------------------
# Member Contribution Views
# ---------------------------
def member_contribution_receipt(request):
    form = MemberContributionFilterForm(request.GET or None, user=request.user)
    contributions = []
    member = None
    total_contributions = 0

    if form.is_valid():
        member = form.cleaned_data['member']
        qs = Contribution.objects.filter(member=member)
        # Restrict by church
        if not request.user.is_superuser and hasattr(request.user, 'church'):
            qs = qs.filter(church=request.user.church)
        # Date filter
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        contributions = qs.order_by('date')
        total_contributions = qs.aggregate(Sum('amount'))['amount__sum'] or 0

    context = dict(
        custom_admin_site.each_context(request),
        title="Member Contribution Receipt",
        form=form,
        member=member,
        contributions=contributions,
        total_contributions=total_contributions,
    )
    return TemplateResponse(request, "admin/member_contribution_receipt.html", context)


def export_member_contribution_receipt(request):
    form = MemberContributionFilterForm(request.GET or None)
    if not form.is_valid():
        return HttpResponse("Invalid form input", status=400)

    member = form.cleaned_data['member']
    qs = Contribution.objects.filter(member=member)
    if not request.user.is_superuser and hasattr(request.user, 'church'):
        qs = qs.filter(church=request.user.church)
    start_date = form.cleaned_data.get('start_date')
    end_date = form.cleaned_data.get('end_date')
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    contributions = qs.order_by('date')

    # CSV response
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = f'attachment; filename="member_{member.id}_contributions.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Amount", "Type", "Notes"])
    for c in contributions:
        writer.writerow([c.date, c.amount, c.contribution_type, c.notes or ""])
    total = qs.aggregate(Sum('amount'))['amount__sum'] or 0
    writer.writerow([])
    writer.writerow(["Total", total])
    return response


def member_contribution_receipt_pdf(request):
    # Initialize form with GET data - don't restrict member queryset for PDF export
    form = MemberContributionFilterForm(request.GET or None)
    contributions = []
    member = None
    total_contributions = 0
    church_name = ""
    start_date = None
    end_date = None

    if form.is_valid():
        member = form.cleaned_data['member']
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        qs = Contribution.objects.filter(member=member)

        # Restrict by church
        if not request.user.is_superuser and hasattr(request.user, 'church'):
            qs = qs.filter(church=request.user.church)
            church_name = request.user.church.name
        elif hasattr(member, 'church') and member.church:
            church_name = member.church.name

        # Filter by date range
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        contributions = qs.order_by('date')
        total_contributions = qs.aggregate(Sum('amount'))['amount__sum'] or 0

    # Ensure church_name is set from member if not already
    if not church_name and member and hasattr(member, 'church') and member.church:
        church_name = member.church.name

    # Render HTML template
    html_string = render_to_string("admin/member_contribution_receipt_pdf.html", {
        "member": member,
        "contributions": contributions,
        "total_contributions": total_contributions,
        "church_name": church_name,
        "start_date": start_date,
        "end_date": end_date,
    })

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"{member.full_name}_contributions.pdf" if member else "member_contributions.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response



# ---------------------------
# Income & Expenditure Views
# ---------------------------
# def income_expenditure_view(request):
#     form = DateRangeForm(request.GET or None)
#     qs_contributions = Contribution.objects.all()
#     qs_group_contributions = GroupContribution.objects.all()
#     qs_donations = Donation.objects.all()
#     qs_expenses = Expense.objects.all()

#     if not request.user.is_superuser and hasattr(request.user, 'church'):
#         qs_contributions = qs_contributions.filter(church=request.user.church)
#         qs_group_contributions = qs_group_contributions.filter(church=request.user.church)
#         qs_donations = qs_donations.filter(church=request.user.church)
#         qs_expenses = qs_expenses.filter(church=request.user.church)

#     if form.is_valid():
#         start_date = form.cleaned_data.get('start_date')
#         end_date = form.cleaned_data.get('end_date')
#         if start_date:
#             qs_contributions = qs_contributions.filter(date__gte=start_date)
#             qs_group_contributions = qs_group_contributions.filter(date__gte=start_date)
#             qs_donations = qs_donations.filter(date__gte=start_date)
#             qs_expenses = qs_expenses.filter(date__gte=start_date)
#         if end_date:
#             qs_contributions = qs_contributions.filter(date__lte=end_date)
#             qs_group_contributions = qs_group_contributions.filter(date__lte=end_date)
#             qs_donations = qs_donations.filter(date__lte=end_date)
#             qs_expenses = qs_expenses.filter(date__lte=end_date)

#     total_contributions = qs_contributions.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_group_contributions = qs_group_contributions.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_donations = qs_donations.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_income = total_contributions + total_group_contributions + total_donations
#     total_expense = qs_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
#     balance = total_income - total_expense

#     context = dict(
#         custom_admin_site.each_context(request),
#         title="Income & Expenditure Statement",
#         form=form,
#         total_contributions=total_contributions,
#         total_group_contributions=total_group_contributions,
#         total_donations=total_donations,
#         total_income=total_income,
#         total_expense=total_expense,
#         balance=balance,
#     )
#     return TemplateResponse(request, "admin/income_expenditure.html", context)


# def export_income_expenditure(request):
#     qs_contributions = Contribution.objects.all()
#     qs_group_contributions = GroupContribution.objects.all()
#     qs_donations = Donation.objects.all()
#     qs_expenses = Expense.objects.all()

#     if not request.user.is_superuser and hasattr(request.user, 'church'):
#         qs_contributions = qs_contributions.filter(church=request.user.church)
#         qs_group_contributions = qs_group_contributions.filter(church=request.user.church)
#         qs_donations = qs_donations.filter(church=request.user.church)
#         qs_expenses = qs_expenses.filter(church=request.user.church)

#     total_contributions = qs_contributions.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_group_contributions = qs_group_contributions.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_donations = qs_donations.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_income = total_contributions + total_group_contributions + total_donations
#     total_expense = qs_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
#     balance = total_income - total_expense

#     response = HttpResponse(content_type="text/csv")
#     response['Content-Disposition'] = 'attachment; filename="income_expenditure.csv"'
#     writer = csv.writer(response)
#     writer.writerow(["Member Contributions", total_contributions])
#     writer.writerow(["Group Contributions", total_group_contributions])
#     writer.writerow(["Donations", total_donations])
#     writer.writerow(["Total Income", total_income])
#     writer.writerow(["Total Expense", total_expense])
#     writer.writerow(["Balance", balance])
#     return response


# def income_expenditure_pdf(request):
#     form = DateRangeForm(request.GET or None)
#     qs_contributions = Contribution.objects.all()
#     qs_group_contributions = GroupContribution.objects.all()
#     qs_donations = Donation.objects.all()
#     qs_expenses = Expense.objects.all()

#     church_name = ""
#     if not request.user.is_superuser and hasattr(request.user, 'church'):
#         qs_contributions = qs_contributions.filter(church=request.user.church)
#         qs_group_contributions = qs_group_contributions.filter(church=request.user.church)
#         qs_donations = qs_donations.filter(church=request.user.church)
#         qs_expenses = qs_expenses.filter(church=request.user.church)
#         church_name = request.user.church.name

#     if form.is_valid():
#         start_date = form.cleaned_data.get('start_date')
#         end_date = form.cleaned_data.get('end_date')
#         if start_date:
#             qs_contributions = qs_contributions.filter(date__gte=start_date)
#             qs_group_contributions = qs_group_contributions.filter(date__gte=start_date)
#             qs_donations = qs_donations.filter(date__gte=start_date)
#             qs_expenses = qs_expenses.filter(date__gte=start_date)
#         if end_date:
#             qs_contributions = qs_contributions.filter(date__lte=end_date)
#             qs_group_contributions = qs_group_contributions.filter(date__lte=end_date)
#             qs_donations = qs_donations.filter(date__lte=end_date)
#             qs_expenses = qs_expenses.filter(date__lte=end_date)

#     total_contributions = qs_contributions.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_group_contributions = qs_group_contributions.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_donations = qs_donations.aggregate(Sum('amount'))['amount__sum'] or 0
#     total_income = total_contributions + total_group_contributions + total_donations
#     total_expense = qs_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
#     balance = total_income - total_expense

#     # Render HTML template
#     html_string = render_to_string("admin/income_expenditure_pdf.html", {
#         "total_contributions": total_contributions,
#         "total_group_contributions": total_group_contributions,
#         "total_donations": total_donations,
#         "total_income": total_income,
#         "total_expense": total_expense,
#         "balance": balance,
#         "church_name": church_name,
#         "start_date": form.cleaned_data.get('start_date') if form.is_valid() else None,
#         "end_date": form.cleaned_data.get('end_date') if form.is_valid() else None,
#     })

#     # Generate PDF
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="income_expenditure.pdf"'

#     pisa_status = pisa.CreatePDF(html_string, dest=response)
#     if pisa_status.err:
#         return HttpResponse("Error generating PDF", status=500)
#     return response


# # ---------------------------
# # Add Custom URLs to Admin
# # ---------------------------
# def _add_custom_admin_urls(urls):
#     my_urls = [
#         # Income & Expenditure
#         path(
#             "reports/financial/income-expenditure/",
#             custom_admin_site.admin_view(income_expenditure_view),
#             name="income_expenditure"
#         ),
#         path(
#             "reports/financial/income-expenditure/export/",
#             custom_admin_site.admin_view(export_income_expenditure),
#             name="export_income_expenditure"
#         ),
#         path(
#             "reports/financial/income-expenditure/pdf/",
#             custom_admin_site.admin_view(income_expenditure_pdf),
#             name="income_expenditure_pdf"
#         ),
#         # Member Contribution Receipt
#         path(
#             "reports/contributions/member-receipt/",
#             custom_admin_site.admin_view(member_contribution_receipt),
#             name="member_contribution_receipt"
#         ),
#         path(
#             "reports/contributions/member-receipt/export/",
#             custom_admin_site.admin_view(export_member_contribution_receipt),
#             name="export_member_contribution_receipt"
#         ),
#         path(
#             "reports/contributions/member-receipt/pdf/",
#             custom_admin_site.admin_view(member_contribution_receipt_pdf),
#             name="member_contribution_receipt_pdf"
#         ),
#     ]
#     return my_urls + urls

# Custom view for loans dashboard
def loans_dashboard(request):
    """Custom dashboard view for loans app"""
    # Get lender
    lender = None
    if not request.user.is_superuser and hasattr(request.user, 'lender'):
        lender = request.user.lender

    import datetime
    from django.db.models import Sum

    now = datetime.datetime.now()
    year = now.year

    # Monthly loan performance
    disbursement_data = []
    repayment_data = []
    months = []
    for month in range(1, 13):
        month_start = datetime.date(year, month, 1)
        if month == 12:
            month_end = datetime.date(year+1, 1, 1) - datetime.timedelta(days=1)
        else:
            month_end = datetime.date(year, month+1, 1) - datetime.timedelta(days=1)

        months.append(month_start.strftime('%b'))

        disbursements = Loan.objects.filter(lender=lender, disbursement_date__range=(month_start, month_end)).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0
        repayments = LoanRepayment.objects.filter(loan__lender=lender, payment_date__range=(month_start, month_end)).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

        disbursement_data.append(float(disbursements))
        repayment_data.append(float(repayments))

    # Loan status pie
    loan_statuses = Loan.objects.filter(lender=lender).values('status').annotate(count=Sum('principal_amount')).order_by('-count')

    # Borrower count
    borrower_count = Borrower.objects.filter(lender=lender).count()

    # Additional loan metrics
    total_loans_outstanding = Loan.objects.filter(
        lender=lender,
        status__in=['ACTIVE', 'PENDING_DISBURSEMENT']
    ).aggregate(Sum('outstanding_balance'))['outstanding_balance__sum'] or 0

    total_principal_disbursed = Loan.objects.filter(
        lender=lender,
        status__in=['ACTIVE', 'PAID_OFF']
    ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

    total_repayments_received = LoanRepayment.objects.filter(
        loan__lender=lender
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

    total_interest_earned = LoanRepayment.objects.filter(
        loan__lender=lender
    ).aggregate(Sum('interest_paid'))['interest_paid__sum'] or 0

    total_operating_expenses = OperatingExpense.objects.filter(
        lender=lender
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Loan status counts
    active_loans = Loan.objects.filter(lender=lender, status='ACTIVE').count()
    pending_loans = Loan.objects.filter(lender=lender, status='PENDING_DISBURSEMENT').count()
    paid_off_loans = Loan.objects.filter(lender=lender, status='PAID_OFF').count()
    defaulted_loans = Loan.objects.filter(lender=lender, status='DEFAULTED').count()

    # Recent activity (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.datetime.now() - timedelta(days=30)

    recent_applications = LoanApplication.objects.filter(
        lender=lender,
        application_date__gte=thirty_days_ago
    ).count()

    recent_disbursements = Loan.objects.filter(
        lender=lender,
        disbursement_date__gte=thirty_days_ago
    ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

    recent_repayments = LoanRepayment.objects.filter(
        loan__lender=lender,
        payment_date__gte=thirty_days_ago
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

    context = dict(
        custom_admin_site.each_context(request),
        title="Loans Dashboard",
        months_json=json.dumps(months),
        disbursement_data_json=json.dumps(disbursement_data),
        repayment_data_json=json.dumps(repayment_data),
        loan_labels_json=json.dumps([ls['status'] for ls in loan_statuses]),
        loan_data_json=json.dumps([float(ls['count']) for ls in loan_statuses]),
        borrower_count=borrower_count,
        total_loans_outstanding=total_loans_outstanding,
        total_principal_disbursed=total_principal_disbursed,
        total_repayments_received=total_repayments_received,
        total_interest_earned=total_interest_earned,
        total_operating_expenses=total_operating_expenses,
        active_loans=active_loans,
        pending_loans=pending_loans,
        paid_off_loans=paid_off_loans,
        defaulted_loans=defaulted_loans,
        recent_applications=recent_applications,
        recent_disbursements=recent_disbursements,
        recent_repayments=recent_repayments,
    )
    # return TemplateResponse(request, "admin/index.html", context)
    return TemplateResponse(request, "admin/loans_dashboard.html", context)



# Add custom URL for loans dashboard
def _add_loans_dashboard_url(urls):
    from django.urls import path
    my_urls = [
        path('loans/', custom_admin_site.admin_view(loans_dashboard), name='loans_dashboard'),
    ]
    return my_urls + urls

# Hook into admin URLs
_original_get_urls = custom_admin_site.get_urls
custom_admin_site.get_urls = lambda: _add_loans_dashboard_url(_original_get_urls())
