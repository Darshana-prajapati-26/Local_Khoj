from django.urls import path
from .views import vendor_dashboard
from . import views

app_name = 'vendor'

urlpatterns = [
    path('dashboard/', vendor_dashboard, name='dashboard'),
    path("leads/", views.vendor_leads, name="leads"),
    path("products/", views.vendor_products, name="products"),
    path("products/add/", views.vendor_product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.vendor_product_update, name="product_update"),
    path("products/<int:pk>/delete/", views.vendor_product_delete, name="product_delete"),
    path("request-category/", views.request_category, name="request_category"),
    path("kyc-upload/", views.kyc_upload, name="kyc_upload"),
    path("orders/", views.vendor_orders, name="orders"),
    path("orders/<int:order_id>/status/", views.vendor_order_status, name="order_status"),
    path("products/bulk-upload/", views.vendor_product_bulk_upload, name="product_bulk_upload"),
    path("subscription/", views.vendor_subscription, name="subscription"),
    path("subscription/activate-trial/<int:plan_id>/", views.vendor_activate_trial, name="activate_trial"),
    path("notifications/", views.vendor_notifications, name="notifications"),
    path("chat/", views.vendor_chat_inbox, name="chat_inbox"),
    # Services
    path("services/", views.vendor_services, name="services"),
    path("services/add/", views.vendor_service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.vendor_service_update, name="service_update"),
    path("services/<int:pk>/delete/", views.vendor_service_delete, name="service_delete"),
]
