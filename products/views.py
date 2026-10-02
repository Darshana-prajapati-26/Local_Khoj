from django.shortcuts import render, get_object_or_404
from .models import Product, ProductReview, WishlistItem
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from stores.models import Store
from accounts.decorators import vendor_required
from django import forms
from .forms import ProductReviewForm

def product_detail(request, slug=None, pk=None):
    if pk is not None:
        product = get_object_or_404(Product, pk=pk, is_active=True)
    else:
        product = get_object_or_404(Product, slug=slug, is_active=True)

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        form = ProductReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect("product_detail", slug=product.slug)
    else:
        form = ProductReviewForm()

    reviews = product.reviews.select_related("user").order_by("-created_at")
    return render(request, "products/product_detail.html", {
        "product": product,
        "form": form,
        "reviews": reviews,
    })


@login_required
def wishlist_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    WishlistItem.objects.get_or_create(user=request.user, product=product)
    return redirect("wishlist_list")


@login_required
def wishlist_list(request):
    items = WishlistItem.objects.filter(user=request.user).select_related("product")
    return render(request, "products/wishlist.html", {"items": items})



# Simple Product Form (no store field exposed)
class VendorProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category',
            'name',
            'slug',
            'description',
            'price',
            'discount_price',
            'stock',
            'image',
            'is_active'
        ]


@login_required
@vendor_required
def vendor_product_list(request):
    try:
        store = Store.objects.get(vendor=request.user)
    except Store.DoesNotExist:
        return HttpResponseForbidden("You don't have a store.")

    products = Product.objects.filter(store=store)

    return render(request, "vendor_panel/vendor_products.html", {
        "products": products
    })


@login_required
@vendor_required
def vendor_product_add(request):
    try:
        store = Store.objects.get(vendor=request.user)
    except Store.DoesNotExist:
        return HttpResponseForbidden("You don't have a store.")

    if request.method == "POST":
        form = VendorProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store  # secure binding
            product.save()
            return redirect("vendor_product_list")
    else:
        form = VendorProductForm()

    return render(request, "vendor_panel/vendor_product_form.html", {
        "form": form
    })


@login_required
@vendor_required
def vendor_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # 🔐 Ownership validation
    if product.store.vendor != request.user:
        return HttpResponseForbidden("Not allowed.")

    if request.method == "POST":
        form = VendorProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("vendor_product_list")
    else:
        form = VendorProductForm(instance=product)

    return render(request, "vendor_panel/vendor_product_form.html", {
        "form": form
    })


@login_required
@vendor_required
def vendor_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # 🔐 Ownership validation
    if product.store.vendor != request.user:
        return HttpResponseForbidden("Not allowed.")

    product.delete()
    return redirect("vendor_product_list")

class VendorProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['store']  # prevent vendor from choosing store


@login_required
@vendor_required
def vendor_add_product(request):

    # 🔐 Ensure vendor has a store
    try:
        store = Store.objects.get(vendor=request.user)
    except Store.DoesNotExist:
        return HttpResponseForbidden("You must create a store first.")

    if request.method == "POST":
        form = VendorProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store  # secure binding
            product.save()
            return redirect("vendor:dashboard")
    else:
        form = VendorProductForm()

    return render(request, "vendor_panel/vendor_product_form.html", {
        "form": form
    })
