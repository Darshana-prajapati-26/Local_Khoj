from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product
from services.models import Service


def add_to_cart(request, item_type, item_id):
    if not request.user.is_authenticated:
        return redirect("login")

    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if item_type == "product":
        product = get_object_or_404(Product, id=item_id)

        # Check stock availability
        existing = CartItem.objects.filter(cart=cart, product=product).first()
        already_in_cart = existing.quantity if existing else 0
        if already_in_cart + quantity > product.stock:
            messages.error(request, f'Only {product.stock} unit(s) available for "{product.name}".')
            return redirect(request.META.get('HTTP_REFERER', 'cart_view'))

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    elif item_type == "service":
        service = get_object_or_404(Service, id=item_id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, service=service)

    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    return redirect("cart_view")


def update_cart_item(request, item_id):
    if not request.user.is_authenticated:
        return redirect("login")
    
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    
    if action == 'plus':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'minus':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()
        
    return redirect("cart_view")


from django.shortcuts import render


def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart/cart.html", {"cart": cart})