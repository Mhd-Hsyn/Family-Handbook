from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from decouple import config
from django.conf import settings
from core.permissions import authorization
from core.helper import get_payment_details, get_payment_details
from django.shortcuts import get_object_or_404
from api.models import Auth
from .serializers import *
from .models import Paymentdetail, Balance, Expense
from django.db.models import Sum
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError


response = lambda data: Response({"status": True, "data": data})


def index(request):
    return HttpResponse("<h1>Project Family Handbook --FamFin</h1>")


class FamilyMemberViewSet(ModelViewSet):
    @action(detail=False, methods=["GET"], permission_classes=[authorization])
    def retrieve_family_members(self, request):
        try:
            token_id = request.GET["token"]["id"]
            auth_instance = Auth.objects.get(id=token_id)
        except (Auth.DoesNotExist, ValueError, KeyError):
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        member_details = FamilyMemberRegisterationDetail.objects.filter(auth=auth_instance)
        print("member_details",member_details)
        if not member_details.exists():
            return Response({'error': 'No family member details found for the provided token'}, status=status.HTTP_404_NOT_FOUND)

        member_serializer = FamilyMemberRegisterationDetailSerializer(member_details, many=True)
        return Response(member_serializer.data, status=status.HTTP_200_OK)



    @action(detail=False, methods=["POST"], permission_classes=[authorization])
    def sendpocketmoney(self, request):
        try:
            auth_user_id = str(request.GET.get("token", {}).get("id"))

            amount = int(request.data.get("amount"))
            select_method = request.data.get("select_method")
            transaction_type = request.data.get("transaction_type")
            to_user_id = request.data.get("to_user")

            # Fetch the authenticated user
            auth_user = get_object_or_404(Auth, id=auth_user_id)

            # Fetch the recipient user
            to_user = get_object_or_404(Auth, id=to_user_id)

            # Validate select_method
            if not select_method:
                raise ValueError("Select method is required.")

            # Fetch or create balance for the recipient user
            to_user_balance, created = Balance.objects.get_or_create(auth=to_user)
            to_user_balance.amount += amount
            to_user_balance.save()

            # Create payment detail entry
            Paymentdetail.objects.create(
                amount=amount,
                select_method=select_method,
                transaction_type=transaction_type,
                to_user=to_user,
                from_user=auth_user,
            )

            return Response(
                {"status": True, "message": "Pocket Money Sent Successfully"},
                status=status.HTTP_201_CREATED,
            )

        except (ValueError, KeyError, Auth.DoesNotExist, Balance.DoesNotExist) as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError as e:
            return Response(
                {"status": False, "message": "All fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action(detail=False, methods=["GET"], permission_classes=[authorization])
    def getbalance(self, request):
        auth_user_id = str(request.GET.get("token", {}).get("id"))

        balance = get_object_or_404(Balance, auth=auth_user_id)
        data = {"amount": balance.amount}

        return Response(data, status=status.HTTP_200_OK)


    @action(detail=False, methods=["GET"], permission_classes=[authorization])
    def pocket_money_details(self, request):
        try:
            id = request.GET["id"]
            auth_user_id = str(request.GET["token"]["id"])

            payment_detail = get_object_or_404(Paymentdetail, id=id)
            user_from = (
                payment_detail.from_user
                if str(payment_detail.to_user.id) == auth_user_id
                else None
            )
            user_to = (
                payment_detail.to_user
                if str(payment_detail.from_user.id) == auth_user_id
                else None
            )

            data = (
                Paymentdetail.objects.filter(id=id)
                .values("id", "created_at", "select_method", "transaction_type", "amount")
                .first()
            )

            if user_to:
                data["fullname"] = user_to.full_name
                data["profile"] = user_to.profile.url
            elif user_from:
                data["fullname"] = user_from.full_name
                data["profile"] = user_from.profile.url

            return response(data)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Paymentdetail.DoesNotExist:
            return Response({"error": "Payment detail not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    serializer_class = FamilyMemberRegisterationDetailSerializer
    @action(detail=False, methods=["GET"], permission_classes=[authorization])
    def money_transfer_summary(self, request):
        auth_user_id = str(request.GET.get("token", {}).get("id"))

        sent_payments = Paymentdetail.objects.filter(from_user_id=auth_user_id).select_related("to_user")
        sent_to_details, total_sent_amount = get_payment_details(sent_payments, "to_user_id")

        received_payments = Paymentdetail.objects.filter(to_user_id=auth_user_id).select_related("from_user")
        received_from_details, total_received_amount = get_payment_details(received_payments, "from_user_id")

        response_data = {
            "sent_to": {"total_amount": total_sent_amount, "users": sent_to_details},
            "received_from": {"total_amount": total_received_amount, "users": received_from_details},
        }

        return Response(response_data, status=status.HTTP_200_OK)
    

class ExpensesViewSet(ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    @action(detail=False, methods=["POST"], permission_classes=[authorization])
    def create_expense(self, request):
        Put_your_expense = request.data.get("Put_your_expense")
        Amount = request.data.get("Amount")
        Date = request.data.get("Date")
        Invoice = request.data.get("Invoice")

        auth_user_id = request.GET["token"]["id"]
        auth_user = get_object_or_404(Auth, id=auth_user_id)

        data = Expense(
            Put_your_expense=Put_your_expense,
            Amount=Amount,
            Date=Date,
            Invoice=Invoice,
            user_id=auth_user,
        )
        data.save()

        return Response(
            {"status": True, "message": "Expense Has Been Successfully Created."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["GET"], permission_classes=[authorization])
    def get_expenses(self, request):
        auth_user_id = str(request.GET["token"]["id"])
        data = Expense.objects.filter(user_id=auth_user_id).values(
            "Put_your_expense", "Amount", "Date","Invoice"
        )
        return response(data)
