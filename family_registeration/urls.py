from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    index,
    RegisterationViewset
)

router = DefaultRouter()
router.register("v1/registeration", RegisterationViewset, basename="registeration")

urlpatterns = [
    path("", index) 
]
 
urlpatterns += router.urls
