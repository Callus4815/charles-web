from django.urls import path
from regression import views


urlpatterns = [
    path('', views.regression_upload, name='regression-upload'),
    path('upload', views.upload, name="upload"),
    path('download_file', views.download_file, name="download_file"),
    path("delete", views.delete, name="delete"),
    path("single", views.single_file_upload, name='single-upload'),
    path('single_upload', views.upload_single_file, name="upload-single_file"),
    path("preview_file", views.preview_file, name="preview_file"),
]