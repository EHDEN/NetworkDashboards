from django.contrib import admin

from .models import MaterializedQuery

@admin.register(MaterializedQuery)
class MaterializedQueryAdmin(admin.ModelAdmin):
    list_display = ("name", "dashboards",)
