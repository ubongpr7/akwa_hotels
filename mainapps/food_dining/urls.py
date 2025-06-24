"""
Food and Dining Microservice URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CuisineTypeViewSet, RestaurantViewSet, MenuItemViewSet,
    TableViewSet, FoodBookingViewSet, RestaurantReviewViewSet
)

router = DefaultRouter()
router.register(r'cuisine-types', CuisineTypeViewSet, basename='cuisine-type')
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')
router.register(r'tables', TableViewSet, basename='table')
router.register(r'bookings', FoodBookingViewSet, basename='booking')
router.register(r'reviews', RestaurantReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
