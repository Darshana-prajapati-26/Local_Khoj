from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Avg, Count, F, FloatField
from django.utils.text import slugify
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django import forms
from math import radians, cos, sin, asin, sqrt
import json

from .models import (
    Store, StoreCategory, StoreReview, FavoriteStore, StoreGallery,
    StoreItemCategory, StoreOffer, StoreVisit, ReviewReaction, Area, City, State
)
from products.models import Product
from services.models import Service
from core.models import SearchQuery, UserInteraction, Notification
from vendor_panel.models import StoreViewLog, StoreClickLog
from accounts.models import User
from accounts.decorators import vendor_required


# ===========================
# HELPER FUNCTIONS
# ===========================

def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points on the earth (in km)"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def log_store_view(store, request):
    """Log store view for analytics"""
    ip_address = get_client_ip(request)
    StoreViewLog.objects.create(
        store=store,
        user=request.user if request.user.is_authenticated else None,
        ip_address=ip_address,
        source=request.GET.get('source', 'direct'),
        device_type=get_device_type(request)
    )
    store.total_views += 1
    store.save(update_fields=['total_views'])


def log_store_click(store, click_type, request):
    """Log store clicks"""
    ip_address = get_client_ip(request)
    StoreClickLog.objects.create(
        store=store,
        user=request.user if request.user.is_authenticated else None,
        click_type=click_type,
        ip_address=ip_address,
        device_type=get_device_type(request)
    )


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_type(request):
    """Detect device type"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'mobile' in user_agent or 'android' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'tablet'
    return 'web'


# ===========================
# STORE LISTING & SEARCH
# ===========================

def store_list(request):
    """Advanced store listing with filters"""
    stores = Store.objects.filter(is_active=True, is_verified=True)
    
    # Filtering
    category_slug = request.GET.get("category")
    if category_slug:
        stores = stores.filter(category__slug=category_slug)
    
    area_id = request.GET.get("area")
    if area_id:
        stores = stores.filter(area_id=area_id)
    
    city_id = request.GET.get("city")
    if city_id:
        stores = stores.filter(area__city_id=city_id)
    
    # Rating filter
    min_rating = request.GET.get("min_rating")
    if min_rating:
        stores = stores.filter(rating__gte=float(min_rating))
    
    # Open now filter
    if request.GET.get("open_now") == "1":
        from django.utils import timezone
        current_time = timezone.localtime().time()
        stores = stores.exclude(
            Q(opening_time__isnull=True) | Q(closing_time__isnull=True)
        ).filter(
            opening_time__lte=current_time,
            closing_time__gte=current_time
        )
    
    # Verified only
    if request.GET.get("verified_only") == "1":
        stores = stores.filter(is_verified=True)
    
    # Sorting
    sort_by = request.GET.get("sort", "-featured")
    valid_sorts = ['-featured', '-rating', '-created_at', 'name', '-total_views']
    if sort_by in valid_sorts:
        stores = stores.order_by(sort_by, '-featured')
    else:
        stores = stores.order_by('-featured', '-created_at')
    
    # Pagination
    paginator = Paginator(stores, 20)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)
    
    # Get filter options
    categories = StoreCategory.objects.filter(stores__is_active=True).distinct()
    cities = City.objects.filter(areas__store__is_active=True).distinct()
    
    context = {
        'stores': page_obj,
        'categories': categories,
        'cities': cities,
        'selected_category': category_slug,
        'selected_city': city_id,
        'selected_area': area_id,
        'selected_rating': min_rating,
        'sort_by': sort_by,
    }
    
    return render(request, 'stores/store_list.html', context)


def store_search(request):
    """Global store search with autocomplete"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Log search query
    SearchQuery.objects.create(
        query=query,
        search_type='store',
        user=request.user if request.user.is_authenticated else None,
        location=request.GET.get('location', '')
    )
    
    # Search in stores
    stores = Store.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query),
        is_active=True,
        is_verified=True
    )[:20]
    
    # Search in categories
    categories = StoreCategory.objects.filter(
        name__icontains=query
    )[:10]
    
    results = {
        'stores': [
            {
                'id': s.id,
                'name': s.name,
                'slug': s.slug,
                'category': s.category.name,
                'rating': float(s.rating),
                'url': f'/stores/{s.slug}/'
            }
            for s in stores
        ],
        'categories': [
            {
                'id': c.id,
                'name': c.name,
                'slug': c.slug,
                'url': f'/stores/?category={c.slug}'
            }
            for c in categories
        ]
    }
    
    return JsonResponse(results)


@require_GET
def autocomplete_search(request):
    """Search autocomplete API"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get suggestions from search history
    recent_searches = SearchQuery.objects.filter(
        query__icontains=query
    ).values_list('query', flat=True).distinct()[:5]
    
    # Get store name suggestions
    store_names = Store.objects.filter(
        name__icontains=query,
        is_active=True
    ).values_list('name', flat=True).distinct()[:5]
    
    # Get category suggestions
    category_names = StoreCategory.objects.filter(
        name__icontains=query
    ).values_list('name', flat=True).distinct()[:5]
    
    suggestions = list(recent_searches) + list(store_names) + list(category_names)
    
    return JsonResponse({
        'suggestions': suggestions[:10]
    })


def location_based_search(request):
    """Search stores near location"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')
    
    if not (user_lat and user_lon):
        messages.error(request, 'Location access required')
        return redirect('stores:store_list')
    
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
    except ValueError:
        messages.error(request, 'Invalid location coordinates')
        return redirect('stores:store_list')
    
    # Get stores with coordinates
    stores = Store.objects.filter(
        is_active=True,
        is_verified=True,
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    # Calculate distances and sort
    stores_with_distance = []
    for store in stores:
        distance = haversine(user_lon, user_lat, store.longitude, store.latitude)
        stores_with_distance.append((store, distance))
    
    # Sort by distance and filter (within 50km)
    stores_with_distance.sort(key=lambda x: x[1])
    nearby_stores = [(s, d) for s, d in stores_with_distance if d <= 50]
    
    paginator = Paginator(nearby_stores, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    return render(request, 'stores/nearby_stores.html', {
        'page_obj': page_obj
    })


# ===========================
# STORE DETAIL
# ===========================

def store_detail(request, slug, city=None):
    """Detailed store profile page"""
    store = get_object_or_404(Store, slug=slug, is_active=True, is_verified=True)
    
    # Log view
    log_store_view(store, request)
    
    # Get store content
    products = Product.objects.filter(store=store, is_active=True).order_by('-created_at')
    services = Service.objects.filter(store=store, is_active=True).order_by('-created_at')
    reviews = StoreReview.objects.filter(store=store, is_approved=True).order_by('-created_at')
    gallery = StoreGallery.objects.filter(store=store).order_by('display_order')
    offers = StoreOffer.objects.filter(store=store, is_active=True)
    
    # Pagination
    product_paginator = Paginator(products, 12)
    product_page = request.GET.get('product_page', 1)
    product_page_obj = product_paginator.get_page(product_page)
    
    # Review stats
    review_stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_count=Count('id')
    )
    
    rating_distribution = reviews.values('rating').annotate(count=Count('id')).order_by('rating')
    
    # Check if favorite
    is_favorite = FavoriteStore.objects.filter(
        user=request.user,
        store=store
    ).exists() if request.user.is_authenticated else False
    
    context = {
        'store': store,
        'products': product_page_obj,
        'services': services[:6],
        'reviews': reviews[:5],
        'gallery': gallery,
        'offers': offers,
        'review_stats': review_stats,
        'rating_distribution': rating_distribution,
        'is_favorite': is_favorite,
        'review_form': StoreReviewForm(),
    }
    
    return render(request, 'stores/store_detail.html', context)

# Legacy city+slug route wrapper
def store_detail_city(request, city, slug):
    return store_detail(request, slug)

def store_city_category(request, city, slug):
    stores = Store.objects.filter(is_active=True, is_verified=True, category__slug=slug)
    if city and city.lower() != 'none':
        stores = stores.filter(area__city__slug=city)
    paginator = Paginator(stores.order_by('-featured', '-created_at'), 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    return render(request, 'stores/store_list.html', {'stores': page_obj})


# ===========================
# REVIEWS
# ===========================

class StoreReviewForm(forms.ModelForm):
    class Meta:
        model = StoreReview
        fields = ['rating', 'title', 'content', 'image']
        widgets = {
            'rating': forms.RadioSelect(choices=StoreReview.RATING_CHOICES),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Review Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Your review...'}),
        }


@login_required
@require_POST
def add_store_review(request, slug):
    """Add or update store review"""
    store = get_object_or_404(Store, slug=slug, is_active=True, is_verified=True)
    
    try:
        review = StoreReview.objects.get(store=store, user=request.user)
        form = StoreReviewForm(request.POST, request.FILES, instance=review)
    except StoreReview.DoesNotExist:
        form = StoreReviewForm(request.POST, request.FILES)
    
    if form.is_valid():
        review = form.save(commit=False)
        review.store = store
        review.user = request.user
        review.save()
        
        # Recalculate store rating immediately
        from django.db.models import Avg
        qs = store.reviews.filter(is_approved=True)
        avg = qs.aggregate(avg=Avg('rating'))['avg'] or 0.0
        store.rating = round(avg, 1)
        store.total_reviews = qs.count()
        store.save(update_fields=['rating', 'total_reviews'])
        
        messages.success(request, 'Review posted successfully!')
        
        # Notify store vendor
        Notification.objects.create(
            user=store.vendor,
            notification_type='review',
            title=f'New review from {request.user.first_name or request.user.username}',
            body=f'{review.title}: {review.rating} stars',
            related_store=store
        )
    else:
        messages.error(request, 'Please fix the errors in your review.')
    
    return redirect('stores:store_detail', slug=slug)


@login_required
@require_POST
def review_reaction(request, review_id):
    """Like/Dislike a review"""
    review = get_object_or_404(StoreReview, id=review_id)
    reaction_type = request.POST.get('reaction')  # helpful or unhelpful
    
    if reaction_type not in ['helpful', 'unhelpful']:
        return JsonResponse({'error': 'Invalid reaction'}, status=400)
    
    reaction, created = ReviewReaction.objects.get_or_create(
        review=review,
        user=request.user,
        defaults={'reaction': reaction_type}
    )
    
    if not created:
        reaction.reaction = reaction_type
        reaction.save()
    
    # Update review stats
    helpful = ReviewReaction.objects.filter(review=review, reaction='helpful').count()
    unhelpful = ReviewReaction.objects.filter(review=review, reaction='unhelpful').count()
    
    review.helpful_count = helpful
    review.unhelpful_count = unhelpful
    review.save(update_fields=['helpful_count', 'unhelpful_count'])
    
    return JsonResponse({
        'helpful': helpful,
        'unhelpful': unhelpful
    })


# ===========================
# FAVORITES
# ===========================

@login_required
@login_required
def toggle_favorite(request, slug):
    """Toggle favorite store — works via GET (link) or POST (AJAX)"""
    store = get_object_or_404(Store, slug=slug, is_active=True, is_verified=True)

    obj, created = FavoriteStore.objects.get_or_create(
        user=request.user,
        store=store
    )

    if not created:
        obj.delete()
        favorited = False
    else:
        favorited = True

    # AJAX request → return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'favorited': favorited})

    # Normal link click → redirect back to store page
    if favorited:
        messages.success(request, f'"{store.name}" saved to your favourites.')
    else:
        messages.info(request, f'"{store.name}" removed from your favourites.')
    return redirect('stores:store_detail', slug=slug)


@login_required
def favorite_stores(request):
    """User's favorite stores list"""
    favorites = FavoriteStore.objects.filter(user=request.user).select_related('store')
    
    paginator = Paginator(favorites, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    return render(request, 'stores/favorite_stores.html', {
        'page_obj': page_obj
    })


# ===========================
# CONTACT & INTERACTIONS
# ===========================

@require_POST
def log_store_interaction(request, slug):
    """Log clicks on store actions (Call, WhatsApp, Website, etc)"""
    store = get_object_or_404(Store, slug=slug)
    click_type = request.POST.get('type')  # call, whatsapp, website, direction
    
    log_store_click(store, click_type, request)
    
    return JsonResponse({'status': 'logged'})


# ===========================
# VENDOR STORE MANAGEMENT
# ===========================

class StoreForm(forms.ModelForm):
    category_new = forms.CharField(required=False, label="New Category (if not listed)",
                                   widget=forms.TextInput(attrs={'placeholder': 'e.g., Art Supplies'}))
    pincode_new = forms.CharField(required=False, label="New PIN Code (6 digits)",
                                  widget=forms.TextInput(attrs={'maxlength': '6', 'pattern': r'\d{6}', 'inputmode': 'numeric', 'placeholder': 'e.g., 560001'}))
    class Meta:
        model = Store
        fields = [
            'name', 'category', 'description', 'address', 'area', 'pincode',
            'latitude', 'longitude', 'phone', 'email', 'whatsapp_number',
            'logo', 'banner', 'gst_number', 'pan_number', 'year_established',
            'opening_time', 'closing_time', 'is_open_today', 'website_url',
            'instagram_url', 'facebook_url', 'twitter_url', 'linkedin_url',
            'amenities'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'amenities': forms.CheckboxSelectMultiple(),
            'phone': forms.TextInput(attrs={'maxlength': '10', 'pattern': r'\d{10}', 'inputmode': 'numeric'}),
            'whatsapp_number': forms.TextInput(attrs={'maxlength': '10', 'pattern': r'\d{10}', 'inputmode': 'numeric'}),
            'email': forms.EmailInput(attrs={'required': 'required', 'pattern': r'^[A-Za-z0-9._%+-]+@[A-Za-z][A-Za-z0-9.-]*\.[A-Za-z]{2,}$'}),
        }

    def clean(self):
        cleaned = super().clean()
        # Handle new category creation
        cat = cleaned.get('category')
        cat_new = (cleaned.get('category_new') or '').strip()
        if not cat and cat_new:
            base_slug = slugify(cat_new or 'category')
            slug = base_slug
            counter = 1
            from .models import StoreCategory
            while StoreCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            cat_obj, _ = StoreCategory.objects.get_or_create(name=cat_new, defaults={'slug': slug})
            cleaned['category'] = cat_obj

        # Handle new PIN code creation (requires area selected)
        pin = cleaned.get('pincode')
        pin_new = (cleaned.get('pincode_new') or '').strip()
        area = cleaned.get('area')
        if not pin and pin_new:
            if not area:
                self.add_error('area', 'Select Area for new PIN code.')
            elif not pin_new.isdigit() or len(pin_new) != 6:
                self.add_error('pincode_new', 'Enter a valid 6-digit PIN code.')
            else:
                from .models import Pincode
                pin_obj, _ = Pincode.objects.get_or_create(code=pin_new, defaults={'area': area, 'city': area.city})
                # If exists without links, ensure associations
                if not pin_obj.area_id:
                    pin_obj.area = area
                if not pin_obj.city_id:
                    pin_obj.city = area.city
                pin_obj.save()
                cleaned['pincode'] = pin_obj

        return cleaned
    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip().replace(' ', '').replace('+', '')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError('Enter a valid 10-digit mobile number.')
        return phone

    def clean_whatsapp_number(self):
        num = (self.cleaned_data.get('whatsapp_number') or '').strip().replace(' ', '').replace('+', '')
        if not num:
            return ''
        if not num.isdigit() or len(num) != 10:
            raise forms.ValidationError('Enter a valid 10-digit mobile number.')
        return num

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise forms.ValidationError('Email is required.')
        import re
        pattern = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z][A-Za-z0-9.-]*\.[A-Za-z]{2,}$')
        if not pattern.match(email):
            raise forms.ValidationError('Enter a valid email like xyz123@gmail.com.')
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_email(email)
        except DjangoValidationError:
            raise forms.ValidationError('Enter a valid email like xyz123@gmail.com.')
        return email


@login_required
@vendor_required
def create_store(request):
    """Create a new store"""
    if hasattr(request.user, 'store'):
        messages.warning(request, 'You already have a store. Edit it instead.')
        return redirect('vendor:dashboard')
    
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store = form.save(commit=False)
            store.vendor = request.user
            
            # Generate unique slug
            base_slug = slugify(store.name or 'store')
            slug = base_slug
            counter = 1
            while Store.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            store.slug = slug
            store.save()
            form.save_m2m()  # Save amenities
            
            messages.success(request, 'Store created successfully!')
            return redirect('vendor:dashboard')
    else:
        form = StoreForm()
    
    return render(request, 'vendor_panel/create_store.html', {'form': form})


@login_required
@vendor_required
def edit_store(request, slug=None):
    """Edit store profile"""
    store = get_object_or_404(Store, vendor=request.user)
    
    if slug and slug != store.slug:
        return redirect('stores:edit_store', slug=store.slug)
    
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store updated successfully!')
            return redirect('stores:store_detail', slug=store.slug)
    else:
        form = StoreForm(instance=store)
    
    return render(request, 'vendor_panel/edit_store.html', {'form': form, 'store': store})


@login_required
def trending_searches(request):
    """Get trending searches"""
    from core.models import TrendingSearch
    
    trending = TrendingSearch.objects.filter(is_active=True).order_by('-search_count')[:10]
    
    return render(request, 'stores/trending_searches.html', {'trending': trending})

