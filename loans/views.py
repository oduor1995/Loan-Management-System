from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Borrower, LoanApplication, Loan, LoanRepayment, Collateral, OperatingExpense, LoanProduct, LoanPortfolio, LoanCalculator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Borrower
from .serializers import LoanRepaymentSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from .models import Loan, LoanRepayment, OperatingExpense
from django.urls import reverse
from decimal import Decimal
from datetime import date

# ----------------- Dashboard Home -----------------
@login_required
def dashboard_home(request):
    user_lender = request.user.lender

    # Core loan metrics
    total_borrowers = Borrower.objects.filter(lender=user_lender).count()
    total_loans_outstanding = Loan.objects.filter(
        lender=user_lender,
        status__in=['ACTIVE', 'PENDING_DISBURSEMENT']
    ).aggregate(Sum('outstanding_balance'))['outstanding_balance__sum'] or 0

    # Financial performance
    total_principal_disbursed = Loan.objects.filter(
        lender=user_lender,
        status__in=['ACTIVE', 'PAID_OFF']
    ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

    total_repayments_received = LoanRepayment.objects.filter(
        loan__lender=user_lender
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

    total_interest_earned = LoanRepayment.objects.filter(
        loan__lender=user_lender
    ).aggregate(Sum('interest_paid'))['interest_paid__sum'] or 0

    total_operating_expenses = OperatingExpense.objects.filter(
        lender=user_lender
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Loan status breakdown
    active_loans = Loan.objects.filter(lender=user_lender, status='ACTIVE').count()
    pending_loans = Loan.objects.filter(lender=user_lender, status='PENDING_DISBURSEMENT').count()
    paid_off_loans = Loan.objects.filter(lender=user_lender, status='PAID_OFF').count()
    defaulted_loans = Loan.objects.filter(lender=user_lender, status='DEFAULTED').count()

    # Recent activity (last 30 days)
    from datetime import timedelta
    thirty_days_ago = date.today() - timedelta(days=30)

    recent_applications = LoanApplication.objects.filter(
        lender=user_lender,
        application_date__gte=thirty_days_ago
    ).count()

    recent_disbursements = Loan.objects.filter(
        lender=user_lender,
        disbursement_date__gte=thirty_days_ago
    ).aggregate(Sum('principal_amount'))['principal_amount__sum'] or 0

    recent_repayments = LoanRepayment.objects.filter(
        loan__lender=user_lender,
        payment_date__gte=thirty_days_ago
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

    # Calculate key ratios
    net_profit = total_interest_earned - total_operating_expenses
    repayment_rate = (total_repayments_received / total_principal_disbursed * 100) if total_principal_disbursed > 0 else 0

    context = {
        # Core metrics
        'total_borrowers': total_borrowers,
        'total_loans_outstanding': total_loans_outstanding,
        'total_principal_disbursed': total_principal_disbursed,

        # Financial performance
        'total_repayments_received': total_repayments_received,
        'total_interest_earned': total_interest_earned,
        'total_operating_expenses': total_operating_expenses,
        'net_profit': net_profit,

        # Loan status breakdown
        'active_loans': active_loans,
        'pending_loans': pending_loans,
        'paid_off_loans': paid_off_loans,
        'defaulted_loans': defaulted_loans,

        # Recent activity
        'recent_applications': recent_applications,
        'recent_disbursements': recent_disbursements,
        'recent_repayments': recent_repayments,

        # Key ratios
        'repayment_rate': round(repayment_rate, 2),
    }
    return render(request, 'members/dashboard_home.html', context)

# ----------------- Borrower Management -----------------
@login_required
def borrower_management(request):
    user_lender = request.user.lender
    borrowers = Borrower.objects.filter(lender=user_lender)
    context = {
        'borrowers': borrowers
    }
    return render(request, 'members/borrower_management.html', context)

# ----------------- Loan Portfolio & Financial Overview -----------------
@login_required
def loan_portfolio_overview(request):
    user_lender = request.user.lender

    # Get portfolio data
    portfolio, created = LoanPortfolio.objects.get_or_create(lender=user_lender)

    # Current period calculations
    current_month = date.today().replace(day=1)
    next_month = current_month.replace(month=current_month.month + 1) if current_month.month < 12 else current_month.replace(year=current_month.year + 1, month=1)

    monthly_repayments = LoanRepayment.objects.filter(
        loan__lender=user_lender,
        payment_date__range=(current_month, next_month)
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0

    monthly_expenses = OperatingExpense.objects.filter(
        lender=user_lender,
        date__range=(current_month, next_month)
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Loan status breakdown
    active_loans = Loan.objects.filter(lender=user_lender, status='ACTIVE').count()
    pending_loans = Loan.objects.filter(lender=user_lender, status='PENDING_DISBURSEMENT').count()
    defaulted_loans = Loan.objects.filter(lender=user_lender, status='DEFAULTED').count()

    context = {
        'portfolio': portfolio,
        'monthly_repayments': monthly_repayments,
        'monthly_expenses': monthly_expenses,
        'active_loans': active_loans,
        'pending_loans': pending_loans,
        'defaulted_loans': defaulted_loans,
    }
    return render(request, 'members/loan_portfolio_overview.html', context)

@csrf_exempt
@api_view(['POST'])
def record_loan_repayment(request):
    """
    POST JSON:
    {
        "loan_number": "LN12345678",
        "amount_paid": 1500.00,
        "payment_method": "CASH",
        "reference_number": "REF001",
        "notes": "Monthly repayment"
    }
    """
    serializer = LoanRepaymentSerializer(data=request.data)
    if serializer.is_valid():
        repayment = serializer.save()

        # Update loan outstanding balance
        loan = repayment.loan
        loan.outstanding_balance -= repayment.principal_paid
        loan.total_repaid += repayment.amount_paid
        loan.save()

        # Update borrower repayment history
        borrower = repayment.borrower
        borrower.total_repaid += repayment.amount_paid
        borrower.outstanding_balance -= repayment.principal_paid
        borrower.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecordLoanRepaymentView(APIView):
    authentication_classes = []  # disables authentication
    permission_classes = []       # disables permissions

    def post(self, request, *args, **kwargs):
        serializer = LoanRepaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===========================
# Loan Management Views
# ===========================

@login_required
def loan_applications(request):
    """View and manage loan applications"""
    user_lender = request.user.lender
    applications = LoanApplication.objects.filter(lender=user_lender).select_related('borrower').order_by('-application_date')

    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    context = {
        'applications': applications,
        'status_filter': status_filter,
    }
    return render(request, 'members/loan_applications.html', context)


@login_required
def loan_application_detail(request, pk):
    """Detailed view of a loan application"""
    user_lender = request.user.lender
    application = get_object_or_404(LoanApplication, pk=pk, lender=user_lender)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            application.status = 'APPROVED'
            application.reviewed_by = request.user.staff_profile
            application.reviewed_date = date.today()
            application.save()

            # Create loan from application
            loan = Loan.objects.create(
                lender=user_lender,
                borrower=application.borrower,
                application=application,
                principal_amount=application.requested_amount,
                loan_term_months=application.loan_term_months,
                # Other fields will be set during disbursement
            )
            messages.success(request, f'Application approved. Loan {loan.loan_number} created.')
        elif action == 'reject':
            application.status = 'REJECTED'
            application.reviewed_by = request.user.staff_profile
            application.reviewed_date = date.today()
            application.review_notes = request.POST.get('review_notes')
            application.save()
            messages.success(request, 'Application rejected.')

        return redirect('members:loan_applications')

    context = {
        'application': application,
    }
    return render(request, 'members/loan_application_detail.html', context)


@login_required
def loans_list(request):
    """View all loans"""
    user_lender = request.user.lender
    loans = Loan.objects.filter(lender=user_lender).select_related('borrower').order_by('-disbursement_date')

    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        loans = loans.filter(status=status_filter)

    context = {
        'loans': loans,
        'status_filter': status_filter,
    }
    return render(request, 'members/loans_list.html', context)


@login_required
def loan_detail(request, pk):
    """Detailed view of a loan"""
    user_lender = request.user.lender
    loan = get_object_or_404(Loan, pk=pk, lender=user_lender)

    # Get repayment schedule
    schedule = loan.repayment_schedule.all().order_by('due_date')

    # Get repayments
    repayments = loan.repayments.all().order_by('-payment_date')

    # Calculate loan calculator data
    if loan.status == 'ACTIVE':
        calculator = LoanCalculator()
        monthly_payment = calculator.calculate_monthly_payment(
            float(loan.principal_amount),
            float(loan.interest_rate),
            loan.loan_term_months
        )
    else:
        monthly_payment = 0

    context = {
        'loan': loan,
        'schedule': schedule,
        'repayments': repayments,
        'monthly_payment': monthly_payment,
    }
    return render(request, 'members/loan_detail.html', context)


@login_required
def disburse_loan(request, pk):
    """Disburse a loan"""
    user_lender = request.user.lender
    loan = get_object_or_404(Loan, pk=pk, lender=user_lender, status='PENDING_DISBURSEMENT')

    if request.method == 'POST':
        # Update loan details
        loan.interest_rate = Decimal(request.POST.get('interest_rate'))
        loan.disbursement_date = date.today()
        loan.first_payment_date = date.today()  # Will be calculated properly
        loan.status = 'ACTIVE'
        loan.disbursed_by = request.user.staff_profile
        loan.outstanding_balance = loan.principal_amount

        # Calculate total interest and maturity date
        calculator = LoanCalculator()
        if loan.interest_type == 'SIMPLE':
            loan.total_interest = calculator.calculate_simple_interest(
                float(loan.principal_amount),
                float(loan.interest_rate),
                loan.loan_term_months
            )
        else:
            # For compound interest, calculate total payments
            monthly_payment = calculator.calculate_monthly_payment(
                float(loan.principal_amount),
                float(loan.interest_rate),
                loan.loan_term_months
            )
            loan.total_interest = (monthly_payment * loan.loan_term_months) - float(loan.principal_amount)

        loan.maturity_date = loan.disbursement_date  # Will be calculated properly
        loan.save()

        # Generate repayment schedule
        schedule_data = calculator.generate_repayment_schedule(loan)
        for item in schedule_data:
            from .models import RepaymentSchedule
            RepaymentSchedule.objects.create(
                loan=loan,
                installment_number=item['installment_number'],
                due_date=item['due_date'],
                principal_due=item['principal_due'],
                interest_due=item['interest_due'],
                total_due=item['total_due'],
            )

        # Update borrower loan history
        borrower = loan.borrower
        borrower.total_loans_taken += loan.principal_amount
        borrower.outstanding_balance += loan.principal_amount
        borrower.save()

        messages.success(request, f'Loan {loan.loan_number} has been disbursed successfully.')
        return redirect('members:loan_detail', pk=loan.pk)

    context = {
        'loan': loan,
    }
    return render(request, 'members/disburse_loan.html', context)


# ===========================
# Marketplace Views (keeping for now, but will be removed later)
# ===========================

@login_required
def marketplace_home(request):
    """Main marketplace page - browse listings"""
    user_church = request.user.church

    # Get active listings for user's church
    listings = BusinessListing.objects.filter(
        church=user_church,
        status='ACTIVE'
    ).select_related('member', 'category').prefetch_related('images')

    # Apply filters
    category_id = request.GET.get('category')
    if category_id:
        listings = listings.filter(category_id=category_id)

    search_query = request.GET.get('q')
    if search_query:
        listings = listings.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(business_type__icontains=search_query) |
            Q(member__full_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(listings, 12)  # 12 listings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter
    categories = BusinessCategory.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
    }
    return render(request, 'members/marketplace/marketplace_home.html', context)


@login_required
def marketplace_listing_detail(request, pk):
    """Detailed view of a business listing"""
    user_church = request.user.church

    listing = get_object_or_404(
        BusinessListing,
        pk=pk,
        church=user_church,
        status='ACTIVE'
    )

    # Increment view count
    listing.views_count += 1
    listing.save(update_fields=['views_count'])

    # Get related listings (same category, different listing)
    related_listings = BusinessListing.objects.filter(
        church=user_church,
        status='ACTIVE',
        category=listing.category
    ).exclude(pk=listing.pk)[:4]

    # Get reviews
    reviews = BusinessReview.objects.filter(
        listing=listing,
        is_approved=True
    ).select_related('reviewer').order_by('-created_at')

    # Check if user can review (hasn't reviewed before)
    can_review = not reviews.filter(reviewer__user=request.user).exists()

    context = {
        'listing': listing,
        'related_listings': related_listings,
        'reviews': reviews,
        'can_review': can_review,
        'average_rating': reviews.aggregate(avg_rating=Sum('rating'))['avg_rating'] or 0,
    }
    return render(request, 'members/marketplace/listing_detail.html', context)


@login_required
def marketplace_my_listings(request):
    """Member's own business listings management"""
    user_church = request.user.church

    # Get or create member profile for the user
    member, created = Member.objects.get_or_create(
        user=request.user,
        defaults={
            'church': user_church,
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': '',  # Will need to be filled later
            'email': request.user.email,
        }
    )

    # Ensure member has church association
    if member.church is None:
        member.church = user_church
        member.save()

    # Get member's listings
    listings = BusinessListing.objects.filter(
        member=member
    ).select_related('category').prefetch_related('images').order_by('-created_at')

    context = {
        'listings': listings,
    }
    return render(request, 'members/marketplace/my_listings.html', context)


@login_required
def marketplace_create_listing(request):
    """Create a new business listing"""
    user_church = request.user.church

    if not user_church:
        messages.error(request, 'You must be associated with a church to create business listings.')
        return redirect('members:dashboard_home')

    # Get or create member profile for the user
    member, created = Member.objects.get_or_create(
        user=request.user,
        defaults={
            'church': user_church,
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': '',  # Will need to be filled later
            'email': request.user.email,
        }
    )

    # Ensure member has church association
    if member.church is None:
        member.church = user_church
        member.save()

    if request.method == 'POST':
        # Handle form submission
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        business_type = request.POST.get('business_type')

        # Create listing
        listing = BusinessListing.objects.create(
            church=user_church,
            member=member,
            title=title,
            description=description,
            category_id=category_id,
            business_type=business_type,
            contact_phone=request.POST.get('contact_phone'),
            contact_email=request.POST.get('contact_email'),
            website=request.POST.get('website'),
            location=request.POST.get('location'),
            service_area=request.POST.get('service_area'),
            established_year=request.POST.get('established_year') or None,
            employee_count=request.POST.get('employee_count'),
            price_range=request.POST.get('price_range'),
            services_offered=request.POST.get('services_offered'),
            status='PENDING'  # Requires admin approval
        )

        # Handle image uploads
        images = request.FILES.getlist('images')
        for i, image in enumerate(images[:5]):  # Max 5 images
            BusinessImage.objects.create(
                listing=listing,
                image=image,
                is_primary=(i == 0)  # First image is primary
            )

        messages.success(request, 'Your business listing has been submitted for approval.')
        return redirect('members:marketplace_my_listings')

    # GET request - show form
    categories = BusinessCategory.objects.filter(is_active=True)

    context = {
        'categories': categories,
    }
    return render(request, 'members/marketplace/create_listing.html', context)


@login_required
def marketplace_edit_listing(request, pk):
    """Edit an existing business listing"""
    user_church = request.user.church

    # Get or create member profile for the user
    member, created = Member.objects.get_or_create(
        user=request.user,
        defaults={
            'church': user_church,
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': '',  # Will need to be filled later
            'email': request.user.email,
        }
    )

    # Ensure member has church association
    if member.church is None:
        member.church = user_church
        member.save()

    listing = get_object_or_404(
        BusinessListing,
        pk=pk,
        member=member
    )

    if request.method == 'POST':
        # Update listing
        listing.title = request.POST.get('title')
        listing.description = request.POST.get('description')
        listing.category_id = request.POST.get('category')
        listing.business_type = request.POST.get('business_type')
        listing.contact_phone = request.POST.get('contact_phone')
        listing.contact_email = request.POST.get('contact_email')
        listing.website = request.POST.get('website')
        listing.location = request.POST.get('location')
        listing.service_area = request.POST.get('service_area')
        listing.established_year = request.POST.get('established_year') or None
        listing.employee_count = request.POST.get('employee_count')
        listing.price_range = request.POST.get('price_range')
        listing.services_offered = request.POST.get('services_offered')
        listing.save()

        # Handle new image uploads
        images = request.FILES.getlist('images')
        for image in images[:5]:  # Max 5 additional images
            BusinessImage.objects.create(
                listing=listing,
                image=image,
                is_primary=False
            )

        messages.success(request, 'Your business listing has been updated.')
        return redirect('members:marketplace_my_listings')

    categories = BusinessCategory.objects.filter(is_active=True)

    context = {
        'listing': listing,
        'categories': categories,
    }
    return render(request, 'members/marketplace/edit_listing.html', context)


@login_required
def marketplace_delete_listing(request, pk):
    """Delete a business listing"""
    user_church = request.user.church

    # Get or create member profile for the user
    member, created = Member.objects.get_or_create(
        church=user_church,
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': '',  # Will need to be filled later
            'email': request.user.email,
        }
    )

    # Ensure member has church association
    if member.church is None:
        member.church = user_church
        member.save()

    listing = get_object_or_404(
        BusinessListing,
        pk=pk,
        member=member
    )

    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Your business listing has been deleted.')
        return redirect('members:marketplace_my_listings')

    context = {
        'listing': listing,
    }
    return render(request, 'members/marketplace/delete_listing.html', context)


@login_required
def marketplace_add_review(request, pk):
    """Add a review to a business listing"""
    user_church = request.user.church

    # Get or create member profile for the user
    member, created = Member.objects.get_or_create(
        church=user_church,
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': '',  # Will need to be filled later
            'email': request.user.email,
        }
    )

    # Ensure member has church association
    if member.church is None:
        member.church = user_church
        member.save()

    listing = get_object_or_404(
        BusinessListing,
        pk=pk,
        church=user_church,
        status='ACTIVE'
    )

    # Check if user already reviewed
    if BusinessReview.objects.filter(listing=listing, reviewer=member).exists():
        messages.error(request, 'You have already reviewed this business.')
        return redirect('members:marketplace_listing_detail', pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        BusinessReview.objects.create(
            listing=listing,
            reviewer=member,
            rating=rating,
            comment=comment,
            is_approved=True  # Auto-approve for now
        )

        messages.success(request, 'Your review has been added.')
        return redirect('members:marketplace_listing_detail', pk=pk)

    context = {
        'listing': listing,
    }
    return render(request, 'members/marketplace/add_review.html', context)
