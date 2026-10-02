from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from stores.models import Store
from products.models import Product
from products.forms import ProductForm
from services.models import Service
from services.forms import VendorServiceForm
from stores.forms import CategoryRequestForm
from stores.models import CategoryRequest
from orders.models import OrderItem
from django.db.models import Sum, F, Count
from django.utils import timezone
from .models import KycDocument
from orders.models import Order
from .models import SubscriptionPlan, Subscription
from django.utils import timezone as tz
from core.models import Notification
from vendor_panel.models import Lead


# ==========================
# Vendor Dashboard
# ==========================
@login_required
def vendor_dashboard(request):
    store = Store.objects.filter(vendor=request.user).first()

    if not store:
        return render(request, "vendor_panel/dashboard.html", {
            "store": None
        })

    products = Product.objects.filter(store=store)
    services = Service.objects.filter(store=store)

    total_products = products.count()
    total_services = services.count()
    total_stock = sum(p.stock for p in products)

    qs = OrderItem.objects.filter(product__store=store) | OrderItem.objects.filter(service__store=store)

    revenue_total = qs.aggregate(total=Sum(F("price") * F("quantity")))["total"] or 0
    orders_count = qs.values("order_id").distinct().count()

    orders_qs = Order.objects.filter(items__product__store=store).distinct() | \
                Order.objects.filter(items__service__store=store).distinct()
    status_counts = orders_qs.values("status").annotate(c=Count("id"))
    status_map = {s["status"]: s["c"] for s in status_counts}
    status_series = [
        status_map.get("pending", 0),
        status_map.get("confirmed", 0),
        status_map.get("processing", 0),
        status_map.get("completed", 0),
        status_map.get("cancelled", 0),
    ]

    # Top performing products/services
    top_products = (OrderItem.objects.filter(product__store=store, product__isnull=False)
                    .values("product__name")
                    .annotate(q=Sum("quantity"), rev=Sum(F("price") * F("quantity")))
                    .order_by("-rev")[:5])
    top_services = (OrderItem.objects.filter(service__store=store, service__isnull=False)
                    .values("service__name")
                    .annotate(q=Sum("quantity"), rev=Sum(F("price") * F("quantity")))
                    .order_by("-rev")[:5])

    # Customer insights
    customer_counts = orders_qs.values("user_id").annotate(cnt=Count("id"))
    total_customers = len(customer_counts)
    returning_customers = sum(1 for x in customer_counts if x["cnt"] > 1)

    # Low stock alerts
    low_stock_products = products.filter(stock__lte=5).order_by("stock")[:10]

    # Monthly revenue for last 6 months
    today = timezone.now().date().replace(day=1)
    months = []
    month_data = []
    for i in range(6):
        start = (today - timezone.timedelta(days=30 * i)).replace(day=1)
        end = (start + timezone.timedelta(days=32)).replace(day=1)
        total = qs.filter(order__created_at__gte=start, order__created_at__lt=end)\
                  .aggregate(total=Sum(F("price") * F("quantity")))["total"] or 0
        months.append(start.strftime("%b %Y"))
        month_data.append(float(total))
    months.reverse()
    month_data.reverse()

    recent_orders = (Order.objects.filter(items__product__store=store) |
                     Order.objects.filter(items__service__store=store)).distinct().order_by("-created_at")[:5]
    recent_rows = []
    for o in recent_orders:
        vendor_total = (OrderItem.objects.filter(order=o, product__store=store).aggregate(t=Sum(F("price") * F("quantity")))["t"] or 0) + \
                       (OrderItem.objects.filter(order=o, service__store=store).aggregate(t=Sum(F("price") * F("quantity")))["t"] or 0)
        recent_rows.append({"order": o, "vendor_total": vendor_total})

    context = {
        "store": store,
        "products": products,
        "services": services,
        "total_products": total_products,
        "total_services": total_services,
        "total_stock": total_stock,
        "revenue_total": revenue_total,
        "orders_count": orders_count,
        "months": months,
        "month_data": month_data,
        "kyc": KycDocument.objects.filter(user=request.user).first(),
        "status_map": status_map,
        "status_series": status_series,
        "top_products": list(top_products),
        "top_services": list(top_services),
        "total_customers": total_customers,
        "returning_customers": returning_customers,
        "low_stock_products": low_stock_products,
        "subscription": Subscription.objects.filter(store=store, status='active').order_by("-end_date").first(),
        "plans": SubscriptionPlan.objects.filter(is_active=True),
        "recent_orders": recent_rows,
        "pending_category_requests": CategoryRequest.objects.filter(vendor=request.user, is_approved=False).count(),
    }

    return render(request, "vendor_panel/dashboard.html", context)


# ==========================
# Vendor Products List
# ==========================
@login_required
def vendor_products(request):
    store = Store.objects.filter(vendor=request.user).first()

    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")

    products = Product.objects.filter(store=store)

    return render(request, "vendor_panel/vendor_products.html", {
        "products": products
    })


# ==========================
# Vendor Add Product
# ==========================
@login_required
def vendor_product_create(request):
    store = Store.objects.filter(vendor=request.user).first()

    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, store=store)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()
            messages.success(request, "Product added successfully!")
            return redirect("vendor:products")
    else:
        form = ProductForm(store=store)

    return render(request, "vendor_panel/vendor_product_form.html", {
        "form": form
    })


from django.shortcuts import get_object_or_404


# ==========================
# Vendor Update Product
# ==========================
@login_required
def vendor_product_update(request, pk):
    store = Store.objects.filter(vendor=request.user).first()

    product = get_object_or_404(Product, pk=pk, store=store)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product, store=store)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect("vendor:products")
    else:
        form = ProductForm(instance=product, store=store)

    return render(request, "vendor_panel/vendor_product_form.html", {
        "form": form
    })


# ==========================
# Vendor Delete Product
# ==========================
@login_required
def vendor_product_delete(request, pk):
    store = Store.objects.filter(vendor=request.user).first()

    product = get_object_or_404(Product, pk=pk, store=store)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect("vendor:products")

    return render(request, "vendor_panel/vendor_product_confirm_delete.html", {
        "product": product
    })

# ==========================
# Vendor Request New Category
# ==========================

@login_required
def request_category(request):
    if request.method == "POST":
        form = CategoryRequestForm(request.POST)
        if form.is_valid():
            category_request = form.save(commit=False)
            category_request.vendor = request.user
            category_request.save()
            messages.success(request, "Category request submitted. It will appear once approved by admin.")
            return redirect("vendor:request_category")
    else:
        form = CategoryRequestForm()

    # Show all requests by this vendor
    my_requests = CategoryRequest.objects.filter(vendor=request.user).order_by('-created_at')

    return render(request, "vendor_panel/request_category.html", {
        "form": form,
        "my_requests": my_requests,
    })


@login_required
def kyc_upload(request):
    if request.method == "POST":
        file = request.FILES.get("document")
        if file:
            KycDocument.objects.update_or_create(user=request.user, defaults={"document": file, "is_verified": False})
            messages.success(request, "KYC document uploaded.")
        return redirect("vendor:dashboard")
    return render(request, "vendor_panel/kyc_upload.html")


# ==========================
# Vendor Orders Management
# ==========================
@login_required
def vendor_orders(request):
    store = Store.objects.filter(vendor=request.user).first()
    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")

    orders = (Order.objects.filter(items__product__store=store) |
              Order.objects.filter(items__service__store=store)).distinct().order_by("-created_at").select_related('user')

    # Group rows by status
    STATUS_GROUPS = {
        'pending':         [],
        'confirmed':       [],
        'processing':      [],
        'shipped':         [],
        'out_for_delivery':[],
        'completed':       [],
        'delivered':       [],
        'cancelled':       [],
    }
    all_rows = []
    for o in orders:
        vendor_items = list(
            OrderItem.objects.filter(order=o, product__store=store).select_related('product') |
            OrderItem.objects.filter(order=o, service__store=store).select_related('service')
        )
        vendor_total = sum(item.get_total_price() for item in vendor_items)
        row = {"order": o, "vendor_total": vendor_total, "vendor_items": vendor_items}
        all_rows.append(row)
        if o.status in STATUS_GROUPS:
            STATUS_GROUPS[o.status].append(row)

    return render(request, "vendor_panel/vendor_orders.html", {
        "rows": all_rows,
        "status_groups": STATUS_GROUPS,
        "store": store,
    })


@login_required
def vendor_order_status(request, order_id):
    store = Store.objects.filter(vendor=request.user).first()
    order = get_object_or_404(Order, id=order_id)
    # ensure this order includes vendor items
    has_vendor_items = OrderItem.objects.filter(order=order, product__store=store).exists() or \
                       OrderItem.objects.filter(order=order, service__store=store).exists()
    if not has_vendor_items:
        messages.error(request, "Not allowed.")
        return redirect("vendor:orders")

    status = request.POST.get("status")
    if status in dict(Order.STATUS_CHOICES).keys():
        order.status = status
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {status}.")
        Notification.objects.create(user=order.user, title="Order update", body=f"Order #{order.id} is {status}")
    return redirect("vendor:orders")


# ==========================
# Bulk Product Upload (CSV)
# ==========================
import csv
from django.core.files.storage import FileSystemStorage
from products.models import ProductCategory

@login_required
def vendor_product_bulk_upload(request):
    store = Store.objects.filter(vendor=request.user).first()
    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")

    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Upload a CSV file.")
            return redirect("vendor_product_bulk_upload")
        try:
            decoded = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded)
            created = 0
            for row in reader:
                cat = None
                if row.get("category_slug"):
                    cat = ProductCategory.objects.filter(slug=row["category_slug"]).first()
                Product.objects.create(
                    store=store,
                    category=cat,
                    name=row.get("name") or "",
                    slug=row.get("slug") or f"{store.slug}-{row.get('name','').lower().replace(' ','-')}",
                    description=row.get("description") or "",
                    price=row.get("price") or 0,
                    discount_price=row.get("discount_price") or None,
                    stock=int(row.get("stock") or 0),
                    is_active=True
                )
                created += 1
            messages.success(request, f"Uploaded {created} products.")
            return redirect("vendor:products")
        except Exception as e:
            messages.error(request, f"Upload failed: {e}")
            return redirect("vendor_product_bulk_upload")

    return render(request, "vendor_panel/bulk_upload.html")


@login_required
def vendor_subscription(request):
    store = Store.objects.filter(vendor=request.user).first()
    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")
    subs = Subscription.objects.filter(store=store, status='active').order_by("-end_date").first()
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, "vendor_panel/subscription.html", {"subscription": subs, "plans": plans, "store": store})


# ==========================
# Vendor Leads
# ==========================
@login_required
def vendor_leads(request):
    store = Store.objects.filter(vendor=request.user).first()
    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")
    leads = Lead.objects.filter(store=store).order_by("-created_at")[:200]
    return render(request, "vendor_panel/leads.html", {"leads": leads, "store": store})


@login_required
def vendor_notifications(request):
    items = Notification.objects.filter(user=request.user).order_by("-created_at")[:200]
    return render(request, "vendor_panel/notifications.html", {"notifications": items})


@login_required
def vendor_chat_inbox(request):
    """List all chat threads for the vendor's store."""
    from core.models import ChatThread
    store = Store.objects.filter(vendor=request.user).first()
    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")
    threads = ChatThread.objects.filter(store=store).select_related("user").order_by("-last_message_at", "-created_at")
    return render(request, "vendor_panel/vendor_chat_inbox.html", {"threads": threads, "store": store})

@login_required
def vendor_activate_trial(request, plan_id):
    from django.shortcuts import get_object_or_404
    from django.utils import timezone as tz
    
    store = Store.objects.filter(vendor=request.user).first()
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    start = tz.now()
    end = start + timezone.timedelta(days=7)
    
    Subscription.objects.create(
        store=store,
        plan=plan,
        start_date=start,
        end_date=end,
        status='active'
    )
    messages.success(request, "Trial activated for 7 days.")
    return redirect("vendor:subscription")


# ==========================
# Vendor Services
# ==========================

@login_required
def vendor_services(request):
    store = Store.objects.filter(vendor=request.user).first()
    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")
    services = Service.objects.filter(store=store).order_by("-id")
    return render(request, "vendor_panel/vendor_services.html", {"services": services, "store": store})


@login_required
def vendor_service_create(request):
    store = Store.objects.filter(vendor=request.user).first()
    if not store:
        messages.error(request, "You must create a store first.")
        return redirect("vendor:dashboard")
    if request.method == "POST":
        form = VendorServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.store = store
            service.save()
            messages.success(request, "Service added successfully!")
            return redirect("vendor:services")
    else:
        form = VendorServiceForm()
    return render(request, "vendor_panel/vendor_service_form.html", {"form": form})


@login_required
def vendor_service_update(request, pk):
    store = Store.objects.filter(vendor=request.user).first()
    from django.shortcuts import get_object_or_404
    service = get_object_or_404(Service, pk=pk, store=store)
    if request.method == "POST":
        form = VendorServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully!")
            return redirect("vendor:services")
    else:
        form = VendorServiceForm(instance=service)
    return render(request, "vendor_panel/vendor_service_form.html", {"form": form, "service": service})


@login_required
def vendor_service_delete(request, pk):
    store = Store.objects.filter(vendor=request.user).first()
    from django.shortcuts import get_object_or_404
    service = get_object_or_404(Service, pk=pk, store=store)
    if request.method == "POST":
        service.delete()
        messages.success(request, "Service deleted.")
        return redirect("vendor:services")
    return render(request, "vendor_panel/vendor_service_confirm_delete.html", {"service": service})
