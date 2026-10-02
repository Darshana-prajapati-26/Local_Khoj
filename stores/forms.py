from django import forms
from .models import CategoryRequest, StoreCategory, State, City, Area, Pincode
from django.core.exceptions import ValidationError
import difflib


class CategoryRequestForm(forms.ModelForm):
    class Meta:
        model = CategoryRequest
        fields = ["name"]


class StoreCategoryForm(forms.ModelForm):
    class Meta:
        model = StoreCategory
        fields = ["name", "icon", "description", "display_order"]


INDIA_STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh",
    "Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
    "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
    "Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu","Delhi","Jammu and Kashmir",
    "Ladakh","Lakshadweep","Puducherry"
]

def _normalize(s: str) -> str:
    return (s or "").strip().title()

class StateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = ["name", "code"]
    def clean_name(self):
        n = _normalize(self.cleaned_data.get("name",""))
        if n in INDIA_STATES:
            return n
        sugg = difflib.get_close_matches(n, INDIA_STATES, n=1, cutoff=0.7)
        if sugg:
            raise ValidationError(f"Enter valid Indian state. Did you mean '{sugg[0]}'?")
        raise ValidationError("Enter valid Indian state name.")
    def clean_code(self):
        c = (self.cleaned_data.get("code","") or "").upper().strip()
        if len(c) != 2 or not c.isalpha():
            raise ValidationError("Enter 2-letter state code.")
        return c

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ["state", "name", "slug"]
    def clean_name(self):
        return _normalize(self.cleaned_data.get("name",""))

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ["city", "name", "slug"]
    def clean_name(self):
        return _normalize(self.cleaned_data.get("name",""))

class PincodeForm(forms.ModelForm):
    class Meta:
        model = Pincode
        fields = ["code", "area", "city"]
    def clean_code(self):
        code = (self.cleaned_data.get("code","") or "").strip()
        if not code.isdigit() or len(code) != 6:
            raise ValidationError("Enter a valid 6-digit PIN code.")
        return code
    def clean(self):
        cleaned = super().clean()
        area = cleaned.get("area")
        city = cleaned.get("city")
        if area and city and area.city_id != city.id:
            raise ValidationError("Selected city must match the area's city.")
        return cleaned
