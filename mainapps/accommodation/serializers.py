"""
Accommodation Microservice Serializers
"""

from rest_framework import serializers
from django.db import transaction
from .models import (
    Accommodation, RoomType, Amenity, AccommodationAmenity,
    AccommodationImage, AccommodationAvailability, AccommodationBooking,
    AccommodationReview
)


class AmenitySerializer(serializers.ModelSerializer):
    """Serializer for amenities"""
    
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon', 'category', 'description']


class AccommodationAmenitySerializer(serializers.ModelSerializer):
    """Serializer for accommodation amenities with details"""
    
    amenity = AmenitySerializer(read_only=True)
    amenity_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AccommodationAmenity
        fields = ['id', 'amenity', 'amenity_id', 'is_free', 'additional_cost']


class AccommodationImageSerializer(serializers.ModelSerializer):
    """Serializer for accommodation images"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AccommodationImage
        fields = [
            'id', 'image', 'image_url', 'caption', 'alt_text', 
            'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room types"""
    
    images = AccommodationImageSerializer(many=True, read_only=True)
    availability_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'description', 'max_occupancy', 'bed_type',
            'room_size', 'base_price', 'weekend_price', 'total_rooms',
            'is_active', 'images', 'availability_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_availability_count(self, obj):
        # Get current available rooms (this would be calculated based on bookings)
        return obj.total_rooms


class AccommodationAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for accommodation availability"""
    
    class Meta:
        model = AccommodationAvailability
        fields = [
            'id', 'date', 'available_rooms', 'price', 'minimum_stay',
            'is_available', 'is_weekend', 'is_holiday', 'special_event'
        ]
    
    def validate(self, data):
        if data.get('available_rooms', 0) < 0:
            raise serializers.ValidationError("Available rooms cannot be negative")
        return data


class AccommodationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for accommodation listings"""
    
    primary_image = serializers.SerializerMethodField()
    amenities_count = serializers.SerializerMethodField()
    room_types_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Accommodation
        fields = [
            'id', 'name', 'slug', 'short_description', 'accommodation_type',
            'address', 'base_price', 'currency_id',
            'average_rating', 'total_reviews', 'primary_image',
            'amenities_count', 'room_types_count', 'is_featured'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
        return None
    
    def get_amenities_count(self, obj):
        return obj.amenities.count()
    
    def get_room_types_count(self, obj):
        return obj.room_types.filter(is_active=True).count()


class AccommodationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for accommodation"""
    
    room_types = RoomTypeSerializer(many=True, read_only=True)
    images = AccommodationImageSerializer(many=True, read_only=True)
    amenities = AccommodationAmenitySerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Accommodation
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'accommodation_type', 'status', 'address',  'phone',
            'email', 'website', 'average_rating', 'total_reviews',
            'base_price', 'currency_id', 'check_in_time', 'check_out_time',
            'cancellation_policy', 'house_rules', 'total_rooms', 'max_guests',
            'is_active', 'is_featured', 'is_verified', 'meta_title',
            'meta_description', 'room_types', 'images', 'amenities',
            'recent_reviews', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'average_rating', 'total_reviews']
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.filter(is_published=True)[:3]
        return AccommodationReviewSerializer(recent_reviews, many=True, context=self.context).data


class AccommodationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating accommodations"""
    
    amenities_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Accommodation
        fields = [
            'name', 'slug', 'description', 'short_description',
            'accommodation_type', 'address', 'phone', 'email',
            'website', 'base_price', 'currency_id', 'check_in_time',
            'check_out_time', 'cancellation_policy', 'house_rules',
            'total_rooms', 'max_guests', 'meta_title', 'meta_description',
            'amenities_data'
        ]
    
    def validate_slug(self, value):
        if self.instance:
            if Accommodation.objects.exclude(pk=self.instance.pk).filter(slug=value).exists():
                raise serializers.ValidationError("Accommodation with this slug already exists.")
        else:
            if Accommodation.objects.filter(slug=value).exists():
                raise serializers.ValidationError("Accommodation with this slug already exists.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        amenities_data = validated_data.pop('amenities_data', [])
        accommodation = super().create(validated_data)
        
        # Create amenity associations
        for amenity_data in amenities_data:
            AccommodationAmenity.objects.create(
                accommodation=accommodation,
                **amenity_data
            )
        
        return accommodation
    
    @transaction.atomic
    def update(self, instance, validated_data):
        amenities_data = validated_data.pop('amenities_data', None)
        accommodation = super().update(instance, validated_data)
        
        # Update amenity associations if provided
        if amenities_data is not None:
            accommodation.amenities.all().delete()
            for amenity_data in amenities_data:
                AccommodationAmenity.objects.create(
                    accommodation=accommodation,
                    **amenity_data
                )
        
        return accommodation


class AccommodationBookingSerializer(serializers.ModelSerializer):
    """Serializer for accommodation bookings"""
    
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    nights_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AccommodationBooking
        fields = [
            'id', 'booking_reference', 'accommodation', 'accommodation_name',
            'room_type', 'room_type_name', 'guest_name', 'guest_email',
            'guest_phone', 'check_in_date', 'check_out_date', 'number_of_guests',
            'number_of_rooms', 'room_rate', 'total_nights', 'subtotal',
            'taxes', 'fees', 'total_amount', 'currency_id', 'status',
            'payment_status', 'special_requests', 'booking_date',
            'confirmation_date', 'nights_count'
        ]
        read_only_fields = [
            'booking_reference', 'total_nights', 'subtotal', 'total_amount',
            'booking_date', 'confirmation_date'
        ]
    
    def get_nights_count(self, obj):
        return obj.total_nights
    
    def validate(self, data):
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError("Check-out date must be after check-in date")
            
            from datetime import date
            if check_in < date.today():
                raise serializers.ValidationError("Check-in date cannot be in the past")
        
        return data


class AccommodationReviewSerializer(serializers.ModelSerializer):
    """Serializer for accommodation reviews"""
    
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True)
    
    class Meta:
        model = AccommodationReview
        fields = [
            'id', 'accommodation', 'accommodation_name', 'reviewer_name',
            'rating', 'title', 'comment', 'cleanliness_rating',
            'location_rating', 'service_rating', 'value_rating',
            'is_verified', 'is_published', 'response', 'response_date',
            'created_at'
        ]
        read_only_fields = ['created_at', 'is_verified', 'response', 'response_date']
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
