from django.urls import path

from . import views

urlpatterns = [
    path("", views.TabsView.as_view()),
    path("api", views.APITabsView.as_view()),
]
