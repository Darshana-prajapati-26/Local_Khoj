from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


# ===========================
# LOCATION MODELS
# ===========================

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)
    
    class Meta:
        ordering = ['name']
        db_table = 'store_state'
        verbose_name_plural = "State"
    
    def __str__(self):
        return self.name


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    
    class Meta:
        unique_together = ('state', 'name')
        ordering = ['name']
        verbose_name_plural = "City"
        db_table = 'store_city'
    
    def __str__(self):
        return f"{self.name}, {self.state.name}"


class Area(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='areas')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    
    class Meta:
        unique_together = ('city', 'name')
        ordering = ['name']
        db_table = 'store_area'
        verbose_name_plural = "Area"
    
    def __str__(self):
        return f"{self.name}, {self.city.name}"


class Pincode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='pincodes')
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['code']
        db_table = 'store_pincode'
        verbose_name_plural = "Pincode"
    
    def __str__(self):
        return f"{self.code} - {self.area.name}"


# ===========================
# CATEGORY & STORE
# ===========================

class StoreCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Category"
        ordering = ['display_order', 'name']
        db_table = 'store_category'
    
    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)  # FontAwesome or similar
    
    class Meta:
        verbose_name_plural = "Amenity"
        db_table = 'store_amenity'
    
    def __str__(self):
        return self.name


class Store(models.Model):
    # Basic Info
    vendor = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='store'
    )
    category = models.ForeignKey(StoreCategory, on_delete=models.CASCADE, related_name='stores')
    
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    # Location
    address = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    pincode = models.ForeignKey(Pincode, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    # Contact
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Media
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    
    # Business Details
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    year_established = models.PositiveIntegerField(blank=True, null=True)
    
    # Features
    theme_color = models.CharField(max_length=7, default="#324bc9")
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)
    is_open_today = models.BooleanField(default=True)
    
    # Social & Web
    website_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # Amenities
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='stores')
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)  # Featured listing
    
    # Metrics
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    total_reviews = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-featured', '-rating', '-created_at']
        indexes = [
            models.Index(fields=['area', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-rating']),
        ]
        db_table = 'store_store'
        verbose_name_plural = "Store"
    
    def __str__(self):
        return self.name
    
    def is_open_now(self):
        from django.utils import timezone
        if not self.opening_time or not self.closing_time:
            return None
        now = timezone.localtime().time()
        return self.opening_time <= now <= self.closing_time
    
    def get_average_rating(self):
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Avoid accessing reverse relations before the object has a primary key
        if self.pk:
            self.rating = self.get_average_rating()
        super().save(*args, **kwargs)



class CategoryRequest(models.Model):
    name = models.CharField(max_length=100)
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='category_requests'
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.vendor.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Create StoreCategory when approved
        if self.is_approved:
            if not StoreCategory.objects.filter(name=self.name).exists():
                StoreCategory.objects.create(
                    name=self.name,
                    slug=slugify(self.name)
                )
    class Meta:
        db_table = 'store_category_request'
        verbose_name_plural = "Category request"


class StoreGallery(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='store_gallery/')
    caption = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'created_at']
        verbose_name_plural = "Gallery image"
        db_table = 'store_gallery'
    
    def __str__(self):
        return f"{self.store.name} - Image"


class FavoriteStore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_stores')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "store")
        ordering = ['-created_at']
        verbose_name_plural = "Favorite store"
        db_table = 'store_favorite_store'

    def __str__(self):
        return f"{self.user.username} -> {self.store.name}"


class StoreItemCategory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="item_categories")
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("store", "slug")
        ordering = ['display_order', 'name']
        verbose_name_plural = "Item category"
        db_table = 'store_item_category'

    def __str__(self):
        return f"{self.store.name} - {self.name}"


class StoreReview(models.Model):
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='store_reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='store_reviews/', blank=True, null=True)
    
    # Review engagement
    helpful_count = models.PositiveIntegerField(default=0)
    unhelpful_count = models.PositiveIntegerField(default=0)
    
    # Moderation
    is_verified = models.BooleanField(default=False)  # Verified purchase
    is_approved = models.BooleanField(default=True)  # Admin approval
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("store", "user")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'is_approved']),
            models.Index(fields=['-created_at']),
        ]
        db_table = 'store_review'
        verbose_name_plural = "Review"

    def __str__(self):
        return f"{self.store.name} - {self.rating} Stars"


class StoreVisit(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='visits')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'created_at']),
        ]
        db_table = 'store_visit'
        verbose_name_plural = "Visit"
    
    def __str__(self):
        return f"{self.store.name} - Visit"


class StoreOffer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    discount_percentage = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'store_offer'
        verbose_name_plural = "Offer"
    
    def __str__(self):
        return f"{self.store.name} - {self.title}"


class ReviewReaction(models.Model):
    REACTION_CHOICES = (
        ('helpful', 'Helpful'),
        ('unhelpful', 'Unhelpful'),
    )
    
    review = models.ForeignKey(StoreReview, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
        db_table = 'store_review_reaction'
        verbose_name_plural = "Review reaction"
    
    def __str__(self):
        return f"{self.review.store.name} - {self.reaction}"

