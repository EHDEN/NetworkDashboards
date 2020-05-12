
from django.urls import path

from . import views

urlpatterns = [
    path('', views.LandingPageView.as_view()),
    path('tabs/', views.TabsView.as_view()),
    path('api/', views.APITabsView.as_view()),
]
