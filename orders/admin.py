from django.contrib import admin
from .models import Order, OrderItem, Coupon, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'delivery_name', 'delivery_phone', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'is_service_order', 'created_at']
    search_fields = ['id', 'user__username', 'delivery_name', 'delivery_phone', 'delivery_address']
    readonly_fields = ['created_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {'fields': ('id', 'user', 'total_amount', 'status')}),
        ('Delivery Info', {'fields': ('delivery_name', 'delivery_phone', 'delivery_address', 'is_service_order')}),
        ('Dates', {'fields': ('created_at',)}),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ['id', 'user']
        return self.readonly_fields


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'store', 'type', 'value', 'active', 'used_count', 'max_uses']
    list_filter = ['active', 'type', 'created_at']
    search_fields = ['code', 'store__name']
    readonly_fields = ['used_count', 'created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['provider', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status', 'provider', 'created_at']
    search_fields = ['order__id', 'user__username']
    readonly_fields = ['created_at']