from rest_framework import serializers
from .models import LoanRepayment, Borrower, Loan

class LoanRepaymentSerializer(serializers.ModelSerializer):
    loan_number = serializers.CharField(write_only=True)  # accept loan_number instead of loan_id
    borrower_phone = serializers.CharField(write_only=True, required=False)  # optional borrower phone

    class Meta:
        model = LoanRepayment
        fields = ['id', 'loan_number', 'borrower_phone', 'amount_paid', 'principal_paid', 'interest_paid', 'payment_method', 'reference_number', 'notes', 'payment_date']

    def validate_loan_number(self, value):
        try:
            loan = Loan.objects.get(loan_number=value)
            return loan
        except Loan.DoesNotExist:
            raise serializers.ValidationError('Loan with this number does not exist.')

    def validate(self, data):
        loan = data.get('loan_number')
        borrower_phone = data.get('borrower_phone')

        if borrower_phone:
            try:
                borrower = Borrower.objects.get(phone=borrower_phone)
                if borrower != loan.borrower:
                    raise serializers.ValidationError({'borrower_phone': 'Borrower phone does not match loan borrower.'})
            except Borrower.DoesNotExist:
                raise serializers.ValidationError({'borrower_phone': 'Borrower with this phone does not exist.'})

        return data

    def create(self, validated_data):
        loan = validated_data.pop('loan_number')
        validated_data.pop('borrower_phone', None)  # Remove if present

        repayment = LoanRepayment.objects.create(
            loan=loan,
            borrower=loan.borrower,
            lender=loan.lender,
            **validated_data
        )
        return repayment
