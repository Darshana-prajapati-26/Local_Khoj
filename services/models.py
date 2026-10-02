from django.db import models
from stores.models import Store


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'service_category'
        verbose_name_plural = "Service category"


class Service(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    duration_minutes = models.PositiveIntegerField(help_text="Service duration in minutes")

    image = models.ImageField(upload_to='services/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'service_service'
        verbose_name_plural = "Service"
