from django.db import models
from django.conf import settings
from products.models import Product
from services.models import Service
from stores.models import Store


class Order(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Delivery Information
    delivery_address = models.TextField(blank=True, null=True)
    delivery_phone = models.CharField(max_length=20, blank=True, null=True)
    delivery_name = models.CharField(max_length=100, blank=True, null=True)
    is_service_order = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    class Meta:
        db_table = 'order_order'
        verbose_name_plural = "Order"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )  # snapshot price

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        if self.product:
            return self.product.name
        if self.service:
            return self.service.name
        return "Order Item"
    class Meta:
        db_table = 'order_item'
        verbose_name_plural = "Order item"


class Coupon(models.Model):
    CODE_TYPES = (
        ("percent", "Percent"),
        ("fixed", "Fixed"),
    )
    code = models.CharField(max_length=40, unique=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=10, choices=CODE_TYPES, default="percent")
    value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
    class Meta:
        db_table = 'order_coupon'
        verbose_name_plural = "Coupon"


class Payment(models.Model):
    PROVIDERS = (
        ("manual", "Manual"),
        ("stripe", "Stripe"),
        ("razorpay", "Razorpay"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDERS, default="manual")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=20, default="pending")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider}-{self.status}-{self.amount}"
    class Meta:
        db_table = 'order_payment'
        verbose_name_plural = "Payment"
