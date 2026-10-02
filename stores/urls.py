from django.urls import path
from . import views

app_name = 'stores'

urlpatterns = [
    # Store Listing & Search
    path('', views.store_list, name='store_list'),
    path('search/', views.store_search, name='store_search'),
    path('autocomplete/', views.autocomplete_search, name='autocomplete_search'),
    path('nearby/', views.location_based_search, name='nearby_stores'),
    path('trending/', views.trending_searches, name='trending_searches'),
    
    # Store Detail & Management
    path('store/<slug:slug>/', views.store_detail, name='store_detail'),
    path('store/<slug:slug>/edit/', views.edit_store, name='edit_store'),
    path('create/', views.create_store, name='create_store'),
    
    # Reviews
    path('store/<slug:slug>/review/', views.add_store_review, name='add_store_review'),
    path('review/<int:review_id>/reaction/', views.review_reaction, name='review_reaction'),
    
    # Favorites
    path('store/<slug:slug>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorite_stores, name='favorite_stores'),
    
    # Tracking
    path('store/<slug:slug>/click/', views.log_store_interaction, name='log_interaction'),
    
    # Legacy support: city + category slug -> listing
    path('<slug:city>/<slug:slug>/', views.store_city_category, name='city_category'),
]

