from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class RegisterForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=150)
    email = forms.EmailField()
    user_type = forms.ChoiceField(choices=(("customer", "Customer"), ("vendor", "Vendor")))
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            cls = "form-control"
            if name == "user_type":
                cls = "form-select"
            attrs = field.widget.attrs
            attrs["class"] = (attrs.get("class", "") + " " + cls).strip()
            if name == "email":
                attrs["required"] = "required"
                attrs["pattern"] = r'^[A-Za-z0-9._%+-]+@[A-Za-z][A-Za-z0-9.-]*\.[A-Za-z]{2,}$'

    def clean_username(self):
        User = get_user_model()
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        User = get_user_model()
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise forms.ValidationError("Email is required.")
        import re
        pattern = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z][A-Za-z0-9.-]*\.[A-Za-z]{2,}$')
        if not pattern.match(email):
            raise forms.ValidationError("Enter a valid email like xyz123@gmail.com.")
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("Enter a valid email like xyz123@gmail.com.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned
