
from django.urls import path

from .import views

urlpatterns = [
    path(
        '<str:data_source>/',
        views.upload_achilles_results,
        name="upload_achilles_results"
    ),
    path(
        '<str:data_source>/edit/',
        views.edit_data_source,
        name="edit_data_source"
    ),
    path(
        '',
        views.create_data_source,
        name="create_data_source"
    ),
]
