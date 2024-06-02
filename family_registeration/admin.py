from django.contrib import admin
from .models import  FamilyParentRegisterationDetail, FamilyMemberRegisterationDetail, FamilyRelationship


# Register your models with the custom admin class
admin.site.register([FamilyParentRegisterationDetail, FamilyMemberRegisterationDetail, FamilyRelationship])
