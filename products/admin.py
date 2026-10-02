from django.contrib import admin
from .models import ProductCategory, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ['name', 'slug']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ['name', 'store', 'price', 'discount_price', 'stock', 'is_active']
    list_filter = ['is_active', 'store', 'category']
    search_fields = ['name', 'description', 'store__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Info', {'fields': ('store', 'category', 'name', 'slug', 'description')}),
        ('Pricing & Inventory', {'fields': ('price', 'discount_price', 'stock')}),
        ('Media', {'fields': ('image',)}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )