from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    index,
    ChatViewset
)

router = DefaultRouter()
router.register("v1/chat", ChatViewset, basename="chat")

urlpatterns = [
    path("", index) 
]
  
urlpatterns += router.urls
