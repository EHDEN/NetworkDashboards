from django.shortcuts import redirect
from django.urls import path

from . import views

urlpatterns = [
    path("", lambda request: redirect("tabs/")),
    path("tabs/", views.TabsView.as_view()),
    path("api/", views.APITabsView.as_view()),
]
