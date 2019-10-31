from django.urls import path
from regression import views


urlpatterns = [
    path('', views.regression_upload, name='regression-upload'),
    path('upload', views.upload, name="upload"),
    path('download_file', views.download_file, name="download_file"),
    path("delete", views.delete, name="delete"),
]