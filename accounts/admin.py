from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'user_type', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_staff', 'is_superuser', 'is_active', 'groups']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Personal Info', {'fields': ('phone', 'profile_image', 'bio')}),
        ('Role Info', {'fields': ('user_type',)}),
        ('Location Info', {'fields': ('address', 'city', 'state', 'pincode')}),
        ('Social Links', {'fields': ('instagram_url', 'facebook_url', 'linkedin_url')}),
    )


admin.site.register(User, CustomUserAdmin)