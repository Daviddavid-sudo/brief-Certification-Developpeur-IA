from django.contrib import admin

from .models import (
    MeteoArchive,
    ActiviteCommerciale,
    Population,
    UserProfile,
)


@admin.register(MeteoArchive)
class MeteoArchiveAdmin(admin.ModelAdmin):
    list_display = ("dep", "annee", "mois", "jour", "temp_min", "temp_max")
    list_filter = ("annee", "mois")


@admin.register(ActiviteCommerciale)
class ActiviteCommercialeAdmin(admin.ModelAdmin):
    list_display = ("ville", "code_dept", "annee", "mois", "ca_tot")
    list_filter = ("annee", "mois")


@admin.register(Population)
class PopulationAdmin(admin.ModelAdmin):
    list_display = ("dep", "departement", "region", "pop")
    list_filter = ("region",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_approved")
    list_filter = ("is_approved",)
    list_editable = ("is_approved",)