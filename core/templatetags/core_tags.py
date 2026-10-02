from django import template
from django.utils.text import slugify as dj_slugify

register = template.Library()


@register.filter
def slugify(value):
    try:
        return dj_slugify(value or "")
    except Exception:
        return ""

@register.filter
def eq(value, other):
    try:
        return str(value or "") == str(other or "")
    except Exception:
        return False

@register.filter
def category_icon(slug):
    """Map category slug to a Bootstrap Icon class name."""
    s = (slug or '').lower()
    icons = {
        # Food & Drink
        'restaurants': 'bi-egg-fried',
        'restaurant': 'bi-egg-fried',
        'dine-in-restaurant': 'bi-cup-hot-fill',
        'cafe': 'bi-cup-straw',
        'bakery': 'bi-cake2-fill',
        'food-beverage': 'bi-basket2-fill',
        'food-&-beverage': 'bi-basket2-fill',
        'food': 'bi-basket2-fill',
        'sweet-shop': 'bi-cake-fill',
        'juice-bar': 'bi-cup-fill',
        'fast-food': 'bi-bag-fill',

        # Retail & Shopping
        'shops': 'bi-shop-window',
        'shop': 'bi-shop-window',
        'retail': 'bi-bag-heart-fill',
        'retail-shopping': 'bi-bag-heart-fill',
        'boutique': 'bi-bag-fill',
        'fashion': 'bi-handbag-fill',
        'clothing': 'bi-handbag-fill',
        'grocery': 'bi-cart-fill',
        'supermarket': 'bi-cart4',
        'electronics': 'bi-laptop-fill',
        'electronics-store': 'bi-laptop-fill',
        'mobile': 'bi-phone-fill',
        'hardware-store': 'bi-hammer',
        'hardware': 'bi-hammer',
        'furniture': 'bi-house-fill',
        'books': 'bi-book-fill',
        'stationery': 'bi-pencil-fill',
        'toys': 'bi-controller',
        'sports': 'bi-trophy-fill',
        'jewellery': 'bi-gem',
        'jewelry': 'bi-gem',
        'gifts': 'bi-gift-fill',

        # Health & Beauty
        'health-beauty': 'bi-heart-pulse-fill',
        'health-&-beauty': 'bi-heart-pulse-fill',
        'beauty': 'bi-stars',
        'beauty-parlour': 'bi-stars',
        'salon': 'bi-scissors',
        'hair-salon': 'bi-scissors',
        'spa': 'bi-flower1',
        'pharmacy': 'bi-capsule-pill',
        'medical': 'bi-hospital-fill',
        'hospitals': 'bi-hospital-fill',
        'hospital': 'bi-hospital-fill',
        'clinic': 'bi-bandaid-fill',
        'dental': 'bi-emoji-smile-fill',
        'eye-care': 'bi-eye-fill',
        'fitness': 'bi-heart-pulse-fill',
        'fitness-center': 'bi-heart-pulse-fill',
        'gym': 'bi-bicycle',
        'yoga': 'bi-person-arms-up',

        # Services
        'services': 'bi-gear-wide-connected',
        'professional-services': 'bi-briefcase-fill',
        'professional': 'bi-briefcase-fill',
        'plumber': 'bi-wrench-adjustable-fill',
        'electrician': 'bi-lightning-charge-fill',
        'carpenter': 'bi-tools',
        'cleaning': 'bi-stars',
        'laundry': 'bi-droplet-fill',
        'tailoring': 'bi-scissors',
        'repair': 'bi-wrench-adjustable',
        'printing': 'bi-printer-fill',
        'photography': 'bi-camera-fill',
        'event': 'bi-calendar-event-fill',
        'events': 'bi-calendar-event-fill',
        'catering': 'bi-cup-hot-fill',
        'security': 'bi-shield-fill-check',
        'pest-control': 'bi-bug-fill',
        'interior': 'bi-house-heart-fill',
        'architect': 'bi-building-fill',

        # Education
        'education': 'bi-mortarboard-fill',
        'school': 'bi-mortarboard-fill',
        'college': 'bi-building-fill',
        'coaching': 'bi-pencil-square',
        'tuition': 'bi-pencil-square',
        'library': 'bi-book-fill',
        'computer': 'bi-pc-display-horizontal',
        'language': 'bi-translate',

        # Automotive
        'automotive': 'bi-car-front-fill',
        'car': 'bi-car-front-fill',
        'bike': 'bi-bicycle',
        'garage': 'bi-tools',
        'petrol': 'bi-fuel-pump-fill',
        'tyres': 'bi-circle-fill',

        # Travel & Hospitality
        'travel': 'bi-airplane-fill',
        'hotel': 'bi-building-fill',
        'hotels': 'bi-building-fill',
        'lodge': 'bi-house-door-fill',
        'transport': 'bi-bus-front-fill',
        'taxi': 'bi-taxi-front-fill',

        # Finance & Legal
        'banking': 'bi-bank2',
        'bank': 'bi-bank2',
        'finance': 'bi-currency-rupee',
        'insurance': 'bi-shield-fill',
        'legal': 'bi-briefcase-fill',
        'ca': 'bi-calculator-fill',

        # Entertainment
        'entertainment': 'bi-controller',
        'gaming': 'bi-controller',
        'cinema': 'bi-film',
        'music': 'bi-music-note-beamed',
        'art': 'bi-palette-fill',
        'henna-art': 'bi-palette-fill',
        'henna': 'bi-palette-fill',

        # Real Estate
        'real-estate': 'bi-house-fill',
        'property': 'bi-house-fill',
        'construction': 'bi-building-fill',

        # Pets
        'pets': 'bi-heart-fill',
        'veterinary': 'bi-heart-fill',
    }
    # Exact match first
    if s in icons:
        return icons[s]
    # Partial match
    for key, icon in icons.items():
        if key in s or s in key:
            return icon
    return 'bi-grid-fill'


@register.filter
def category_color(slug):
    """Map category slug to a colour style string."""
    s = (slug or '').lower()
    colors = {
        # Food
        'restaurants': '#f59e0b', 'restaurant': '#f59e0b',
        'dine-in-restaurant': '#f59e0b', 'cafe': '#a16207',
        'bakery': '#d97706', 'food': '#f59e0b', 'food-beverage': '#f59e0b',
        'sweet-shop': '#ec4899', 'juice-bar': '#10b981',
        # Retail
        'shops': '#ef4444', 'boutique': '#8b5cf6', 'fashion': '#ec4899',
        'grocery': '#10b981', 'electronics': '#3b82f6',
        'electronics-store': '#3b82f6', 'hardware-store': '#78716c',
        'jewellery': '#f59e0b', 'jewelry': '#f59e0b',
        # Health & Beauty
        'health-beauty': '#ef4444', 'beauty': '#ec4899',
        'beauty-parlour': '#ec4899', 'salon': '#ec4899',
        'hair-salon': '#ec4899', 'spa': '#10b981',
        'pharmacy': '#ef4444', 'hospitals': '#ef4444',
        'hospital': '#ef4444', 'fitness': '#ef4444',
        'fitness-center': '#ef4444', 'gym': '#f97316',
        # Services
        'services': '#00d2ff', 'professional-services': '#3b82f6',
        'electrician': '#ffd200', 'plumber': '#3b82f6',
        'carpenter': '#78716c', 'photography': '#8b5cf6',
        'events': '#8b5cf6', 'catering': '#f59e0b',
        # Education
        'education': '#06b6d4', 'coaching': '#06b6d4',
        'tuition': '#06b6d4',
        # Automotive
        'automotive': '#3b82f6', 'car': '#3b82f6',
        # Travel
        'travel': '#f59e0b', 'hotel': '#8b5cf6',
        # Finance
        'banking': '#10b981', 'finance': '#10b981',
        # Entertainment
        'entertainment': '#8b5cf6', 'art': '#ec4899',
        'henna-art': '#ec4899', 'henna': '#ec4899',
        # Real Estate
        'real-estate': '#06b6d4',
    }
    if s in colors:
        return colors[s]
    for key, color in colors.items():
        if key in s or s in key:
            return color
    # Default cycle through nice colors based on hash
    palette = ['#00d2ff','#3a7bd5','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#f97316']
    return palette[hash(s) % len(palette)]

@register.filter
def star_range(value):
    try:
        return range(int(value or 0))
    except (ValueError, TypeError):
        return range(0)

@register.filter
def empty_star_range(value):
    try:
        return range(5 - int(value or 0))
    except (ValueError, TypeError):
        return range(5)

@register.simple_tag
def get_cart_count(user):
    if not user.is_authenticated:
        return 0
    from cart.models import Cart
    cart = Cart.objects.filter(user=user).first()
    if cart:
        return sum(item.quantity for item in cart.items.all())
    return 0
