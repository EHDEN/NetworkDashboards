from django.contrib import admin

from .models import Country, DatabaseType, DataSource

admin.site.register(DataSource)
admin.site.register(Country)
admin.site.register(DatabaseType)
