# @Time : 2022/9/21 19:29 
# @Author : QIAOPENGFEI
# @File : urls.py 

# -*- coding: utf-8 -*-


from wedding import views
from django.urls import path

urlpatterns = [
    path('', views.wedding, name='wedding')

]