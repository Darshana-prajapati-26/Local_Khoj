from django.db import models
from stores.models import Store
from stores.models import StoreItemCategory
from django.conf import settings
from django.apps import apps


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'product_category'
        verbose_name_plural = "Product category"


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True)
    store_category = models.ForeignKey(StoreItemCategory, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    stock = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to='products/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_final_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'product_product'
        verbose_name_plural = "Product"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="reviews/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_verified(self):
        OrderItem = apps.get_model('orders', 'OrderItem')
        return OrderItem.objects.filter(order__user=self.user, product=self.product).exists()

    def __str__(self):
        return f"{self.product.name} - {self.rating}"
    class Meta:
        db_table = 'product_review'
        verbose_name_plural = "Product review"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        db_table = 'product_wishlist_item'
        verbose_name_plural = "Wishlist item"

    def __str__(self):
        return f"{self.user.username} -> {self.product.name}"
