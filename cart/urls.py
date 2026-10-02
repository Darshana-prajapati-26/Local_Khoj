from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart_view, name="cart_view"),
    path("add/<str:item_type>/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    path("update/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
]