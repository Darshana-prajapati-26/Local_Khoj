from django.contrib import admin
from .models import (
    State, City, Area, Pincode, StoreCategory, Store,
    Amenity, StoreGallery, FavoriteStore, StoreItemCategory,
    StoreReview, StoreVisit, StoreOffer, ReviewReaction,
    CategoryRequest
)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state']
    list_filter = ['state']
    search_fields = ['name']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'city']
    list_filter = ['city']
    search_fields = ['name']


@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'area', 'city']
    list_filter = ['city']
    search_fields = ['code']


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ['name', 'slug', 'display_order']
    list_editable = ['display_order']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ['name', 'vendor',  'area', 'category', 'is_verified', 'featured', 'rating', 'is_active']
    list_filter = ['is_verified', 'is_active', 'featured', 'category', 'area']
    search_fields = ['name', 'vendor__username', 'phone']
    readonly_fields = ['rating', 'total_reviews', 'total_views', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {'fields': ('vendor', 'name', 'slug', 'category', 'description')}),
        ('Location', {'fields': ('address', 'area', 'pincode', 'latitude', 'longitude')}),
        ('Contact', {'fields': ('phone', 'email', 'whatsapp_number')}),
        ('Media', {'fields': ('logo', 'banner')}),
        ('Business Details', {'fields': ('gst_number', 'pan_number', 'year_established')}),
        ('Features', {'fields': ('theme_color', 'opening_time', 'closing_time', 'is_open_today', 'amenities')}),
        ('Social & Web', {'fields': ('website_url', 'instagram_url', 'facebook_url', 'twitter_url', 'linkedin_url')}),
        ('Status', {'fields': ('is_verified', 'is_active', 'featured')}),
        ('Metrics', {'fields': ('rating', 'total_reviews', 'total_views')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(StoreGallery)
class StoreGalleryAdmin(admin.ModelAdmin):
    list_display = ['store', 'created_at', 'display_order']
    list_filter = ['store', 'created_at']
    list_editable = ['display_order']


@admin.register(FavoriteStore)
class FavoriteStoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'store', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'store__name']


@admin.register(StoreItemCategory)
class StoreItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['store', 'name', 'display_order']
    list_filter = ['store']
    list_editable = ['display_order']


@admin.register(StoreReview)
class StoreReviewAdmin(admin.ModelAdmin):
    list_display = ['store', 'user', 'rating', 'is_approved', 'is_verified', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_verified', 'created_at']
    search_fields = ['store__name', 'user__username']
    readonly_fields = ['helpful_count', 'unhelpful_count', 'created_at', 'updated_at']


@admin.register(StoreVisit)
class StoreVisitAdmin(admin.ModelAdmin):
    list_display = ['store', 'user', 'ip_address', 'created_at']
    list_filter = ['created_at', 'store']
    readonly_fields = ['created_at']


@admin.register(StoreOffer)
class StoreOfferAdmin(admin.ModelAdmin):
    list_display = ['store', 'title', 'discount_percentage', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'start_date']
    list_editable = ['is_active']


@admin.register(ReviewReaction)
class ReviewReactionAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'reaction', 'created_at']
    list_filter = ['reaction', 'created_at']


@admin.register(CategoryRequest)
class CategoryRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "vendor", "is_approved", "created_at"]
    list_filter = ["is_approved"]
    search_fields = ['name']
