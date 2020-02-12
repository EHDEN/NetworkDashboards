
from django.contrib import admin

from .models import DataSource, Country, DatabaseType

admin.site.register(DataSource)
admin.site.register(Country)
admin.site.register(DatabaseType)