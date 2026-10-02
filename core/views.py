from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import RegisterForm

from stores.models import Store
from products.models import Product
from services.models import Service
from .models import SearchQuery
from .models import Notification, ChatThread, ChatMessage, UserInteraction
from vendor_panel.models import Lead
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
import math
from django.contrib.auth.decorators import login_required


# ✅ Get User model safely (works for custom or default)
User = get_user_model()


def home(request):
    featured_stores = Store.objects.filter(is_active=True, is_verified=True).order_by("-featured", "-created_at")[:8]
    top_stores = Store.objects.filter(is_active=True, is_verified=True).order_by("-rating", "-created_at")[:6]
    products = Product.objects.filter(is_active=True).order_by("-created_at")[:8]
    services = Service.objects.filter(is_active=True).order_by("-created_at")[:6]
    from stores.models import StoreCategory, City, State
    from products.models import ProductCategory
    store_categories = StoreCategory.objects.all()[:8]
    product_categories = ProductCategory.objects.all()[:8]
    states = State.objects.all().order_by('name')
    cities = City.objects.all().order_by('name')
    since = timezone.now() - timezone.timedelta(days=7)
    trending = list(SearchQuery.objects.filter(created_at__gte=since)
                    .values("query")
                    .order_by()
                    .annotate(count=Count("query"))
                    .order_by("-count")[:10])

    context = {
        "featured_stores": featured_stores,
        "top_stores": top_stores,
        "products": products,
        "services": services,
        "store_categories": store_categories,
        "product_categories": product_categories,
        "trending": [t["query"] for t in trending],
        "states": states,
        "cities": cities,
    }
    return render(request, "home.html", context)


def explore(request):
    from stores.models import StoreCategory, City
    categories = StoreCategory.objects.all().order_by('display_order', 'name')
    cities = City.objects.all().order_by('name')
    return render(request, "explore.html", {
        "categories": categories,
        "cities": cities
    })


def offers(request):
    return render(request, "offers.html")


def search(request):
    query = request.GET.get("q")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    city = request.GET.get("city")
    state = request.GET.get("state")
    open_now = request.GET.get("open_now")
    verified = request.GET.get("verified")
    rating_min = request.GET.get("rating_min")
    sort = request.GET.get("sort")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    if city is not None:
        request.session["city"] = city

    if query:
        SearchQuery.objects.create(
            query=query,
            user=request.user if request.user.is_authenticated else None
        )

    products_qs = Product.objects.filter(name__icontains=query) if query else Product.objects.none()
    if min_price:
        products_qs = products_qs.filter(price__gte=min_price)
    if max_price:
        products_qs = products_qs.filter(price__lte=max_price)
    products = products_qs

    from django.db.models import Q
    stores_qs = Store.objects.filter(is_active=True, is_verified=True).select_related('area__city__state')
    if query:
        stores_qs = stores_qs.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(area__name__icontains=query) |
            Q(area__city__name__icontains=query) |
            Q(area__city__state__name__icontains=query) |
            Q(product__name__icontains=query) |
            Q(service__name__icontains=query)
        ).distinct()
    if city:
        if city.isdigit():
            stores_qs = stores_qs.filter(area__city_id=int(city))
        else:
            stores_qs = stores_qs.filter(area__city__name__icontains=city)
    if state:
        if state.isdigit():
            stores_qs = stores_qs.filter(area__city__state_id=int(state))
        else:
            stores_qs = stores_qs.filter(area__city__state__name__icontains=state)
    stores = list(stores_qs)

    if open_now:
        stores = [s for s in stores if s.is_open_now() is True]
    if verified:
        stores = [s for s in stores if s.is_verified]

    if rating_min:
        try:
            rm = float(rating_min)
        except Exception:
            rm = None
        if rm is not None:
            def avg_rating(s):
                agg = s.reviews.aggregate(c=Count("id"), s=Count("rating"))
                c = agg["c"] or 0
                if c == 0:
                    return 0
                total = s.reviews.aggregate(t=models.Sum("rating"))["t"] or 0
                return float(total) / c
            stores = [s for s in stores if avg_rating(s) >= rm]

    if lat and lng:
        try:
            lat_f = float(lat)
            lng_f = float(lng)
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371.0
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c
            for s in stores:
                if s.latitude and s.longitude:
                    s.distance_km = haversine(lat_f, lng_f, s.latitude, s.longitude)
                else:
                    s.distance_km = None
        except Exception:
            pass

    if sort == "rating":
        stores.sort(key=lambda s: float(s.rating or 0), reverse=True)
    elif sort == "distance" and lat and lng:
        stores.sort(key=lambda s: getattr(s, 'distance_km', None) if getattr(s, 'distance_km', None) is not None else 1e9)
    elif sort == "new":
        stores.sort(key=lambda s: s.created_at, reverse=True)
    elif sort == "popularity":
        stores.sort(key=lambda s: s.total_reviews or 0, reverse=True)

    return render(request, "search.html", {
        "query": query,
        "min_price": min_price,
        "max_price": max_price,
        "city": city,
        "state": state,
        "open_now": open_now,
        "verified": verified,
        "rating_min": rating_min,
        "sort": sort,
        "products": products,
        "stores": stores,
    })


def suggestions(request):
    q = request.GET.get("q", "").strip()

    if q:
        product_names = list(
            Product.objects.filter(name__istartswith=q)
            .values_list("name", flat=True)[:5]
        )
        store_names = list(
            Store.objects.filter(name__istartswith=q)
            .values_list("name", flat=True)[:5]
        )
        payload = {"suggestions": product_names + store_names}
        if request.user.is_authenticated:
            recent = list(SearchQuery.objects.filter(user=request.user).order_by("-created_at").values_list("query", flat=True)[:5])
            payload["recent"] = recent
        return JsonResponse(payload)

    since = timezone.now() - timezone.timedelta(days=7)
    trending = list(SearchQuery.objects.filter(created_at__gte=since)
                    .values("query")
                    .order_by()
                    .annotate(count=Count("query"))
                    .order_by("-count")[:10])
    payload = {"trending": [t["query"] for t in trending]}
    if request.user.is_authenticated:
        recent = list(SearchQuery.objects.filter(user=request.user).order_by("-created_at").values_list("query", flat=True)[:5])
        payload["recent"] = recent
    return JsonResponse(payload)


@require_POST
def delete_search(request):
    """Remove a stored search query for the authenticated user.

    Expects POST data containing a `query` parameter. The view will delete
    any matching `SearchQuery` objects tied to the current user and return a
    simple JSON response indicating success or failure. Clients use this when
    the user clears a recent search entry.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "authentication required"}, status=401)

    query = request.POST.get("query", "").strip()
    if query:
        SearchQuery.objects.filter(user=request.user, query=query).delete()
    return JsonResponse({"ok": True})


def api_products(request):
    qs = Product.objects.filter(is_active=True)
    data = [{"name": p.name, "slug": p.slug, "price": float(p.get_final_price())} for p in qs[:100]]
    return JsonResponse({"products": data})


def api_stores(request):
    qs = Store.objects.filter(is_active=True, is_verified=True)
    def _city(s):
        try:
            return s.area.city.name if s.area and s.area.city else ""
        except Exception:
            return ""
    def _state(s):
        try:
            return s.area.city.state.name if s.area and s.area.city and s.area.city.state else ""
        except Exception:
            return ""
    data = [{"name": s.name, "slug": s.slug, "city": _city(s), "state": _state(s)} for s in qs[:100]]
    return JsonResponse({"stores": data})


def api_notifications(request):
    if not request.user.is_authenticated:
        return JsonResponse({"count": 0, "items": []})
    items = Notification.objects.filter(user=request.user, is_read=False).order_by("-created_at")[:10]
    return JsonResponse({"count": items.count(), "items": [
        {
            "id": i.id,
            "title": i.title,
            "body": i.body,
            "type": i.notification_type,
            "link_url": i.link_url or "",
            "store_slug": i.related_store.slug if i.related_store else "",
        }
        for i in items
    ]})


def chat_open(request, slug):
    store = get_object_or_404(Store, slug=slug, is_active=True, is_verified=True)
    if not request.user.is_authenticated:
        return redirect("login")

    # Vendors should not create a new thread as a customer — redirect to their most recent thread
    if request.user == store.vendor:
        thread = ChatThread.objects.filter(store=store).order_by('-last_message_at', '-created_at').first()
        if thread:
            return redirect("chat_open_by_id", thread_id=thread.id)
        # No threads yet — show empty vendor view
        return render(request, "chat/chat.html", {
            "store": store,
            "thread": None,
            "messages": [],
            "last_id": 0,
            "is_vendor": True,
            "other_user": None,
        })

    thread, _ = ChatThread.objects.get_or_create(store=store, user=request.user)
    messages_list = list(thread.messages.select_related("sender").order_by("created_at")[:100])
    last_id = messages_list[-1].id if messages_list else 0
    is_vendor = False
    other_user = store.vendor
    return render(request, "chat/chat.html", {
        "store": store,
        "thread": thread,
        "messages": messages_list,
        "last_id": last_id,
        "is_vendor": is_vendor,
        "other_user": other_user,
    })


def chat_open_by_id(request, thread_id):
    """Open chat by thread ID — used for vendor notifications."""
    if not request.user.is_authenticated:
        return redirect("login")
    thread = get_object_or_404(ChatThread, id=thread_id)
    # Verify access: either the customer or the store vendor
    if request.user != thread.user and request.user != thread.store.vendor:
        return redirect("home")
    messages_list = list(thread.messages.select_related("sender").order_by("created_at")[:100])
    last_id = messages_list[-1].id if messages_list else 0
    is_vendor = (request.user == thread.store.vendor)
    other_user = thread.user if is_vendor else thread.store.vendor
    return render(request, "chat/chat.html", {
        "store": thread.store,
        "thread": thread,
        "messages": messages_list,
        "last_id": last_id,
        "is_vendor": is_vendor,
        "other_user": other_user,
    })


@require_POST
def chat_send(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    if not request.user.is_authenticated:
        return redirect("login")
    content = request.POST.get("content", "").strip()
    image = request.FILES.get("image")

    if not content and not image:
        return redirect("chat_open_by_id", thread_id=thread.id)

    msg = ChatMessage.objects.create(thread=thread, sender=request.user, content=content, image=image)

    # ── Auto-greet: if this is the first message and it's a greeting ──
    GREETINGS = {'hi', 'hello', 'hey', 'hii', 'helo', 'helo', 'namaste', 'namaskar',
                 'good morning', 'good afternoon', 'good evening', 'good night',
                 'sup', 'howdy', 'greetings', 'salaam', 'salam'}
    is_first = thread.messages.count() == 1  # just created above
    is_greeting = content.lower().strip().rstrip('!.,') in GREETINGS
    is_vendor_sending = (request.user == thread.store.vendor)

    if is_first and is_greeting and not is_vendor_sending:
        # Vendor's store auto-replies
        customer_name = thread.user.get_full_name() or thread.user.username
        store = thread.store
        auto_reply = (
            f"Hello {customer_name}! 👋 Welcome to {store.name}. "
            f"How can we help you today?"
        )
        ChatMessage.objects.create(
            thread=thread,
            sender=store.vendor,
            content=auto_reply
        )

    # ── Notify the other party ──
    if is_vendor_sending:
        # Vendor replied → notify customer
        Notification.objects.create(
            user=thread.user,
            notification_type='message',
            title=f"New message from {thread.store.name}",
            body=content[:120],
            related_store=thread.store,
            link_url=f"/chat/thread/{thread.id}/"
        )
    else:
        # Customer sent → notify vendor
        Notification.objects.create(
            user=thread.store.vendor,
            notification_type='message',
            title=f"New message from {request.user.get_full_name() or request.user.username}",
            body=content[:120],
            related_store=thread.store,
            link_url=f"/chat/thread/{thread.id}/"
        )

    return redirect("chat_open_by_id", thread_id=thread.id)


def chat_poll(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    if not request.user.is_authenticated:
        return JsonResponse({"messages": []})
    last_id = int(request.GET.get("last_id", 0))
    msgs = thread.messages.filter(id__gt=last_id).order_by("id")
    data = [
        {
            "id": m.id,
            "sender": m.sender.username,
            "avatar": m.sender.profile_image.url if m.sender.profile_image else None,
            "content": m.content,
            "image": m.image.url if m.image else None,
            "created_at": m.created_at.isoformat()
        }
        for m in msgs
    ]
    return JsonResponse({"messages": data})


@login_required
@require_POST
def chat_edit_message(request, msg_id):
    msg = get_object_or_404(ChatMessage, id=msg_id, sender=request.user)
    new_content = request.POST.get("content", "").strip()
    if new_content:
        msg.content = new_content
        msg.save(update_fields=["content", "updated_at"])
    return JsonResponse({"ok": True, "content": msg.content})


@login_required
@require_POST
def chat_delete_message(request, msg_id):
    msg = get_object_or_404(ChatMessage, id=msg_id, sender=request.user)
    msg.content = ""
    msg.image = None
    msg.save(update_fields=["content", "image", "updated_at"])
    return JsonResponse({"ok": True})

def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)
    return render(request, "service_detail.html", {
        "service": service,
    })


# REGISTER VIEW (ROLE BASED)
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password1"]
            )
            if hasattr(user, "user_type"):
                user.user_type = data["user_type"]
                user.save()
            login(request, user)
            if hasattr(user, "user_type") and user.user_type == "vendor":
                return redirect("vendor:dashboard")
            return redirect("home")
        return render(request, "register.html", {"form": form})
    form = RegisterForm()
    return render(request, "register.html", {"form": form})


@login_required
def dashboard(request):
    from orders.models import Order, OrderItem
    from cart.models import Cart
    try:
        from stores.models import FavoriteStore
        fav_count = FavoriteStore.objects.filter(user=request.user).count()
    except Exception:
        fav_count = 0
    try:
        from products.models import WishlistItem
        wish_count = WishlistItem.objects.filter(user=request.user).count()
    except Exception:
        wish_count = 0
    orders = Order.objects.filter(user=request.user).order_by("-created_at")[:10]
    status_counts = orders.values("status").annotate(c=Count("id"))
    status_map = {s["status"]: s["c"] for s in status_counts}
    cart = Cart.objects.filter(user=request.user).first()
    interactions = UserInteraction.objects.filter(user=request.user).order_by("-created_at")[:20]
    searches = SearchQuery.objects.filter(user=request.user).order_by("-created_at")[:10]
    recent_items = OrderItem.objects.filter(order__user=request.user).select_related("product", "service", "order").order_by("-order__created_at")[:10]
    return render(request, "dashboard.html", {
        "orders": orders,
        "status_map": status_map,
        "cart": cart,
        "favorites_count": fav_count,
        "wishlist_count": wish_count,
        "interactions": interactions,
        "searches": searches,
        "recent_items": recent_items,
    })


@require_POST
def lead_submit(request, slug):
    store = get_object_or_404(Store, slug=slug, is_active=True, is_verified=True)
    name = request.POST.get("name", "").strip() or (request.user.get_username() if request.user.is_authenticated else "")
    phone = request.POST.get("phone", "").strip()
    message = request.POST.get("message", "").strip()
    if not name or not phone:
        messages.error(request, "Name and phone are required.")
        return redirect("stores:store_detail", slug=store.slug)
    Lead.objects.create(
        store=store,
        user=request.user if request.user.is_authenticated else None,
        name=name,
        phone=phone,
        message=message[:500],
        source="web"
    )
    Notification.objects.create(user=store.vendor, title="New lead", body=f"{name} - {phone}")
    messages.success(request, "Your request has been sent to the store.")
    return redirect("stores:store_detail", slug=store.slug)

from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

@require_POST
def api_notification_delete(request, notif_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    try:
        n = Notification.objects.get(id=notif_id, user=request.user)
    except Notification.DoesNotExist:
        return JsonResponse({"deleted": False})
    n.delete()
    return JsonResponse({"deleted": True})


@require_GET
def track_click(request, slug, source):
    store = get_object_or_404(Store, slug=slug, is_active=True, is_verified=True)
    Lead.objects.create(
        store=store,
        user=request.user if request.user.is_authenticated else None,
        name=(request.user.get_username() if request.user.is_authenticated else ""),
        phone=store.phone,
        message="click",
        source=source[:20]
    )
    return JsonResponse({"ok": True})


# ===========================
# ERROR HANDLERS
# ===========================

def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)


@login_required
def notifications_page(request):
    """Full notifications page with mark-read support."""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    items = Notification.objects.filter(user=request.user).order_by('-created_at')[:100]

    # Pre-resolve the action URL for each notification
    def resolve_url(n):
        if n.link_url:
            return n.link_url
        if n.notification_type == 'message':
            # Try to find the thread for this notification
            # The notification was created when a message was sent, so we can infer the thread
            # For vendors: find thread by store + look for recent message from the sender mentioned in title
            # For customers: find thread by store
            if n.related_store:
                if request.user == n.related_store.vendor:
                    # Vendor viewing — find the customer's thread
                    thread = ChatThread.objects.filter(store=n.related_store).order_by('-last_message_at').first()
                    return f"/chat/thread/{thread.id}/" if thread else "/vendor/notifications/"
                else:
                    # Customer viewing — their own thread
                    return f"/chat/{n.related_store.slug}/"
            return "/messages/"
        if n.notification_type == 'review' and n.related_store:
            return f"/stores/store/{n.related_store.slug}/#tab-reviews"
        if n.notification_type == 'lead':
            return "/vendor/leads/"
        if n.notification_type == 'payment':
            return "/orders/orders/"
        if n.related_store:
            return f"/stores/store/{n.related_store.slug}/"
        return ""

    notifications = [{"obj": n, "url": resolve_url(n)} for n in items]
    return render(request, 'user/notifications.html', {'notifications': notifications})


@require_POST
def api_notification_mark_read(request, notif_id):
    """Mark a single notification as read."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False}, status=401)
    Notification.objects.filter(id=notif_id, user=request.user).update(
        is_read=True, read_at=timezone.now()
    )
    return JsonResponse({'ok': True})


@require_POST
def api_notifications_mark_all_read(request):
    """Mark all notifications as read."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False}, status=401)
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return JsonResponse({'ok': True})


@login_required
def messages_inbox(request):
    """Customer messages inbox — all chat threads."""
    threads = ChatThread.objects.filter(user=request.user).select_related('store').order_by('-last_message_at', '-created_at')
    return render(request, 'chat/inbox.html', {'threads': threads})
