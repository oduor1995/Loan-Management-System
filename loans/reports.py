from django.db.models import Sum
from slick_reporting.views import SlickReportView
from slick_reporting.fields import SlickReportField
from .models import LoanRepayment, OperatingExpense, Loan


class LoanPerformanceReport(SlickReportView):
    report_model = LoanRepayment
    date_field = "payment_date"
    group_by = "payment_date"

    columns = [
        SlickReportField.create(
            field="amount_paid",
            name="total_repayments",
            verbose_name="Total Repayments",
            method=Sum,
        ),
        SlickReportField.create(
            field="principal_paid",
            name="principal_repaid",
            verbose_name="Principal Repaid",
            method=Sum,
        ),
        SlickReportField.create(
            field="interest_paid",
            name="interest_earned",
            verbose_name="Interest Earned",
            method=Sum,
        ),
    ]

    chart_settings = [
        {
            "type": "line",
            "data_source": ["total_repayments", "principal_repaid", "interest_earned"],
            "title_source": "Loan Performance Over Time",
        }
    ]


class ExpenseReport(SlickReportView):
    report_model = OperatingExpense
    date_field = "date"
    group_by = "category"

    columns = [
        SlickReportField.create(
            field="amount",
            name="total_expenses",
            verbose_name="Total Expenses",
            method=Sum,
        ),
    ]

    chart_settings = [
        {
            "type": "pie",
            "data_source": ["total_expenses"],
            "title_source": "Expenses by Category",
        }
    ]
