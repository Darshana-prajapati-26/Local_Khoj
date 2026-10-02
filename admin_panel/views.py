from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Sum, Count
from django.contrib import messages
from accounts.models import User
from stores.models import Store, CategoryRequest, City, State, Area, Pincode, StoreCategory, StoreReview
from products.models import Product, ProductCategory, ProductReview
from services.models import Service, ServiceCategory
from orders.models import Order, Payment
from core.models import ContentPage, MetaTag, ReviewReport
from .forms import (
    CityForm, StoreForm, ProductForm, ServiceForm, StoreCategoryForm, 
    ProductCategoryForm, ServiceCategoryForm, UserForm, StateForm, AreaForm,
    OrderForm, PaymentForm, ContentPageForm
)


def _is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, 'user_type', None) == 'admin')


@login_required
@user_passes_test(_is_admin)
def dashboard(request):
    total_users = User.objects.count()
    vendors = User.objects.filter(user_type="vendor").count()
    customers = User.objects.filter(user_type="customer").count()
    stores_count = Store.objects.count()
    verified_stores = Store.objects.filter(is_verified=True).count()
    active_stores = Store.objects.filter(is_active=True).count()
    products_count = Product.objects.count()
    services_count = Service.objects.count()
    orders_count = Order.objects.count()
    revenue = Payment.objects.filter(status__in=["completed", "success"]).aggregate(total=Sum("amount"))["total"] or 0
    recent_orders = Order.objects.order_by("-created_at")[:10]
    pending_categories = CategoryRequest.objects.filter(is_approved=False).order_by("-created_at")[:10]
    pending_users = User.objects.filter(is_active=False).order_by("-date_joined")[:10]
    pending_stores = Store.objects.filter(is_verified=False).order_by("-created_at")[:10]
    top_stores = Store.objects.order_by("-rating", "-total_reviews")[:10]
    by_status = list(Order.objects.values("status").annotate(c=Count("id")).order_by())
    ctx = {
        "total_users": total_users,
        "vendors": vendors,
        "customers": customers,
        "stores_count": stores_count,
        "verified_stores": verified_stores,
        "active_stores": active_stores,
        "products_count": products_count,
        "services_count": services_count,
        "orders_count": orders_count,
        "revenue": revenue,
        "recent_orders": recent_orders,
        "pending_categories": pending_categories,
        "pending_users": pending_users,
        "pending_stores": pending_stores,
        "top_stores": top_stores,
        "by_status": by_status,
    }
    return render(request, "admin_panel/dashboard.html", ctx)


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

# ===========================
# GENERIC CRUD HELPER (Internal)
# ===========================
def _generic_list(request, model, template, context_name, order_by='-id', search_fields=None, filter_fields=None, extra_context=None):
    queryset = model.objects.all().order_by(order_by)
    
    # Search
    search_query = request.GET.get('q')
    if search_query and search_fields:
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": search_query})
        queryset = queryset.filter(query)
    
    # Filter
    if filter_fields:
        for field in filter_fields:
            val = request.GET.get(field)
            if val:
                if val in ["True", "False"]:
                    val = val == "True"
                queryset = queryset.filter(**{field: val})
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page')
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
        
    querystring_params = request.GET.copy()
    if "page" in querystring_params:
        querystring_params.pop("page")
    querystring_without_page = querystring_params.urlencode()

    ctx = {
        context_name: objects,
        "search_query": search_query or "",
        "is_paginated": objects.has_other_pages(),
        "page_obj": objects,
        "querystring_without_page": querystring_without_page,
    }
    if extra_context:
        if "filter_options" in extra_context and extra_context["filter_options"]:
            prepared_filters = []
            for f in extra_context["filter_options"]:
                fname = f.get("name")
                if not fname:
                    continue
                selected_val = request.GET.get(fname)
                prepared = {"label": f.get("label", ""), "name": fname, "options": []}
                for opt in f.get("options", []):
                    opt_val = str(opt.get("value", ""))
                    option_qs = request.GET.copy()
                    option_qs[fname] = opt_val
                    if "page" in option_qs:
                        option_qs.pop("page")
                    prepared["options"].append(
                        {
                            "label": opt.get("label", ""),
                            "value": opt_val,
                            "active": selected_val == opt_val,
                            "url": f"?{option_qs.urlencode()}",
                        }
                    )
                prepared_filters.append(prepared)
            extra_context = {**extra_context, "filter_options": prepared_filters}
        ctx.update(extra_context)
        
    return render(request, template, ctx)

def _generic_add(request, form_class, template, redirect_url, success_msg, title):
    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, success_msg)
            return redirect(redirect_url)
    else:
        form = form_class()
    return render(request, template, {"form": form, "title": title})

def _generic_edit(request, model, form_class, pk, template, redirect_url, success_msg, title):
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, success_msg)
            return redirect(redirect_url)
    else:
        form = form_class(instance=obj)
    return render(request, template, {"form": form, "title": title})

def _generic_delete(request, model, pk, redirect_url, success_msg):
    obj = get_object_or_404(model, pk=pk)
    obj.delete()
    messages.success(request, success_msg)
    return redirect(redirect_url)


# ===========================
# USER MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def user_list(request):
    filter_options = [
        {
            "label": "User Type",
            "name": "user_type",
            "options": [
                {"label": "Admin", "value": "admin"},
                {"label": "Vendor", "value": "vendor"},
                {"label": "Customer", "value": "customer"},
            ]
        },
        {
            "label": "Status",
            "name": "is_active",
            "options": [
                {"label": "Active", "value": "True"},
                {"label": "Inactive", "value": "False"},
            ]
        }
    ]
    return _generic_list(
        request, User, "admin_panel/user_list.html", "users", "-date_joined", 
        search_fields=['username', 'email', 'phone'], 
        filter_fields=['user_type', 'is_active'],
        extra_context={"filter_options": filter_options}
    )

@login_required
@user_passes_test(_is_admin)
def user_add(request):
    return _generic_add(request, UserForm, "admin_panel/generic_form.html", "admin_panel:user_list", "User added successfully.", "Add User")

@login_required
@user_passes_test(_is_admin)
def user_edit(request, pk):
    return _generic_edit(request, User, UserForm, pk, "admin_panel/generic_form.html", "admin_panel:user_list", "User updated successfully.", "Edit User")

@login_required
@user_passes_test(_is_admin)
def user_delete(request, pk):
    return _generic_delete(request, User, pk, "admin_panel:user_list", "User deleted successfully.")


@login_required
@user_passes_test(_is_admin)
def user_toggle_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"User '{user.username}' status updated.")
    return redirect("admin_panel:user_list")

@login_required
@user_passes_test(_is_admin)
def user_make_admin(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.user_type = "admin"
    user.is_staff = True
    user.save()
    messages.success(request, f"User '{user.username}' is now an admin.")
    return redirect("admin_panel:user_list")


@login_required
@user_passes_test(_is_admin)
def store_toggle_status(request, pk):
    store = get_object_or_404(Store, pk=pk)
    store.is_active = not store.is_active
    store.save()
    messages.success(request, f"Store '{store.name}' status updated.")
    return redirect("admin_panel:store_list")


@login_required
@user_passes_test(_is_admin)
def store_toggle_verify(request, pk):
    store = get_object_or_404(Store, pk=pk)
    store.is_verified = not store.is_verified
    store.save()
    messages.success(request, f"Store '{store.name}' verification status updated.")
    return redirect("admin_panel:store_list")


# ===========================
# LOCATION MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def state_list(request):
    return _generic_list(request, State, "admin_panel/state_list.html", "states", "name", search_fields=['name', 'code'])

@login_required
@user_passes_test(_is_admin)
def state_add(request):
    return _generic_add(request, StateForm, "admin_panel/generic_form.html", "admin_panel:state_list", "State added.", "Add State")

@login_required
@user_passes_test(_is_admin)
def state_edit(request, pk):
    return _generic_edit(request, State, StateForm, pk, "admin_panel/generic_form.html", "admin_panel:state_list", "State updated.", "Edit State")

@login_required
@user_passes_test(_is_admin)
def state_delete(request, pk):
    return _generic_delete(request, State, pk, "admin_panel:state_list", "State deleted.")

@login_required
@user_passes_test(_is_admin)
def city_list(request):
    return _generic_list(request, City, "admin_panel/city_list.html", "cities", "name", search_fields=['name', 'slug'])

@login_required
@user_passes_test(_is_admin)
def city_add(request):
    return _generic_add(request, CityForm, "admin_panel/city_form.html", "admin_panel:city_list", "City added.", "Add City")

@login_required
@user_passes_test(_is_admin)
def city_edit(request, pk):
    return _generic_edit(request, City, CityForm, pk, "admin_panel/city_form.html", "admin_panel:city_list", "City updated.", "Edit City")

@login_required
@user_passes_test(_is_admin)
def city_delete(request, pk):
    return _generic_delete(request, City, pk, "admin_panel:city_list", "City deleted.")

@login_required
@user_passes_test(_is_admin)
def area_list(request):
    return _generic_list(request, Area, "admin_panel/area_list.html", "areas", "name", search_fields=['name', 'slug'])

@login_required
@user_passes_test(_is_admin)
def area_add(request):
    return _generic_add(request, AreaForm, "admin_panel/generic_form.html", "admin_panel:area_list", "Area added.", "Add Area")

@login_required
@user_passes_test(_is_admin)
def area_edit(request, pk):
    return _generic_edit(request, Area, AreaForm, pk, "admin_panel/generic_form.html", "admin_panel:area_list", "Area updated.", "Edit Area")

@login_required
@user_passes_test(_is_admin)
def area_delete(request, pk):
    return _generic_delete(request, Area, pk, "admin_panel:area_list", "Area deleted.")


# ===========================
# STORE MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def store_list(request):
    from stores.models import StoreCategory
    categories = StoreCategory.objects.all()
    filter_options = [
        {
            "label": "Category",
            "name": "category",
            "options": [{"label": c.name, "value": str(c.id)} for c in categories]
        },
        {
            "label": "Verification",
            "name": "is_verified",
            "options": [{"label": "Verified", "value": "True"}, {"label": "Not Verified", "value": "False"}]
        },
        {
            "label": "Status",
            "name": "is_active",
            "options": [{"label": "Active", "value": "True"}, {"label": "Inactive", "value": "False"}]
        }
    ]
    return _generic_list(
        request, Store, "admin_panel/store_list.html", "stores", "-created_at", 
        search_fields=['name', 'slug', 'phone', 'email'], 
        filter_fields=['category', 'is_verified', 'is_active', 'featured'],
        extra_context={"filter_options": filter_options}
    )

@login_required
@user_passes_test(_is_admin)
def store_add(request):
    return _generic_add(request, StoreForm, "admin_panel/store_form.html", "admin_panel:store_list", "Store added.", "Add Store")

@login_required
@user_passes_test(_is_admin)
def store_edit(request, pk):
    return _generic_edit(request, Store, StoreForm, pk, "admin_panel/store_form.html", "admin_panel:store_list", "Store updated.", "Edit Store")

@login_required
@user_passes_test(_is_admin)
def store_detail(request, pk):
    store = get_object_or_404(Store, pk=pk)
    products = Product.objects.filter(store=store)
    return render(request, "admin_panel/store_detail.html", {"store": store, "products": products})

@login_required
@user_passes_test(_is_admin)
def store_delete(request, pk):
    return _generic_delete(request, Store, pk, "admin_panel:store_list", "Store deleted.")


# ===========================
# PRODUCT MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def product_list(request):
    from products.models import ProductCategory
    categories = ProductCategory.objects.all()
    filter_options = [
        {
            "label": "Category",
            "name": "category",
            "options": [{"label": c.name, "value": str(c.id)} for c in categories]
        },
        {
            "label": "Status",
            "name": "is_active",
            "options": [{"label": "Active", "value": "True"}, {"label": "Inactive", "value": "False"}]
        }
    ]
    return _generic_list(
        request, Product, "admin_panel/product_list.html", "products", "-created_at", 
        search_fields=['name', 'slug', 'description'], 
        filter_fields=['category', 'store', 'is_active'],
        extra_context={"filter_options": filter_options}
    )

@login_required
@user_passes_test(_is_admin)
def product_add(request):
    store_id = request.GET.get('store')
    initial_data = {}
    if store_id:
        initial_data['store'] = store_id

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully.")
            return redirect("admin_panel:product_list")
    else:
        form = ProductForm(initial=initial_data)
    return render(request, "admin_panel/product_form.html", {"form": form, "title": "Add Product"})

@login_required
@user_passes_test(_is_admin)
def product_edit(request, pk):
    return _generic_edit(request, Product, ProductForm, pk, "admin_panel/product_form.html", "admin_panel:product_list", "Product updated.", "Edit Product")

@login_required
@user_passes_test(_is_admin)
def product_delete(request, pk):
    return _generic_delete(request, Product, pk, "admin_panel:product_list", "Product deleted.")


# ===========================
# SERVICE MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def service_list(request):
    return _generic_list(request, Service, "admin_panel/service_list.html", "services", "-created_at",
        search_fields=['name', 'slug', 'description', 'store__name'])

@login_required
@user_passes_test(_is_admin)
def service_add(request):
    store_id = request.GET.get('store')
    initial_data = {}
    if store_id:
        initial_data['store'] = store_id

    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Service added successfully.")
            return redirect("admin_panel:service_list")
    else:
        form = ServiceForm(initial=initial_data)
    return render(request, "admin_panel/service_form.html", {"form": form, "title": "Add Service"})

@login_required
@user_passes_test(_is_admin)
def service_edit(request, pk):
    return _generic_edit(request, Service, ServiceForm, pk, "admin_panel/service_form.html", "admin_panel:service_list", "Service updated.", "Edit Service")

@login_required
@user_passes_test(_is_admin)
def service_delete(request, pk):
    return _generic_delete(request, Service, pk, "admin_panel:service_list", "Service deleted.")


# ===========================
# ORDER & PAYMENT MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def order_list(request):
    return _generic_list(request, Order, "admin_panel/order_list.html", "orders", "-created_at",
        search_fields=['user__username', 'user__email', 'status'])

@login_required
@user_passes_test(_is_admin)
def order_edit(request, pk):
    return _generic_edit(request, Order, OrderForm, pk, "admin_panel/generic_form.html", "admin_panel:order_list", "Order updated.", "Edit Order")

@login_required
@user_passes_test(_is_admin)
def payment_list(request):
    return _generic_list(request, Payment, "admin_panel/payment_list.html", "payments", "-created_at",
        search_fields=['order__user__username', 'status', 'transaction_id'])


# ===========================
# CONTENT MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def content_page_list(request):
    return _generic_list(request, ContentPage, "admin_panel/content_page_list.html", "pages", "title")

@login_required
@user_passes_test(_is_admin)
def content_page_add(request):
    return _generic_add(request, ContentPageForm, "admin_panel/generic_form.html", "admin_panel:content_page_list", "Page added.", "Add Content Page")

@login_required
@user_passes_test(_is_admin)
def content_page_edit(request, pk):
    return _generic_edit(request, ContentPage, ContentPageForm, pk, "admin_panel/generic_form.html", "admin_panel:content_page_list", "Page updated.", "Edit Content Page")

@login_required
@user_passes_test(_is_admin)
def content_page_delete(request, pk):
    return _generic_delete(request, ContentPage, pk, "admin_panel:content_page_list", "Page deleted.")


# ===========================
# CATEGORY MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def store_category_list(request):
    return _generic_list(request, StoreCategory, "admin_panel/category_list.html", "categories", "display_order",
        search_fields=['name', 'slug'], extra_context={"type": "Store"})

@login_required
@user_passes_test(_is_admin)
def store_category_add(request):
    return _generic_add(request, StoreCategoryForm, "admin_panel/generic_form.html", "admin_panel:store_category_list", "Store category added.", "Add Store Category")

@login_required
@user_passes_test(_is_admin)
def store_category_edit(request, pk):
    return _generic_edit(request, StoreCategory, StoreCategoryForm, pk, "admin_panel/generic_form.html", "admin_panel:store_category_list", "Store category updated.", "Edit Store Category")

@login_required
@user_passes_test(_is_admin)
def store_category_delete(request, pk):
    return _generic_delete(request, StoreCategory, pk, "admin_panel:store_category_list", "Store category deleted.")

@login_required
@user_passes_test(_is_admin)
def product_category_list(request):
    return _generic_list(request, ProductCategory, "admin_panel/category_list.html", "categories", "name",
        search_fields=['name', 'slug'], extra_context={"type": "Product"})

@login_required
@user_passes_test(_is_admin)
def product_category_add(request):
    return _generic_add(request, ProductCategoryForm, "admin_panel/generic_form.html", "admin_panel:product_category_list", "Product category added.", "Add Product Category")

@login_required
@user_passes_test(_is_admin)
def product_category_edit(request, pk):
    return _generic_edit(request, ProductCategory, ProductCategoryForm, pk, "admin_panel/generic_form.html", "admin_panel:product_category_list", "Product category updated.", "Edit Product Category")

@login_required
@user_passes_test(_is_admin)
def product_category_delete(request, pk):
    return _generic_delete(request, ProductCategory, pk, "admin_panel:product_category_list", "Product category deleted.")

@login_required
@user_passes_test(_is_admin)
def service_category_list(request):
    return _generic_list(request, ServiceCategory, "admin_panel/category_list.html", "categories", "name",
        search_fields=['name', 'slug'], extra_context={"type": "Service"})

@login_required
@user_passes_test(_is_admin)
def service_category_add(request):
    return _generic_add(request, ServiceCategoryForm, "admin_panel/generic_form.html", "admin_panel:service_category_list", "Service category added.", "Add Service Category")

@login_required
@user_passes_test(_is_admin)
def service_category_edit(request, pk):
    return _generic_edit(request, ServiceCategory, ServiceCategoryForm, pk, "admin_panel/generic_form.html", "admin_panel:service_category_list", "Service category updated.", "Edit Service Category")

@login_required
@user_passes_test(_is_admin)
def service_category_delete(request, pk):
    return _generic_delete(request, ServiceCategory, pk, "admin_panel:service_category_list", "Service category deleted.")

@login_required
@user_passes_test(_is_admin)
def category_request_approve(request, pk):
    req = get_object_or_404(CategoryRequest, pk=pk)
    req.is_approved = True
    req.save()
    messages.success(request, f"Category '{req.name}' approved.")
    return redirect("admin_panel:dashboard")


# ===========================
# REVIEW MANAGEMENT
# ===========================

@login_required
@user_passes_test(_is_admin)
def store_review_list(request):
    return _generic_list(request, StoreReview, "admin_panel/review_list.html", "reviews", "-created_at",
        search_fields=['store__name', 'user__username', 'title', 'content'])

@login_required
@user_passes_test(_is_admin)
def product_review_list(request):
    return _generic_list(request, ProductReview, "admin_panel/review_list.html", "reviews", "-created_at",
        search_fields=['product__name', 'user__username', 'title', 'content'])

@login_required
@user_passes_test(_is_admin)
def review_report_list(request):
    return _generic_list(request, ReviewReport, "admin_panel/review_report_list.html", "reports", "-created_at",
        search_fields=['reason', 'user__username'])
