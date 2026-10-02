from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    
    # User management
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_add, name="user_add"),
    path("users/edit/<int:pk>/", views.user_edit, name="user_edit"),
    path("users/delete/<int:pk>/", views.user_delete, name="user_delete"),
    path("users/toggle/<int:pk>/", views.user_toggle_status, name="user_toggle_status"),
    path("users/make-admin/<int:pk>/", views.user_make_admin, name="user_make_admin"),
    
    # Location management
    path("states/", views.state_list, name="state_list"),
    path("states/add/", views.state_add, name="state_add"),
    path("states/edit/<int:pk>/", views.state_edit, name="state_edit"),
    path("states/delete/<int:pk>/", views.state_delete, name="state_delete"),
    
    path("cities/", views.city_list, name="city_list"),
    path("cities/add/", views.city_add, name="city_add"),
    path("cities/edit/<int:pk>/", views.city_edit, name="city_edit"),
    path("cities/delete/<int:pk>/", views.city_delete, name="city_delete"),
    
    path("areas/", views.area_list, name="area_list"),
    path("areas/add/", views.area_add, name="area_add"),
    path("areas/edit/<int:pk>/", views.area_edit, name="area_edit"),
    path("areas/delete/<int:pk>/", views.area_delete, name="area_delete"),
    
    # Store management
    path("stores/", views.store_list, name="store_list"),
    path("stores/add/", views.store_add, name="store_add"),
    path("stores/edit/<int:pk>/", views.store_edit, name="store_edit"),
    path("stores/detail/<int:pk>/", views.store_detail, name="store_detail"),
    path("stores/delete/<int:pk>/", views.store_delete, name="store_delete"),
    path("stores/toggle-status/<int:pk>/", views.store_toggle_status, name="store_toggle_status"),
    path("stores/toggle-verify/<int:pk>/", views.store_toggle_verify, name="store_toggle_verify"),
    
    # Product management
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_add, name="product_add"),
    path("products/edit/<int:pk>/", views.product_edit, name="product_edit"),
    path("products/delete/<int:pk>/", views.product_delete, name="product_delete"),
    
    # Service management
    path("services/", views.service_list, name="service_list"),
    path("services/add/", views.service_add, name="service_add"),
    path("services/edit/<int:pk>/", views.service_edit, name="service_edit"),
    path("services/delete/<int:pk>/", views.service_delete, name="service_delete"),
    
    # Order & Payment management
    path("orders/", views.order_list, name="order_list"),
    path("orders/edit/<int:pk>/", views.order_edit, name="order_edit"),
    path("payments/", views.payment_list, name="payment_list"),
    
    # Content management
    path("content/pages/", views.content_page_list, name="content_page_list"),
    path("content/pages/add/", views.content_page_add, name="content_page_add"),
    path("content/pages/edit/<int:pk>/", views.content_page_edit, name="content_page_edit"),
    path("content/pages/delete/<int:pk>/", views.content_page_delete, name="content_page_delete"),
    
    # Category management
    path("categories/store/", views.store_category_list, name="store_category_list"),
    path("categories/store/add/", views.store_category_add, name="store_category_add"),
    path("categories/store/edit/<int:pk>/", views.store_category_edit, name="store_category_edit"),
    path("categories/store/delete/<int:pk>/", views.store_category_delete, name="store_category_delete"),
    
    path("categories/product/", views.product_category_list, name="product_category_list"),
    path("categories/product/add/", views.product_category_add, name="product_category_add"),
    path("categories/product/edit/<int:pk>/", views.product_category_edit, name="product_category_edit"),
    path("categories/product/delete/<int:pk>/", views.product_category_delete, name="product_category_delete"),
    
    path("categories/service/", views.service_category_list, name="service_category_list"),
    path("categories/service/add/", views.service_category_add, name="service_category_add"),
    path("categories/service/edit/<int:pk>/", views.service_category_edit, name="service_category_edit"),
    path("categories/service/delete/<int:pk>/", views.service_category_delete, name="service_category_delete"),
    
    path("categories/approve/<int:pk>/", views.category_request_approve, name="category_request_approve"),
    
    # Review management
    path("reviews/store/", views.store_review_list, name="store_review_list"),
    path("reviews/product/", views.product_review_list, name="product_review_list"),
    path("reviews/reports/", views.review_report_list, name="review_report_list"),
]
