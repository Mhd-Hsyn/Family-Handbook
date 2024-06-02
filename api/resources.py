from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Role, Country, City, Subscription, Auth, WhitelistToken, AdminSubscription, ManagerDetails, FamilyDetails, LogoSymbol, LogoColor, LogoSvg, RelatedSvg, UserLogo, Pdf, CoverPage, family_constitutions, code_of_conducts, core_values, mission_statements, family_bios, parent_members, other_members, family_media_agreements

# Define the admin classes for your models

# Register ImportExportModelAdmin for all models
for model in [Role, Country, City, Subscription, Auth, WhitelistToken, AdminSubscription, ManagerDetails, FamilyDetails, LogoSymbol, LogoColor, LogoSvg, RelatedSvg, UserLogo, Pdf, CoverPage, family_constitutions, code_of_conducts, core_values, mission_statements, family_bios, parent_members, other_members, family_media_agreements]:
    @admin.register(model)

    class GenericResource(ImportExportModelAdmin):
        class Meta:
            model = None  # Placeholder for the model
        
        def __init__(self, model, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.Meta.model = model


@admin.register(GenericResource , Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('value', 'comment')

@admin.register(GenericResource , Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(GenericResource , City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(GenericResource , Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'start_date', 'end_date')

@admin.register(GenericResource , Auth)
class AuthAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'role', 'created_at')
    search_fields = ('email', 'full_name')

@admin.register(GenericResource , WhitelistToken)
class WhitelistTokenAdmin(admin.ModelAdmin):
    list_display = ('auth', 'token', 'created_at')

@admin.register(GenericResource , AdminSubscription)
class AdminSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('auth', 'subscription', 'created_at')

@admin.register(GenericResource , ManagerDetails)
class ManagerDetailsAdmin(admin.ModelAdmin):
    list_display = ('auth', 'country', 'city', 'admin_subscription', 'created_at')

@admin.register(GenericResource , FamilyDetails)
class FamilyDetailsAdmin(admin.ModelAdmin):
    list_display = ('family_last_name', 'slogan', 'auth')

@admin.register(GenericResource , LogoSymbol)
class LogoSymbolAdmin(admin.ModelAdmin):
    list_display = ('id','symbol_name',)

@admin.register(GenericResource , LogoColor)
class LogoColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(GenericResource , LogoSvg)
class LogoSvgAdmin(admin.ModelAdmin):
    list_display = ('id', 'style', 'logo',)
    ordering = ('-id',)

@admin.register(GenericResource , RelatedSvg)
class RelatedSvgAdmin(admin.ModelAdmin):
    list_display = ('id','style',)

@admin.register(GenericResource , UserLogo)
class UserLogoAdmin(admin.ModelAdmin):
    list_display = ('family', 'logo', 'created_at')
