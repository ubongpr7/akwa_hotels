"""
Transportation Microservice Filters
"""

import django_filters
from .models import TransportationProvider, Schedule, TransportationBooking


class TransportationProviderFilter(django_filters.FilterSet):
    """Filter for transportation providers"""
    
    transportation_type = django_filters.ChoiceFilter(
        choices=TransportationProvider.TransportationType.choices
    )
    city = django_filters.CharFilter(field_name='headquarters_city', lookup_expr='icontains')
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    is_verified = django_filters.BooleanFilter()
    
    class Meta:
        model = TransportationProvider
        fields = ['transportation_type', 'city', 'min_rating', 'is_verified']


class ScheduleFilter(django_filters.FilterSet):
    """Filter for schedules"""
    
    departure_date = django_filters.DateFilter()
    departure_date_from = django_filters.DateFilter(field_name='departure_date', lookup_expr='gte')
    departure_date_to = django_filters.DateFilter(field_name='departure_date', lookup_expr='lte')
    origin_city = django_filters.CharFilter(field_name='route__origin_city', lookup_expr='icontains')
    destination_city = django_filters.CharFilter(field_name='route__destination_city', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Schedule.status.field.choices)
    available_seats_min = django_filters.NumberFilter(field_name='available_seats', lookup_expr='gte')
    
    class Meta:
        model = Schedule
        fields = [
            'departure_date', 'departure_date_from', 'departure_date_to',
            'origin_city', 'destination_city', 'status', 'available_seats_min'
        ]


class TransportationBookingFilter(django_filters.FilterSet):
    """Filter for transportation bookings"""
    
    status = django_filters.ChoiceFilter(choices=TransportationBooking.BookingStatus.choices)
    departure_date = django_filters.DateFilter(field_name='schedule__departure_date')
    departure_from = django_filters.DateFilter(field_name='schedule__departure_date', lookup_expr='gte')
    departure_to = django_filters.DateFilter(field_name='schedule__departure_date', lookup_expr='lte')
    
    class Meta:
        model = TransportationBooking
        fields = ['status', 'departure_date', 'departure_from', 'departure_to']
