from django.db import models
from api.models import BaseModel, Auth


class Balance(BaseModel):
    amount = models.IntegerField(default=0)
    auth = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)


class Paymentdetail(BaseModel):
    ROLE_CHOICES = [
        ("Bank", "Bank"),
        ("Cash", "Cash"),
    ]
    amount = models.IntegerField(default=0)
    select_method = models.CharField(max_length=60, choices=ROLE_CHOICES)
    transaction_type = models.CharField(max_length=1000, default="")
    from_user = models.ForeignKey(
        Auth, on_delete=models.CASCADE, related_name="paymentdetail_from"
    )
    to_user = models.ForeignKey(
        Auth, on_delete=models.CASCADE, related_name="paymentdetail_to"
    )


class Expense(BaseModel):
    Put_your_expense = models.CharField(max_length=1000, default="")
    Amount = models.IntegerField(default=0)
    Date = models.DateField(auto_now=False)
    Invoice = models.FileField(upload_to="Invoice/", null=True, blank=True)
    user_id = models.ForeignKey(Auth, on_delete=models.CASCADE, related_name="userid")
