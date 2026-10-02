from django.urls import path
from . import views
from .views import (
    vendor_add_service, 
)

urlpatterns = [
   path("services/<int:pk>/", views.service_detail, name="service_detail"),
   path("vendor/add-service/", vendor_add_service, name="vendor_add_service"),
]