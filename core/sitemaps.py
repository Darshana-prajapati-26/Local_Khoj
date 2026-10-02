from django.contrib.sitemaps import Sitemap
from products.models import Product
from stores.models import Store

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7
    def items(self):
        return Product.objects.filter(is_active=True)
    def location(self, obj):
        from django.urls import reverse
        return reverse("product_detail", kwargs={"slug": obj.slug})

class StoreSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    def items(self):
        return Store.objects.filter(is_active=True, is_verified=True)
    def location(self, obj):
        from django.urls import reverse
        return reverse("store_detail", kwargs={"slug": obj.slug})
