"""
Transportation Microservice URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransportationProviderViewSet, VehicleViewSet, RouteViewSet,
    ScheduleViewSet, TransportationBookingViewSet, TransportationReviewViewSet
)

router = DefaultRouter()
router.register(r'providers', TransportationProviderViewSet, basename='provider')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'routes', RouteViewSet, basename='route')
router.register(r'schedules', ScheduleViewSet, basename='schedule')
router.register(r'bookings', TransportationBookingViewSet, basename='booking')
router.register(r'reviews', TransportationReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
