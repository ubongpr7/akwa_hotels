"""
Accommodation Microservice Filters
"""

import django_filters
from django.db.models import Q
from .models import Accommodation, AccommodationBooking, AccommodationType, BookingStatus


class AccommodationFilter(django_filters.FilterSet):
    """Filter for accommodations"""
    
    city = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(lookup_expr='icontains')
    accommodation_type = django_filters.ChoiceFilter(choices=AccommodationType.choices)
    min_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='lte')
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    is_featured = django_filters.BooleanFilter()
    amenities = django_filters.ModelMultipleChoiceFilter(
        field_name='amenities__amenity',
        to_field_name='id',
        queryset=None  # Will be set in __init__
    )
    
    class Meta:
        model = Accommodation
        fields = [
            'city', 'state', 'accommodation_type', 'min_price', 'max_price',
            'min_rating', 'is_featured', 'amenities'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Amenity
        self.filters['amenities'].queryset = Amenity.objects.all()


class AccommodationBookingFilter(django_filters.FilterSet):
    """Filter for accommodation bookings"""
    
    status = django_filters.ChoiceFilter(choices=BookingStatus.choices)
    check_in_from = django_filters.DateFilter(field_name='check_in_date', lookup_expr='gte')
    check_in_to = django_filters.DateFilter(field_name='check_in_date', lookup_expr='lte')
    accommodation = django_filters.ModelChoiceFilter(queryset=Accommodation.objects.all())
    
    class Meta:
        model = AccommodationBooking
        fields = ['status', 'check_in_from', 'check_in_to', 'accommodation']
