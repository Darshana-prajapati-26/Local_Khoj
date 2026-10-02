from django import forms
from .models import User

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'profile_image', 'bio', 'address', 'city', 
            'state', 'pincode'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
