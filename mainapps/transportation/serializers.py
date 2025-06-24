"""
Transportation Microservice Serializers
"""

from rest_framework import serializers
from django.db import transaction
from .models import (
    TransportationProvider, Vehicle, Route, Schedule,
    TransportationBooking, PassengerDetail, TransportationReview
)


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for vehicles"""
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'name', 'vehicle_number', 'vehicle_type', 'make', 'model',
            'year', 'total_seats', 'available_seats', 'has_wifi', 'has_ac',
            'has_entertainment', 'has_charging_ports', 'status', 'is_active'
        ]


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for routes"""
    
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'provider', 'provider_name', 'name', 'route_code',
            'origin_city', 'origin_state', 'origin_terminal', 'origin_address',
            'destination_city', 'destination_state', 'destination_terminal',
            'destination_address', 'distance_km', 'estimated_duration',
            'base_price', 'currency', 'is_active'
        ]


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for schedules"""
    
    route_info = RouteSerializer(source='route', read_only=True)
    vehicle_info = VehicleSerializer(source='vehicle', read_only=True)
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'route', 'route_info', 'vehicle', 'vehicle_info',
            'departure_date', 'departure_time', 'arrival_time', 'price',
            'available_seats', 'booked_seats', 'status', 'is_express', 'is_luxury'
        ]


class TransportationProviderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for provider listings"""
    
    routes_count = serializers.SerializerMethodField()
    vehicles_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TransportationProvider
        fields = [
            'id', 'name', 'slug', 'transportation_type', 'headquarters_city',
            'headquarters_state', 'average_rating', 'total_reviews',
            'is_verified', 'routes_count', 'vehicles_count'
        ]
    
    def get_routes_count(self, obj):
        return obj.routes.filter(is_active=True).count()
    
    def get_vehicles_count(self, obj):
        return obj.vehicles.filter(is_active=True).count()


class TransportationProviderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for transportation provider"""
    
    vehicles = VehicleSerializer(many=True, read_only=True)
    routes = RouteSerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = TransportationProvider
        fields = [
            'id', 'name', 'slug', 'description', 'transportation_type',
            'phone', 'email', 'website', 'license_number', 'registration_number',
            'headquarters_city', 'headquarters_state', 'headquarters_country',
            'average_rating', 'total_reviews', 'status', 'is_verified',
            'is_active', 'vehicles', 'routes', 'recent_reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'average_rating', 'total_reviews']
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.filter(is_published=True)[:3]
        return TransportationReviewSerializer(recent_reviews, many=True, context=self.context).data


class PassengerDetailSerializer(serializers.ModelSerializer):
    """Serializer for passenger details"""
    
    class Meta:
        model = PassengerDetail
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'id_type', 'id_number', 'seat_number'
        ]


class TransportationBookingSerializer(serializers.ModelSerializer):
    """Serializer for transportation bookings"""
    
    schedule_info = ScheduleSerializer(source='schedule', read_only=True)
    passengers = PassengerDetailSerializer(many=True, required=False)
    
    class Meta:
        model = TransportationBooking
        fields = [
            'id', 'booking_reference', 'schedule', 'schedule_info',
            'passenger_name', 'passenger_email', 'passenger_phone',
            'number_of_passengers', 'seat_numbers', 'unit_price',
            'subtotal', 'taxes', 'fees', 'total_amount', 'currency',
            'status', 'payment_status', 'special_requests',
            'booking_date', 'confirmation_date', 'passengers'
        ]
        read_only_fields = [
            'booking_reference', 'subtotal', 'total_amount',
            'booking_date', 'confirmation_date'
        ]
    
    @transaction.atomic
    def create(self, validated_data):
        passengers_data = validated_data.pop('passengers', [])
        booking = super().create(validated_data)
        
        # Create passenger details
        for passenger_data in passengers_data:
            PassengerDetail.objects.create(booking=booking, **passenger_data)
        
        return booking


class TransportationReviewSerializer(serializers.ModelSerializer):
    """Serializer for transportation reviews"""
    
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    
    class Meta:
        model = TransportationReview
        fields = [
            'id', 'provider', 'provider_name', 'reviewer_name',
            'rating', 'title', 'comment', 'punctuality_rating',
            'comfort_rating', 'service_rating', 'value_rating',
            'is_verified', 'is_published', 'response', 'response_date',
            'created_at'
        ]
        read_only_fields = ['created_at', 'is_verified', 'response', 'response_date']
