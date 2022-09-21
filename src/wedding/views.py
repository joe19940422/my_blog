# @Time : 2022/9/21 19:27 
# @Author : QIAOPENGFEI
# @File : views.py


from django.shortcuts import render, get_object_or_404


def wedding(request):
    return render(request, 'wedding/Wedding.html')