from django.urls import path, register_converter
from . import views

urlpatterns = [
    path('news/', views.news, name='news'),
    path('articles/<slug:article_slug>', views.articles, name='article'),
    path('map', views.map, name='map'),
    path('api/filter_news', views.filter_news, name='filter_news'),
    path('api/search_news', views.search_news, name='search_news'),
    path('api/rating', views.rating, name='rating'),
    path('', views.main, name='main'),
]
