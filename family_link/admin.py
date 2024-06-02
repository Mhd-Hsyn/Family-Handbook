from django.contrib import admin
from .models import  Chat_Room, Message


# Register your models with the custom admin class
admin.site.register([Chat_Room, Message])