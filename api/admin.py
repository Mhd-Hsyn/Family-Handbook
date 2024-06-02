from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *

# # Register ImportExportModelAdmin for all models
# admin.site.register([Role, Country, City, Subscription, Auth, WhitelistToken, AdminSubscription, ManagerDetails, FamilyDetails, LogoSymbol, LogoColor, LogoSvg, RelatedSvg, UserLogo, Pdf, CoverPage, family_constitutions, code_of_conducts, core_values, mission_statements, family_bios, parent_members, other_members, family_media_agreements], ImportExportModelAdmin)


class CustomModelAdmin(ImportExportModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('-created_at')  # Assuming 'created_at' is the field representing creation date/time

# Register your models with the custom admin class
admin.site.register(
    [
        Role, Country, City, Subscription, Auth, WhitelistToken, AdminSubscription, ManagerDetails, FamilyDetails, LogoSymbol, LogoColor, LogoSvg, RelatedSvg, UserLogo, 
        Pdf, CoverPage, FamilyConstitutions, CodeOfConducts, CoreValues, MissionStatements, family_bios, parent_members, other_members, FamilyMediaAgreements,
        IntroductionPage, VisionStatements, Summary

     ], CustomModelAdmin)

