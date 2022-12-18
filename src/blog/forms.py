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


from .models import Characteristics, TableData

class TableDataForm(ModelForm):
    name = forms.CharField(label="Name", required=True)
    characteristics = forms.ModelMultipleChoiceField(
        queryset=Characteristics.objects.all().order_by('name'),
        label="Characteristics",
        widget=forms.CheckboxSelectMultiple)

    attendance = forms.CharField(label="Attendance", required=True)
    stadium = forms.CharField(label="Stadium", required=False)

    class Meta:
        model = TableData
        exclude = ['created_at', 'edited_at']