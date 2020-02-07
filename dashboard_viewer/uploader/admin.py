
from django.contrib import admin

from .models import DatabaseType, DataSource

admin.site.register(DatabaseType)
admin.site.register(DataSource)
