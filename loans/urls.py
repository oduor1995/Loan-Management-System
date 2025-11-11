from django.urls import path
from . import views
from .views import RecordLoanRepaymentView

app_name = 'members'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('borrowers/', views.borrower_management, name='borrower_management'),
    path('portfolio/', views.loan_portfolio_overview, name='loan_portfolio_overview'),
    path('api/record-repayment/', RecordLoanRepaymentView.as_view(), name='record_loan_repayment'),
    

    # Loan Management URLs
    path('applications/', views.loan_applications, name='loan_applications'),
    path('applications/<int:pk>/', views.loan_application_detail, name='loan_application_detail'),
    path('loans/', views.loans_list, name='loans_list'),
    path('loans/<int:pk>/', views.loan_detail, name='loan_detail'),
    path('loans/<int:pk>/disburse/', views.disburse_loan, name='disburse_loan'),

    # Legacy Marketplace URLs (to be removed)
    # path('marketplace/', views.marketplace_home, name='marketplace_home'),
    # path('marketplace/listing/<int:pk>/', views.marketplace_listing_detail, name='marketplace_listing_detail'),
    # path('marketplace/my-listings/', views.marketplace_my_listings, name='marketplace_my_listings'),
    # path('marketplace/create/', views.marketplace_create_listing, name='marketplace_create_listing'),
    # path('marketplace/edit/<int:pk>/', views.marketplace_edit_listing, name='marketplace_edit_listing'),
    # path('marketplace/delete/<int:pk>/', views.marketplace_delete_listing, name='marketplace_delete_listing'),
    # path('marketplace/review/<int:pk>/', views.marketplace_add_review, name='marketplace_add_review'),
]
