from django.urls import path, register_converter
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('articles/<int:article_id>', views.articles, name='article'),
    path('map', views.map, name='map'),
    path('api/filter_news', views.filter_news, name='filter_news'),
]