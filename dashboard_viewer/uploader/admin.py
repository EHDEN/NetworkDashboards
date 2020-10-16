from django.contrib import admin

from .models import Country, DatabaseType, DataSource, UploadHistory

admin.site.register(DataSource)
admin.site.register(Country)
admin.site.register(DatabaseType)
admin.site.register(UploadHistory)
