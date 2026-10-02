from django.urls import path
from . import views
from .views import (
    vendor_product_list,
    vendor_product_add,
    vendor_product_edit,
    vendor_product_delete,
    vendor_add_product,
)

urlpatterns = [
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),

    path("vendor/products/", vendor_product_list, name="vendor_product_list"),
    path("vendor/products/add/", vendor_product_add, name="vendor_product_add"),
    path("vendor/products/<int:pk>/edit/", vendor_product_edit, name="vendor_product_edit"),
    path("vendor/products/<int:pk>/delete/", vendor_product_delete, name="vendor_product_delete"),
    path("vendor/add-product/", vendor_add_product, name="vendor_add_product"),

    path("wishlist/add/<int:pk>/", views.wishlist_add, name="wishlist_add"),
    path("wishlist/", views.wishlist_list, name="wishlist_list"),
]
