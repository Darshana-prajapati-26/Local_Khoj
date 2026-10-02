from django.db import models
from django.conf import settings
from stores.models import Store
from django.db.models import Count


# ===========================
# SEARCH & DISCOVERY
# ===========================

class SearchQuery(models.Model):
    query = models.CharField(max_length=255, db_index=True)
    search_type = models.CharField(
        max_length=50,
        choices=[
            ('store', 'Store'),
            ('product', 'Product'),
            ('service', 'Service'),
            ('category', 'Category'),
            ('location', 'Location'),
        ],
        default='store'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='search_queries'
    )
    location = models.CharField(max_length=255, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.query


class TrendingSearch(models.Model):
    query = models.CharField(max_length=255, unique=True)
    search_count = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-search_count']

    def __str__(self):
        return f"{self.query} ({self.search_count})"


# ===========================
# NOTIFICATIONS
# ===========================

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('store_update', 'Store Update'),
        ('offer', 'Offer'),
        ('lead', 'New Lead'),
        ('message', 'Message'),
        ('payment', 'Payment'),
        ('review', 'Review'),
        ('system', 'System'),
        ('promotion', 'Promotion'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    
    # Links
    related_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    link_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return self.title


# ===========================
# MESSAGING
# ===========================

class ChatThread(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='chat_threads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_threads')
    
    subject = models.CharField(max_length=255, blank=True)
    last_message = models.TextField(blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    is_closed = models.BooleanField(default=False)
    vendor_read = models.BooleanField(default=False)
    customer_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("store", "user")
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['store', 'user']),
        ]

    def __str__(self):
        return f"{self.store.name} - {self.user.username}"


class ChatMessage(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat/", blank=True, null=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username}"


# ===========================
# REVIEWS & RATINGS
# ===========================

class ReviewReport(models.Model):
    REPORT_REASONS = (
        ('inappropriate', 'Inappropriate Content'),
        ('fake', 'Fake Review'),
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Can be for store review or product review
    review_id = models.PositiveIntegerField()
    review_type = models.CharField(max_length=50)  # store_review, product_review
    
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports'
    )
    review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on {self.review_type} #{self.review_id}"


# ===========================
# SEO & CONTENT
# ===========================

class MetaTag(models.Model):
    CONTENT_TYPES = (
        ('store', 'Store'),
        ('category', 'Category'),
        ('search', 'Search Results'),
        ('page', 'Page'),
    )
    
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    title = models.CharField(max_length=60)
    description = models.CharField(max_length=160)
    keywords = models.CharField(max_length=255, blank=True)
    og_image = models.ImageField(upload_to='seo/', blank=True, null=True)
    og_title = models.CharField(max_length=255, blank=True)
    og_description = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('content_type', 'object_id')

    def __str__(self):
        return self.title


class ContentPage(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


# ===========================
# ENGAGEMENT
# ===========================

class UserInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('click', 'Click'),
        ('search', 'Search'),
        ('filter', 'Filter'),
        ('favorite', 'Favorite'),
        ('share', 'Share'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True, related_name='user_interactions')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    
    metadata = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['store', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type}"

