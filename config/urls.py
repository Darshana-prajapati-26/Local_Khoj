from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views
from core.sitemaps import ProductSitemap, StoreSitemap

# Custom error handlers
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /admin-panel/",
        "Disallow: /vendor/",
        "Disallow: /user/",
        "Disallow: /cart/",
        "Disallow: /orders/",
        "Disallow: /accounts/",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


class SafePasswordResetView(auth_views.PasswordResetView):
    """Password reset that shows a friendly error if SMTP isn't configured."""
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/accounts/password_reset/done/'

    def get_extra_email_context(self):
        """Force correct protocol and domain in reset email."""
        ctx = super().get_extra_email_context() if hasattr(super(), 'get_extra_email_context') else {}
        from django.contrib.sites.shortcuts import get_current_site
        site = get_current_site(self.request)
        ctx['domain'] = site.domain
        ctx['protocol'] = 'https' if self.request.is_secure() else 'http'
        return ctx

    def form_valid(self, form):
        from django.contrib import messages as dj_messages
        try:
            return super().form_valid(form)
        except Exception as e:
            err = str(e)
            if 'SMTPAuthenticationError' in err or 'BadCredentials' in err or '535' in err:
                dj_messages.error(
                    self.request,
                    'Email is not configured on this server. '
                    'Please contact the administrator or reset your password manually.'
                )
            elif 'Connection refused' in err or 'getaddrinfo' in err:
                dj_messages.error(self.request, 'Cannot connect to email server. Please try again later.')
            else:
                dj_messages.error(self.request, f'Email could not be sent: {err[:120]}')
            return self.form_invalid(form)


urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Custom login with 2FA OTP
    path('login/', accounts_views.custom_login, name='login'),

    # Password reset — custom view with SMTP error handling
    path('accounts/password_reset/', SafePasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        post_reset_login=True,
        post_reset_login_backend='django.contrib.auth.backends.ModelBackend',
        success_url='/accounts/reset/done/',
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Django built-in auth (logout, etc. — NOT password reset, handled above)
    path('accounts/', include('django.contrib.auth.urls')),

    # Allauth (Google OAuth etc.)
    path('accounts/', include('allauth.urls')),

    # Registration
    path('register/', accounts_views.register, name='register'),

    # User profile & OTP verify
    path('user/', include('accounts.urls')),

    # App URLs
    path('vendor/', include('vendor_panel.urls')),
    path('stores/', include('stores.urls')),
    path('cart/', include('cart.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('admin-panel/', include('admin_panel.urls')),

    # Core (home, search, dashboard, etc.)
    path('', include('core.urls')),

    # SEO
    path('sitemap.xml', sitemap, {
        'sitemaps': {'products': ProductSitemap, 'stores': StoreSitemap}
    }, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
