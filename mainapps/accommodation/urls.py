"""
Accommodation Microservice URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AccommodationViewSet, RoomTypeViewSet, AmenityViewSet,
    AccommodationBookingViewSet, AccommodationReviewViewSet
)

router = DefaultRouter()
router.register(r'accommodations', AccommodationViewSet, basename='accommodation')
router.register(r'room-types', RoomTypeViewSet, basename='roomtype')
router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'bookings', AccommodationBookingViewSet, basename='booking')
router.register(r'reviews', AccommodationReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
