from django.urls import path, register_converter
from . import views

urlpatterns = [
    path('test2', views.show, name='show')
]