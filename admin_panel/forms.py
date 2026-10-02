from django import forms
from stores.models import City, Store, State, Area, Pincode, StoreCategory, Amenity
from products.models import Product, ProductCategory
from accounts.models import User
from services.models import Service, ServiceCategory
from orders.models import Order, Payment, Coupon
from core.models import ContentPage, MetaTag

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=False, 
        help_text="Leave blank to keep current password"
    )
    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'phone', 'is_active', 'is_staff', 'is_superuser']
        labels = {
            'username': 'Username',
            'email': 'Email Address',
            'user_type': 'User Type',
            'phone': 'Phone Number',
            'is_active': 'Active',
            'is_staff': 'Staff status',
            'is_superuser': 'Superuser status',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class StateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['city', 'name', 'slug']
        widgets = {
            'city': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['user', 'total_amount', 'status', 'delivery_address', 'delivery_phone', 'delivery_name']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'delivery_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['user', 'order', 'amount', 'provider', 'status', 'currency']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ContentPageForm(forms.ModelForm):
    class Meta:
        model = ContentPage
        fields = ['title', 'slug', 'content', 'is_published', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['state', 'name', 'slug']
        widgets = {
            'state': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = [
            'vendor', 'category', 'name', 'slug', 'description', 
            'address', 'area', 'pincode', 'phone', 'email', 
            'is_verified', 'is_active', 'featured'
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'pincode': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'store', 'category', 'name', 'slug', 'description', 
            'price', 'discount_price', 'stock', 'is_active'
        ]
        widgets = {
            'store': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'store', 'category', 'name', 'slug', 'description', 
            'price', 'duration_minutes', 'is_active'
        ]
        widgets = {
            'store': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class StoreCategoryForm(forms.ModelForm):
    class Meta:
        model = StoreCategory
        fields = ['name', 'slug', 'icon', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi bi-shop'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }
