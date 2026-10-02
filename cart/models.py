from django.db import models
from django.conf import settings
from products.models import Product
from services.models import Service


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.user.username}"
    class Meta:
        verbose_name_plural = "Cart"

    def get_total(self):
        return sum(item.get_total_price() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    def get_unit_price(self):
        if self.product:
            return self.product.get_final_price()
        if self.service:
            return self.service.price
        return 0

    def get_total_price(self):
        return self.get_unit_price() * self.quantity

    def __str__(self):
        if self.product:
            return self.product.name
        if self.service:
            return self.service.name
        return "Cart Item"
    class Meta:
        verbose_name_plural = "Cart item"
