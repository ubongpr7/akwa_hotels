"""
Food and Dining Microservice Filters
"""

import django_filters
from .models import Restaurant, MenuItem, FoodBooking


class RestaurantFilter(django_filters.FilterSet):
    """Filter for restaurants"""
    
    restaurant_type = django_filters.ChoiceFilter(choices=Restaurant.RestaurantType.choices)
    # city = django_filters.CharFilter(lookup_expr='icontains')
    cuisine_type = django_filters.ModelMultipleChoiceFilter(
        field_name='cuisine_types',
        to_field_name='slug',
        queryset=None  # Will be set in __init__
    )
    price_range = django_filters.ChoiceFilter(choices=Restaurant.price_range.field.choices)
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    offers_delivery = django_filters.BooleanFilter()
    offers_takeout = django_filters.BooleanFilter()
    accepts_reservations = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    
    class Meta:
        model = Restaurant
        fields = [
            'restaurant_type', 'cuisine_type', 'price_range',
            'min_rating', 'offers_delivery', 'offers_takeout',
            'accepts_reservations', 'is_featured'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import CuisineType
        self.filters['cuisine_type'].queryset = CuisineType.objects.all()


class MenuItemFilter(django_filters.FilterSet):
    """Filter for menu items"""
    
    category = django_filters.ModelChoiceFilter(queryset=None)  # Will be set in __init__
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_vegetarian = django_filters.BooleanFilter()
    is_vegan = django_filters.BooleanFilter()
    is_gluten_free = django_filters.BooleanFilter()
    is_halal = django_filters.BooleanFilter()
    is_spicy = django_filters.BooleanFilter()
    is_popular = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    is_available = django_filters.BooleanFilter()
    
    class Meta:
        model = MenuItem
        fields = [
            'category', 'min_price', 'max_price', 'is_vegetarian',
            'is_vegan', 'is_gluten_free', 'is_halal', 'is_spicy',
            'is_popular', 'is_featured', 'is_available'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import MenuCategory
        self.filters['category'].queryset = MenuCategory.objects.all()


class FoodBookingFilter(django_filters.FilterSet):
    """Filter for food bookings"""
    
    booking_type = django_filters.ChoiceFilter(choices=FoodBooking.BookingType.choices)
    status = django_filters.ChoiceFilter(choices=FoodBooking.BookingStatus.choices)
    restaurant = django_filters.ModelChoiceFilter(queryset=Restaurant.objects.all())
    reservation_date = django_filters.DateFilter()
    reservation_from = django_filters.DateFilter(field_name='reservation_date', lookup_expr='gte')
    reservation_to = django_filters.DateFilter(field_name='reservation_date', lookup_expr='lte')
    
    class Meta:
        model = FoodBooking
        fields = [
            'booking_type', 'status', 'restaurant', 'reservation_date',
            'reservation_from', 'reservation_to'
        ]
