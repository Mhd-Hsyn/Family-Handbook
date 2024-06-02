from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import index, FamilyMemberViewSet, ExpensesViewSet

router = DefaultRouter()
router.register("v1/FamilyMember", FamilyMemberViewSet, basename="FamilyMemberViewSet")
# router.register("v1/Family", FamilyViewSet, basename="FamilyViewSet")
router.register("v1/Expenses", ExpensesViewSet, basename="ExpensesViewSet")

urlpatterns = [
    path("", index) 
]

urlpatterns += router.urls