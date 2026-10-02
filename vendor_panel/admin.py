from django.contrib import admin
from .models import KycDocument, SubscriptionPlan, Subscription


@admin.register(KycDocument)
class KycDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'document_number', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified', 'uploaded_at']
    search_fields = ['user__username', 'document_number']
    readonly_fields = ['uploaded_at', 'verified_at', 'verified_by']
    
    actions = ['verify_documents']
    
    def verify_documents(self, request, queryset):
        queryset.update(is_verified=True, verified_by=request.user)
    verify_documents.short_description = "Mark selected documents as verified"


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'billing_cycle', 'is_active', 'display_order']
    list_filter = ['is_active', 'plan_type', 'is_recurring']
    list_editable = ['is_active', 'display_order']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['store', 'plan', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'plan']
    search_fields = ['store__name']
    readonly_fields = ['start_date', 'created_at', 'updated_at']
