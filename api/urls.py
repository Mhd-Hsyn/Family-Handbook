from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
   index,
   AuthViewset,
   LogoDetails
)
 
router = DefaultRouter()
router.register("v1/auth", AuthViewset, basename="auth")
router.register("v1/logo_details", LogoDetails, basename="logo_details")

urlpatterns = [
    path("", index) 
]

urlpatterns += router.urls
