from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path("vendor/dashboard/", views.vendor_dashboard, name="vendor_dashboard"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("favorites/", views.favorites, name="favorites"),
    path("overview/", views.overview, name="overview"),
    path("notifications/", views.notifications, name="notifications"),
    # 2FA OTP
    path("otp/verify/", views.otp_verify, name="otp_verify"),
]
