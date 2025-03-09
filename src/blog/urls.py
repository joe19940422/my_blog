# -*- coding: utf-8 -*-


from blog import views, vpn

from django.urls import path

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.blog_list, name='list'),
    path('tag/<str:name>/', views.tag, name='tag'),
    path('category/<str:name>/', views.category, name='category'),
    path('detail/<int:pk>/', views.detail, name='detail'),
    path('archive/', views.archive, name='archive'),
    path('search/', views.search, name='search'),
    path('message/', views.message, name='message'),
    path('getComment/', views.get_comment, name='get_comment'),
    path('bbc/', views.bbc, name='BBC'),
    path('china/', views.China, name='China'),
    path('taiwan/', views.taiwan, name='Taiwan'),
    path('dutch/', views.dutch, name='Dutch'),
    path('aboutme/', views.aboutme, name='aboutme'),
    path('pie-chart/', views.pie_chart, name='pie-chart'),
    path('visitor-chart/', views.visitor_chart, name='visitor-chart'),
    path('currency-chart/', views.currency_chart, name='currency-chart'),
    path('weather/', views.weather, name='weather'),
    #path('contact/', views.contact_view, name='contact'),
    #path('rsvp/', views.rsvp, name='rsvp'),
    path('aws/', vpn.aws_page, name='aws_page'),
    path('wedding-show/', views.wedding_show, name='wedding_show'),
    path('taiwan-show/', views.taiwan_show, name='taiwan_show'),
    # path('aws/start/', views.aws_page, name='start_instance'),
    # path('aws/stop', views.aws_page, name='stop_instance'),
    path('ranking/', views.ranking_view, name='ranking'),
]

