from django.test import TestCase
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from loans.models import Borrower, Loan, Lender, CustomUser, LoanRepayment, LoanCalculator, Staff
from loans.admin import LoanAdmin, CustomUserAdmin, StaffAdmin, custom_admin_site
from decimal import Decimal
from datetime import date


class LoanAdminTestCase(TestCase):
    def setUp(self):
        # Create a lender
        self.lender = Lender.objects.create(name="Test Lender", address="123 Test St", contact_email="test@lender.com")

        # Create a borrower
        self.borrower = Borrower.objects.create(
            lender=self.lender,
            full_name="John Doe",
            phone="1234567890",
            borrower_id="B001"
        )

        # Create a superuser
        self.superuser = CustomUser.objects.create_superuser('admin', 'admin@test.com', 'password')

        # Create a regular user with lender
        self.regular_user = CustomUser.objects.create_user('user', 'user@test.com', 'password')
        self.regular_user.lender = self.lender
        self.regular_user.save()

        # Create LoanAdmin instance
        self.loan_admin = LoanAdmin(Loan, None)

        # Request factory
        self.factory = RequestFactory()

    def test_save_model_valid_borrower_superuser(self):
        """Test that superuser can save loan with valid borrower"""
        request = self.factory.post('/')
        request.user = self.superuser

        loan = Loan(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=1000.00,
            interest_rate=10.00,
            loan_term_months=12
        )

        # Should not raise ValidationError
        self.loan_admin.save_model(request, loan, None, False)

    def test_save_model_valid_borrower_regular_user(self):
        """Test that regular user can save loan with valid borrower from their lender"""
        request = self.factory.post('/')
        request.user = self.regular_user

        loan = Loan(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=1000.00,
            interest_rate=10.00,
            loan_term_months=12
        )

        # Should not raise ValidationError
        self.loan_admin.save_model(request, loan, None, False)

    def test_save_model_none_borrower(self):
        """Test that saving loan with None borrower raises ValidationError"""
        request = self.factory.post('/')
        request.user = self.superuser

        loan = Loan(
            lender=self.lender,
            borrower_id=None,
            principal_amount=1000.00,
            interest_rate=10.00,
            loan_term_months=12
        )

        with self.assertRaises(ValidationError) as cm:
            self.loan_admin.save_model(request, loan, None, False)

        self.assertIn("Borrower is required.", str(cm.exception))

    def test_save_model_invalid_borrower_id(self):
        """Test that saving loan with non-existent borrower ID raises ValidationError"""
        request = self.factory.post('/')
        request.user = self.superuser

        # Create a loan instance with an invalid borrower ID
        loan = Loan(
            lender=self.lender,
            borrower_id=99999,  # Invalid ID
            principal_amount=1000.00,
            interest_rate=10.00,
            loan_term_months=12
        )

        with self.assertRaises(ValidationError) as cm:
            self.loan_admin.save_model(request, loan, None, False)

        self.assertIn("The selected borrower does not exist.", str(cm.exception))

    def test_save_model_none_lender_superuser(self):
        """Test that saving loan with None lender for superuser raises ValidationError"""
        request = self.factory.post('/')
        request.user = self.superuser

        loan = Loan(
            lender=None,
            borrower=self.borrower,
            principal_amount=1000.00,
            interest_rate=10.00,
            loan_term_months=12
        )

        with self.assertRaises(ValidationError) as cm:
            self.loan_admin.save_model(request, loan, None, False)

        self.assertIn("Lender is required.", str(cm.exception))

    def test_save_model_invalid_lender(self):
        """Test that saving loan with non-existent lender raises ValidationError"""
        request = self.factory.post('/')
        request.user = self.superuser

        # Create a loan instance with an invalid lender
        loan = Loan(
            lender_id=99999,  # Invalid ID
            borrower=self.borrower,
            principal_amount=1000.00,
            interest_rate=10.00,
            loan_term_months=12
        )

        with self.assertRaises(ValidationError) as cm:
            self.loan_admin.save_model(request, loan, None, False)

        self.assertIn("The selected lender does not exist.", str(cm.exception))

    def test_save_model_auto_assign_lender_regular_user(self):
        """Test that regular user gets lender auto-assigned"""
        request = self.factory.post('/')
        request.user = self.regular_user

        loan = Loan(
            lender=None,  # No lender set initially
            borrower=self.borrower,
            principal_amount=1000.00,
            interest_rate=10.00,
            loan_term_months=12
        )

        # Should not raise ValidationError and lender should be assigned
        self.loan_admin.save_model(request, loan, None, False)


class CustomUserAdminTestCase(TestCase):
    def setUp(self):
        # Create lenders
        self.lender1 = Lender.objects.create(name="Lender 1", address="123 Test St", contact_email="lender1@test.com")
        self.lender2 = Lender.objects.create(name="Lender 2", address="456 Test St", contact_email="lender2@test.com")

        # Create users
        self.superuser = CustomUser.objects.create_superuser('admin', 'admin@test.com', 'password')

        self.user1 = CustomUser.objects.create_user('user1', 'user1@test.com', 'password')
        self.user1.lender = self.lender1
        self.user1.save()

        self.user2 = CustomUser.objects.create_user('user2', 'user2@test.com', 'password')
        self.user2.lender = self.lender2
        self.user2.save()

        self.user3 = CustomUser.objects.create_user('user3', 'user3@test.com', 'password')
        self.user3.lender = self.lender1
        self.user3.save()

        # Create CustomUserAdmin instance
        self.custom_user_admin = CustomUserAdmin(CustomUser, custom_admin_site)

        # Request factory
        self.factory = RequestFactory()

    def test_get_queryset_superuser(self):
        """Test that superuser can see all users"""
        request = self.factory.get('/')
        request.user = self.superuser

        qs = self.custom_user_admin.get_queryset(request)
        self.assertEqual(qs.count(), 4)  # superuser + 3 regular users

    def test_get_queryset_regular_user(self):
        """Test that regular user can only see users from their lender"""
        request = self.factory.get('/')
        request.user = self.user1

        qs = self.custom_user_admin.get_queryset(request)
        users = list(qs)
        self.assertEqual(len(users), 2)  # user1 and user3 (both lender1)
        self.assertIn(self.user1, users)
        self.assertIn(self.user3, users)
        self.assertNotIn(self.user2, users)  # user2 is lender2

    def test_save_model_auto_assign_lender(self):
        """Test that lender is auto-assigned when saving"""
        request = self.factory.post('/')
        request.user = self.user1

        new_user = CustomUser(username='newuser', email='new@test.com')
        # Don't set lender initially

        self.custom_user_admin.save_model(request, new_user, None, False)
        new_user.refresh_from_db()
        self.assertEqual(new_user.lender, self.lender1)
class LoanCalculatorTestCase(TestCase):
    def setUp(self):
        self.lender = Lender.objects.create(name="Test Lender", address="123 Test St", contact_email="test@lender.com")
        self.borrower = Borrower.objects.create(
            lender=self.lender,
            full_name="John Doe",
            phone="1234567890",
            borrower_id="B001"
        )

    def test_calculate_simple_interest_valid(self):
        """Test simple interest calculation with valid inputs"""
        interest = LoanCalculator.calculate_simple_interest(1000, 10, 12)
        expected = Decimal('100.00')  # 1000 * 0.10 * 1 = 100
        self.assertEqual(interest, expected)

    def test_calculate_simple_interest_zero_rate(self):
        """Test simple interest with zero rate"""
        interest = LoanCalculator.calculate_simple_interest(1000, 0, 12)
        self.assertEqual(interest, Decimal('0.00'))

    def test_calculate_simple_interest_invalid_principal(self):
        """Test simple interest with invalid principal"""
        with self.assertRaises(ValueError):
            LoanCalculator.calculate_simple_interest(0, 10, 12)
        with self.assertRaises(ValueError):
            LoanCalculator.calculate_simple_interest(-100, 10, 12)

    def test_calculate_simple_interest_invalid_rate(self):
        """Test simple interest with invalid rate"""
        with self.assertRaises(ValueError):
            LoanCalculator.calculate_simple_interest(1000, -5, 12)

    def test_calculate_simple_interest_invalid_months(self):
        """Test simple interest with invalid months"""
        with self.assertRaises(ValueError):
            LoanCalculator.calculate_simple_interest(1000, 10, 0)

    def test_calculate_monthly_payment_valid(self):
        """Test monthly payment calculation with valid inputs"""
        payment = LoanCalculator.calculate_monthly_payment(1000, 10, 12)
        self.assertGreater(payment, Decimal('0.00'))
        # Approximate check: should be around 87.92
        self.assertAlmostEqual(float(payment), 87.92, places=2)

    def test_calculate_monthly_payment_zero_rate(self):
        """Test monthly payment with zero rate"""
        payment = LoanCalculator.calculate_monthly_payment(1000, 0, 12)
        self.assertEqual(payment, Decimal('83.33'))

    def test_calculate_monthly_payment_invalid_inputs(self):
        """Test monthly payment with invalid inputs"""
        with self.assertRaises(ValueError):
            LoanCalculator.calculate_monthly_payment(0, 10, 12)
        with self.assertRaises(ValueError):
            LoanCalculator.calculate_monthly_payment(1000, -5, 12)
        with self.assertRaises(ValueError):
            LoanCalculator.calculate_monthly_payment(1000, 10, 0)

    def test_calculate_total_amount_payable(self):
        """Test total amount payable calculation"""
        total = LoanCalculator.calculate_total_amount_payable(1000, 10, 12)
        self.assertGreater(total, Decimal('1000.00'))
        # Should be monthly_payment * 12
        monthly = LoanCalculator.calculate_monthly_payment(1000, 10, 12)
        expected = monthly * 12
        self.assertEqual(total, expected)


class LoanModelTestCase(TestCase):
    def setUp(self):
        self.lender = Lender.objects.create(name="Test Lender", address="123 Test St", contact_email="test@lender.com")
        self.borrower = Borrower.objects.create(
            lender=self.lender,
            full_name="John Doe",
            phone="1234567890",
            borrower_id="B001"
        )

    def test_loan_save_simple_interest(self):
        """Test loan save with simple interest"""
        loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate=Decimal('10.00'),
            loan_term_months=12,
            interest_type='SIMPLE'
        )
        expected_interest = Decimal('100.00')  # 1000 * 0.10 * 1
        self.assertEqual(loan.total_interest, expected_interest)

    def test_loan_save_compound_interest(self):
        """Test loan save with compound interest"""
        loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate=Decimal('10.00'),
            loan_term_months=12,
            interest_type='COMPOUND'
        )
        # Should calculate approximate total interest
        monthly_payment = LoanCalculator.calculate_monthly_payment(1000, 10, 12)
        expected_total = monthly_payment * 12
        expected_interest = expected_total - Decimal('1000.00')
        self.assertEqual(loan.total_interest, expected_interest)

    def test_loan_save_invalid_parameters(self):
        """Test loan save with invalid parameters"""
        with self.assertRaises(ValueError):
            Loan.objects.create(
                lender=self.lender,
                borrower=self.borrower,
                principal_amount=Decimal('0.00'),
                interest_rate=Decimal('10.00'),
                loan_term_months=12
            )

    def test_loan_repayment_updates_total_interest_compound(self):
        """Test that repayments update total interest for compound loans"""
        loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate=Decimal('10.00'),
            loan_term_months=12,
            interest_type='COMPOUND',
            disbursement_date=date.today()
        )

        # Create a repayment
        repayment = LoanRepayment.objects.create(
            loan=loan,
            borrower=self.borrower,
            amount_paid=Decimal('100.00'),
            payment_date=date.today()
        )

        loan.refresh_from_db()
        # total_interest should be updated to the interest paid
        self.assertEqual(loan.total_interest, repayment.interest_paid)

    def test_loan_repayment_negative_amount(self):
        """Test repayment with negative amount raises error"""
        loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate=Decimal('10.00'),
            loan_term_months=12,
            disbursement_date=date.today()
        )

        with self.assertRaises(ValueError):
            repayment = LoanRepayment(
                loan=loan,
                borrower=self.borrower,
                amount_paid=Decimal('-50.00'),
                payment_date=date.today()
            )
            repayment.save()


class StaffAdminTestCase(TestCase):
    def setUp(self):
        # Create lenders
        self.lender1 = Lender.objects.create(name="Lender 1", address="123 Test St", contact_email="lender1@test.com")
        self.lender2 = Lender.objects.create(name="Lender 2", address="456 Test St", contact_email="lender2@test.com")

        # Create users
        self.superuser = CustomUser.objects.create_superuser('admin', 'admin@test.com', 'password')

        self.user1 = CustomUser.objects.create_user('user1', 'user1@test.com', 'password')
        self.user1.lender = self.lender1
        self.user1.save()

        self.user2 = CustomUser.objects.create_user('user2', 'user2@test.com', 'password')
        self.user2.lender = self.lender2
        self.user2.save()

        self.user3 = CustomUser.objects.create_user('user3', 'user3@test.com', 'password')
        self.user3.lender = self.lender1
        self.user3.save()

        # Create StaffAdmin instance
        self.staff_admin = StaffAdmin(Staff, custom_admin_site)

        # Request factory
        self.factory = RequestFactory()

    def test_formfield_for_foreignkey_user_superuser(self):
        """Test that superuser can see all users in staff user dropdown"""
        request = self.factory.get('/')
        request.user = self.superuser

        # Get the user field from Staff model
        user_field = Staff._meta.get_field('user')
        field = self.staff_admin.formfield_for_foreignkey(user_field, request)
        # Superuser should see all users
        self.assertEqual(field.queryset.count(), 4)  # superuser + 3 regular users

    def test_formfield_for_foreignkey_user_regular_user(self):
        """Test that regular user can only see users from their lender in staff user dropdown"""
        request = self.factory.get('/')
        request.user = self.user1

        # Get the user field from Staff model
        user_field = Staff._meta.get_field('user')
        field = self.staff_admin.formfield_for_foreignkey(user_field, request)
        users = list(field.queryset)
        self.assertEqual(len(users), 2)  # user1 and user3 (both lender1)
        self.assertIn(self.user1, users)
        self.assertIn(self.user3, users)
        self.assertNotIn(self.user2, users)  # user2 is lender2


class CustomUserAdminFormfieldTestCase(TestCase):
    def setUp(self):
        # Create lenders
        self.lender1 = Lender.objects.create(name="Lender 1", address="123 Test St", contact_email="lender1@test.com")
        self.lender2 = Lender.objects.create(name="Lender 2", address="456 Test St", contact_email="lender2@test.com")

        # Create users
        self.superuser = CustomUser.objects.create_superuser('admin', 'admin@test.com', 'password')

        self.user1 = CustomUser.objects.create_user('user1', 'user1@test.com', 'password')
        self.user1.lender = self.lender1
        self.user1.save()

        # Create CustomUserAdmin instance
        self.custom_user_admin = CustomUserAdmin(CustomUser, None)

        # Request factory
        self.factory = RequestFactory()

    def test_formfield_for_foreignkey_lender_superuser(self):
        """Test that superuser can see all lenders in user lender dropdown"""
        request = self.factory.get('/')
        request.user = self.superuser

        # Get the lender field from CustomUser model
        lender_field = CustomUser._meta.get_field('lender')
        field = self.custom_user_admin.formfield_for_foreignkey(lender_field, request)
        # Superuser should see all lenders
        self.assertEqual(field.queryset.count(), 2)  # lender1 and lender2

    def test_formfield_for_foreignkey_lender_regular_user(self):
        """Test that regular user can only see their own lender in user lender dropdown"""
        request = self.factory.get('/')
        request.user = self.user1

        # Get the lender field from CustomUser model
        lender_field = CustomUser._meta.get_field('lender')
        field = self.custom_user_admin.formfield_for_foreignkey(lender_field, request)
        lenders = list(field.queryset)
        self.assertEqual(len(lenders), 1)  # only lender1
        self.assertIn(self.lender1, lenders)
        self.assertNotIn(self.lender2, lenders)  # lender2 should not be visible
