from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/", views.order_history, name="order_history"),
    path("invoice/<int:order_id>.pdf", views.invoice_pdf, name="invoice_pdf"),
    path("pay/<int:order_id>/", views.pay_order, name="pay_order"),
    path("pay/verify/", views.pay_verify, name="pay_verify"),
    path("pay/stripe/create/<int:order_id>/", views.pay_stripe_create, name="pay_stripe_create"),
    path("pay/stripe/complete/", views.pay_stripe_complete, name="pay_stripe_complete"),
    path("pay/stripe/webhook/", views.pay_stripe_webhook, name="pay_stripe_webhook"),
]
