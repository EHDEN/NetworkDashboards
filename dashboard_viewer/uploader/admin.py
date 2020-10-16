from django.contrib import admin

from .models import Country, DatabaseType, DataSource, UploadHistory

admin.site.register(DataSource)
admin.site.register(Country)
admin.site.register(DatabaseType)


@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ("data_source", "upload_date")

    def has_add_permission(self, *_, **__):
        return False
