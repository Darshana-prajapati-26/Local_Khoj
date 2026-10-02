from django.db import models
from django.conf import settings
from stores.models import Store
from django.core.validators import MinValueValidator


# ===========================
# KYC DOCUMENTS
# ===========================

class KycDocument(models.Model):
    DOCUMENT_TYPES = (
        ('aadhar', 'Aadhar'),
        ('pan', 'PAN'),
        ('gst', 'GST Certificate'),
        ('udyog', 'Udyog Aadhar'),
        ('llp', 'LLP Agreement'),
        ('company', 'Company Registration'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document = models.FileField(upload_to="kyc/")
    document_number = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    verification_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'document_type')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.document_type}"


# ===========================
# SUBSCRIPTION PLANS
# ===========================

class SubscriptionPlan(models.Model):
    PLAN_TYPES = (
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('featured', 'Featured'),
        ('enterprise', 'Enterprise'),
    )
    
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Billing
    billing_cycle = models.PositiveIntegerField(default=30, help_text="Days")
    is_recurring = models.BooleanField(default=True)
    
    # Features
    max_products = models.PositiveIntegerField(default=100)
    max_services = models.PositiveIntegerField(default=50)
    max_images = models.PositiveIntegerField(default=20)
    max_gallery_images = models.PositiveIntegerField(default=50)
    leads_per_month = models.PositiveIntegerField(default=0, help_text="0 for unlimited")
    featured_duration_days = models.PositiveIntegerField(default=0)
    featured_quantity = models.PositiveIntegerField(default=0, help_text="Number of featured listings allowed")
    
    # Permissions
    analytics = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    verified_badge = models.BooleanField(default=False)
    custom_domain = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    
    # Display
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    highlight_color = models.CharField(max_length=7, default="#328BC9", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['display_order']
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
    )
    
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    renewed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    auto_renewal = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']

    def is_active_subscription(self):
        from django.utils import timezone
        return self.status == 'active' and self.end_date > timezone.now()
    
    def days_remaining(self):
        from django.utils import timezone
        if self.is_active_subscription():
            return (self.end_date - timezone.now()).days
        return 0

    def __str__(self):
        return f"{self.store.name} - {self.plan.name}"


# ===========================
# PAYMENTS
# ===========================

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('upi', 'UPI'),
        ('netbanking', 'Netbanking'),
        ('card', 'Card'),
        ('wallet', 'Wallet'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_PURPOSE = (
        ('subscription', 'Subscription'),
        ('featured_listing', 'Featured Listing'),
        ('lead_credits', 'Lead Credits'),
        ('advertisement', 'Advertisement'),
        ('other', 'Other'),
    )
    
    # References
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment Details
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purpose = models.CharField(max_length=20, choices=PAYMENT_PURPOSE)
    
    # Gateway References
    transaction_id = models.CharField(max_length=255, unique=True, db_index=True)
    order_id = models.CharField(max_length=255, blank=True)
    signature = models.CharField(max_length=500, blank=True)
    gateway_response = models.JSONField(null=True, blank=True)
    
    # Additional Info
    metadata = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


class Refund(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='refund')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_refunds'
    )
    
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund for {self.payment.transaction_id}"


# ===========================
# LEAD CREDITS
# ===========================

class LeadCredit(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='lead_credits')
    available_credits = models.PositiveIntegerField(default=0)
    total_used = models.PositiveIntegerField(default=0)
    total_purchased = models.PositiveIntegerField(default=0)
    
    last_purchase = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Lead Credits"

    def can_use_leads(self, count=1):
        return self.available_credits >= count
    
    def use_credits(self, count=1):
        if self.can_use_leads(count):
            self.available_credits -= count
            self.total_used += count
            self.save()
            return True
        return False
    
    def add_credits(self, count, reason="", payment=None):
        self.available_credits += count
        self.total_purchased += count
        self.save()
        LeadCreditTransaction.objects.create(
            credit=self,
            amount=count,
            transaction_type='add',
            reason=reason,
            payment=payment
        )
    
    def __str__(self):
        return f"{self.store.name} - {self.available_credits} credits"


class LeadCreditTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('add', 'Added'),
        ('use', 'Used'),
        ('refund', 'Refunded'),
    )
    
    credit = models.ForeignKey(LeadCredit, on_delete=models.CASCADE, related_name='transactions')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.credit.store.name} - {self.transaction_type}"


class LeadPackage(models.Model):
    name = models.CharField(max_length=100)
    credits = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.PositiveSmallIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']

    def get_final_price(self):
        if self.discount_percentage:
            return self.price * (100 - self.discount_percentage) / 100
        return self.price

    def __str__(self):
        return f"{self.name} ({self.credits} credits)"


# ===========================
# LEADS
# ===========================

class Lead(models.Model):
    LEAD_STATUS = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('interested', 'Interested'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('rejected', 'Rejected'),
    )
    
    LEAD_SOURCE = (
        ('direct', 'Direct Contact'),
        ('search', 'Search'),
        ('featured', 'Featured Listing'),
        ('advertisement', 'Advertisement'),
        ('referral', 'Referral'),
        ('other', 'Other'),
    )
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='leads')
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15, db_index=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_city = models.CharField(max_length=100, blank=True)
    
    product_interest = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=LEAD_STATUS, default='new')
    source = models.CharField(max_length=20, choices=LEAD_SOURCE, default='direct')
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    
    follow_up_date = models.DateTimeField(null=True, blank=True)
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    quality_score = models.PositiveSmallIntegerField(default=0, help_text="0-100")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store', 'status']),
            models.Index(fields=['store', '-created_at']),
            models.Index(fields=['customer_phone']),
        ]

    def __str__(self):
        return f"Lead from {self.customer_name} - {self.store.name}"


# ===========================
# ANALYTICS
# ===========================

class StoreViewLog(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='view_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    source = models.CharField(max_length=50, blank=True)  # search, category, featured, etc.
    device_type = models.CharField(max_length=20, default='web')  # web, mobile, android, ios
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['store', '-viewed_at']),
            models.Index(fields=['-viewed_at']),
        ]

    def __str__(self):
        return f"{self.store.name} - View"


class StoreClickLog(models.Model):
    CLICK_TYPES = (
        ('call', 'Call'),
        ('whatsapp', 'WhatsApp'),
        ('direction', 'Direction'),
        ('website', 'Website'),
        ('review', 'Review'),
        ('message', 'Message'),
        ('email', 'Email'),
        ('share', 'Share'),
        ('favorite', 'Add to Favorites'),
    )
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='click_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    click_type = models.CharField(max_length=50, choices=CLICK_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=20, default='web')
    clicked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['store', 'click_type']),
            models.Index(fields=['store', '-clicked_at']),
        ]

    def __str__(self):
        return f"{self.store.name} - {self.click_type}"

