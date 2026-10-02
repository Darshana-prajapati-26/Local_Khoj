from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from core.forms import RegisterForm
from django.contrib.auth import get_user_model
from accounts.decorators import vendor_required
from stores.models import Store
from products.models import Product
from orders.models import Order, OrderItem
from core.models import Notification, UserInteraction, SearchQuery
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.core.mail import send_mail
from django.conf import settings as django_settings

from .forms import UserEditForm
from .models import UserOTPverification


User = get_user_model()


# ===========================
# OTP HELPERS
# ===========================

def _generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def _is_email_configured():
    """Return True only if real SMTP credentials are set and working."""
    backend = getattr(django_settings, 'EMAIL_BACKEND', '')
    return 'smtp' in backend.lower() and 'console' not in backend.lower()


def _is_sms_configured():
    """Return True if Fast2SMS API key is set."""
    key = getattr(django_settings, 'FAST2SMS_API_KEY', '').strip()
    return bool(key)


def _send_otp_sms(phone, otp_code):
    """
    Send OTP via Fast2SMS (free ₹50 credits on signup).
    Returns True on success, False on failure.
    Get API key: https://www.fast2sms.com → Sign up → API → Dev API Key
    """
    if not _is_sms_configured():
        return False
    # Clean phone number — remove +91, spaces, dashes
    phone = ''.join(filter(str.isdigit, str(phone or '')))
    if phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]
    if len(phone) != 10:
        return False
    try:
        import urllib.request, urllib.parse, json
        api_key = getattr(django_settings, 'FAST2SMS_API_KEY', '')
        message = f"Your Local Khoj login OTP is {otp_code}. Valid for {getattr(django_settings,'OTP_EXPIRY_MINUTES',10)} minutes. Do not share."
        payload = urllib.parse.urlencode({
            'route': 'q',
            'message': message,
            'language': 'english',
            'flash': 0,
            'numbers': phone,
        }).encode()
        req = urllib.request.Request(
            'https://www.fast2sms.com/dev/bulkV2',
            data=payload,
            headers={
                'authorization': api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get('return', False)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"SMS OTP failed for {phone}: {e}")
        return False


def _send_otp_email(user, otp_code):
    """Send OTP email. Returns True on success, False on failure."""
    if not _is_email_configured():
        return False
    subject = "Local Khoj — Your Login OTP"
    html_message = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;background:#0a0b10;border-radius:16px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#00d2ff,#3a7bd5);padding:24px 32px;">
        <h2 style="color:#fff;margin:0;font-size:1.4rem;">Local Khoj</h2>
        <p style="color:rgba(255,255,255,.7);margin:4px 0 0;font-size:.85rem;">Find Everything Near You</p>
      </div>
      <div style="padding:32px;">
        <p style="color:#e0e6ed;margin:0 0 8px;">Hi <strong>{user.first_name or user.username}</strong>,</p>
        <p style="color:#94a3b8;margin:0 0 24px;font-size:.9rem;">Your one-time login code is:</p>
        <div style="background:rgba(0,210,255,.08);border:1px solid rgba(0,210,255,.2);border-radius:12px;padding:20px;text-align:center;margin-bottom:24px;">
          <span style="font-size:2.5rem;font-weight:800;letter-spacing:12px;color:#00d2ff;">{otp_code}</span>
        </div>
        <p style="color:#64748b;font-size:.82rem;margin:0;">
          Valid for <strong style="color:#e0e6ed;">{getattr(django_settings,'OTP_EXPIRY_MINUTES',10)} minutes</strong>.
          Do not share this code with anyone.
        </p>
      </div>
      <div style="background:#050608;padding:16px 32px;text-align:center;">
        <p style="color:#475569;font-size:.75rem;margin:0;">© 2026 Local Khoj · support@localkhoj.com</p>
      </div>
    </div>
    """
    plain = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Your Local Khoj login OTP is: {otp_code}\n\n"
        f"Valid for {getattr(django_settings,'OTP_EXPIRY_MINUTES',10)} minutes.\n"
        f"Do not share this with anyone.\n\n— Local Khoj Team"
    )
    try:
        from django.core.mail import EmailMultiAlternatives
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"OTP email failed for {user.email}: {e}")
        return False


def _create_otp(user):
    """Create a fresh OTP record, invalidating old ones."""
    UserOTPverification.objects.filter(user=user, otp_type='email', is_verified=False).delete()
    otp_code = _generate_otp()
    expiry = timezone.now() + timedelta(minutes=getattr(django_settings, 'OTP_EXPIRY_MINUTES', 10))
    otp_obj = UserOTPverification.objects.create(
        user=user,
        email=user.email,
        otp_code=otp_code,
        otp_type='email',
        expires_at=expiry,
    )
    return otp_obj


@login_required
def edit_profile(request):
    """View for editing user profile information."""
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserEditForm(instance=request.user)
    
    return render(request, 'user/edit_profile.html', {'form': form})


def register(request):
    """Registration view using project RegisterForm (includes user_type)."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user = User.objects.create_user(
                    username=data.get('username'),
                    email=data.get('email'),
                    password=data.get('password1')
                )
                if hasattr(user, 'user_type'):
                    user.user_type = data.get('user_type', 'customer')
                    user.save()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Registration successful. Welcome!')
                if getattr(user, 'user_type', None) == 'vendor':
                    return redirect('vendor:dashboard')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Error creating account: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


# ===========================
# CUSTOM LOGIN WITH 2FA OTP
# ===========================

def custom_login(request):
    """Simple login — username/password only, no OTP."""
    from django.contrib.auth import authenticate
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            try:
                u = User.objects.get(email=username)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                pass
        if user is not None and user.is_active:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', '') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username/email or password.')
    return render(request, 'registration/login.html', {'next': request.GET.get('next', '')})


def otp_verify(request):
    """Verify the 6-digit OTP and complete login."""
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('login')
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()
        action = request.POST.get('action', 'verify')
        if action == 'resend':
            otp_obj = _create_otp(user)
            if _is_email_configured():
                sent = _send_otp_email(user, otp_obj.otp_code)
                if sent:
                    messages.success(request, 'New OTP sent to your email.')
                else:
                    messages.warning(request,
                        f'Email failed. Your new OTP is: '
                        f'<strong style="font-size:1.2rem;letter-spacing:4px;">{otp_obj.otp_code}</strong>')
            else:
                messages.info(request,
                    f'Your new OTP is: '
                    f'<strong style="font-size:1.2rem;letter-spacing:4px;">{otp_obj.otp_code}</strong>')
            return redirect('user:otp_verify')

        otp_obj = UserOTPverification.objects.filter(
            user=user, otp_type='email', is_verified=False
        ).order_by('-created_at').first()

        if not otp_obj or otp_obj.is_expired():
            messages.error(request, 'OTP expired. Please login again.')
            return redirect('login')

        otp_obj.attempts += 1
        otp_obj.save(update_fields=['attempts'])

        if otp_obj.attempts > otp_obj.max_attempts:
            messages.error(request, 'Too many attempts. Please login again.')
            return redirect('login')

        if otp_obj.otp_code == entered:
            otp_obj.is_verified = True
            otp_obj.save(update_fields=['is_verified'])
            del request.session['otp_user_id']
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.session.pop('otp_next', '') or 'home'
            return redirect(next_url)
        else:
            remaining = otp_obj.max_attempts - otp_obj.attempts
            messages.error(request, f'Incorrect OTP. {remaining} attempt(s) remaining.')

    masked_email = f"{user.email[:3]}***@{user.email.split('@')[1]}" if user.email else 'your email'
    return render(request, 'registration/otp_verify.html', {'masked_email': masked_email})


@login_required
@vendor_required
def vendor_dashboard(request):
    # redirect to vendor_panel namespaced dashboard (primary implementation lives there)
    return redirect('vendor:dashboard')


@login_required
def profile(request):
    """User profile page where users can view and edit basic info."""
    user = request.user
    return render(request, 'user/profile.html', {'user_profile': user})


@login_required
def overview(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')[:20]
    recent_items = OrderItem.objects.filter(order__user=user).select_related('product', 'service', 'order').order_by('-order__created_at')[:10]
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    interactions = UserInteraction.objects.filter(user=user).order_by('-created_at')[:20]
    searches = SearchQuery.objects.filter(user=user).order_by('-created_at')[:10]
    return render(request, 'user/overview.html', {
        'user_profile': user,
        'orders': orders,
        'recent_items': recent_items,
        'notifications': notifications,
        'interactions': interactions,
        'searches': searches,
    })


@login_required
def favorites(request):
    """Show user's favorite stores (uses FavoriteStore model if available)."""
    try:
        from stores.models import FavoriteStore
        favs = FavoriteStore.objects.filter(user=request.user).select_related('store')
    except Exception:
        favs = []
    return render(request, 'user/favorites.html', {'favorites': favs})


@login_required
def notifications(request):
    """User notifications page scoped to current account."""
    items = Notification.objects.filter(user=request.user).order_by('-created_at')[:200]
    return render(request, 'user/notifications.html', {'notifications': items})
