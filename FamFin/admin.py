from django.contrib import admin
from FamFin.models import Balance, Paymentdetail, Expense

admin.site.register([Balance, Paymentdetail, Expense])
