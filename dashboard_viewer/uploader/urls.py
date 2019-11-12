from django.urls import path

from . import views

urlpatterns = [
    #path('<str:db>', views.UploaderView.as_view()),
    path('<str:db>', views.upload, name="upload"),
    path('', views.upload, name="upload"),
]
