from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("", views.DataSourceUpdate, basename="DataSource")

urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "<str:data_source>/",
        views.upload_achilles_results,
        name="upload_achilles_results",
    ),
    path("<str:data_source>/edit/", views.edit_data_source, name="edit_data_source"),
    path(
        "<str:data_source>/upload/<int:upload_id>/status/", views.get_upload_task_status
    ),
    path("", views.create_data_source, name="create_data_source"),
    path(
        "<str:data_source>/dashboard/",
        views.data_source_dashboard,
        name="data_source_dashboard",
    ),
    path(
        "<str:data_source>/OnboardingReport/",
        views.show_onboarding_csv,
        name="show_onboarding_csv"
    )
]
