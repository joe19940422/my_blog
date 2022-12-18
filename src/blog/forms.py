# @Time : 2022/12/17 21:44 
# @Author : QIAOPENGFEI
# @File : forms.py

from django.forms import ModelForm
from .models import Contact
from django import forms

class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = '__all__'



