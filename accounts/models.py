from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='customer',
        db_index=True
    )
    
    # Contact Information
    phone = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    alternate_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Profile
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Address
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    # Social Links
    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # Verification
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Preferences
    newsletter_subscribed = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    account_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('suspended', 'Suspended'),
            ('banned', 'Banned'),
        ],
        default='active'
    )
    
    # Metadata
    language_preference = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['user_type', 'is_active']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]
        db_table = 'account_user'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def is_vendor(self):
        return self.user_type == 'vendor'
    
    def is_customer(self):
        return self.user_type == 'customer'
    
    def is_admin(self):
        return self.user_type == 'admin' or self.is_superuser



class UserOTPverification(models.Model):
    OTP_TYPE_CHOICES = (
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('recovery', 'Recovery'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES)
    
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'account_user_otp_verification'
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_expired() and self.attempts < self.max_attempts
    
    def __str__(self):
        return f"OTP for {self.user.email}"


class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # web, mobile, tablet
    location = models.CharField(max_length=255, blank=True)
    is_successful = models.BooleanField(default=True)
    login_method = models.CharField(
        max_length=50,
        choices=[
            ('password', 'Password'),
            ('otp', 'OTP'),
            ('google', 'Google'),
            ('facebook', 'Facebook'),
        ],
        default='password'
    )
    logged_in_at = models.DateTimeField(auto_now_add=True)
    logged_out_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-logged_in_at']
        indexes = [
            models.Index(fields=['user', '-logged_in_at']),
        ]
        db_table = 'account_login_log'
    
    def __str__(self):
        return f"{self.user.username} - {self.logged_in_at}"
