from django.contrib import admin

from .models import Tab, TabGroup


@admin.register(Tab)
class TabAdmin(admin.ModelAdmin):
    list_display = ("title", "position", "visible", "group")
    list_filter = ("visible",)


@admin.register(TabGroup)
class TabGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "position", "visible")
    list_filter = ("visible",)
