from django import forms
from .models import Users

class UserForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['email', 'password']
        widgets = {
            'password': forms.PasswordInput(),  
        }