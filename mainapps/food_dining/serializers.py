"""
Food and Dining Microservice Serializers
"""

from rest_framework import serializers
from django.db import transaction
from .models import (
    CuisineType, Restaurant, MenuCategory, MenuItem, MenuItemImage,
    RestaurantImage, RestaurantOperatingHours, Table, FoodBooking,
    OrderItem, RestaurantReview
)


class CuisineTypeSerializer(serializers.ModelSerializer):
    """Serializer for cuisine types"""
    
    class Meta:
        model = CuisineType
        fields = ['id', 'name', 'slug', 'description', 'origin_country']


class MenuCategorySerializer(serializers.ModelSerializer):
    """Serializer for menu categories"""
    
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'order', 'is_active', 'items_count']
    
    def get_items_count(self, obj):
        return obj.items.filter(is_available=True).count()


class MenuItemImageSerializer(serializers.ModelSerializer):
    """Serializer for menu item images"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItemImage
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


class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for menu items"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = MenuItemImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'category_name', 'price', 'preparation_time',
            'calories', 'serving_size', 'ingredients', 'allergens',
            'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_halal',
            'is_kosher', 'is_spicy', 'spice_level', 'is_available',
            'available_from', 'available_until', 'available_days',
            'is_popular', 'is_featured', 'is_chef_special',
            'order_count', 'order', 'images'
        ]
        read_only_fields = ['order_count']


class MenuItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating menu items"""
    
    class Meta:
        model = MenuItem
        fields = [
            'name', 'slug', 'description', 'short_description', 'category',
            'price', 'cost_price', 'preparation_time', 'calories',
            'serving_size', 'ingredients', 'allergens', 'is_vegetarian',
            'is_vegan', 'is_gluten_free', 'is_halal', 'is_kosher',
            'is_spicy', 'spice_level', 'is_available', 'available_from',
            'available_until', 'available_days', 'is_popular',
            'is_featured', 'is_chef_special', 'order'
        ]
    
    def validate_slug(self, value):
        restaurant_id = self.context.get('restaurant_id')
        if self.instance:
            if MenuItem.objects.exclude(pk=self.instance.pk).filter(
                restaurant_id=restaurant_id, slug=value
            ).exists():
                raise serializers.ValidationError("Menu item with this slug already exists.")
        else:
            if MenuItem.objects.filter(restaurant_id=restaurant_id, slug=value).exists():
                raise serializers.ValidationError("Menu item with this slug already exists.")
        return value


class RestaurantImageSerializer(serializers.ModelSerializer):
    """Serializer for restaurant images"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RestaurantImage
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


class RestaurantOperatingHoursSerializer(serializers.ModelSerializer):
    """Serializer for restaurant operating hours"""
    
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RestaurantOperatingHours
        fields = [
            'id', 'day_of_week', 'day_name', 'is_closed', 'opening_time',
            'closing_time', 'lunch_opening', 'lunch_closing',
            'dinner_opening', 'dinner_closing', 'notes'
        ]
    
    def get_day_name(self, obj):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[obj.day_of_week]


class TableSerializer(serializers.ModelSerializer):
    """Serializer for restaurant tables"""
    
    class Meta:
        model = Table
        fields = [
            'id', 'table_number', 'capacity', 'location',
            'is_wheelchair_accessible', 'has_power_outlet',
            'is_quiet_area', 'is_available'
        ]


class RestaurantListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for restaurant listings"""
    
    primary_image = serializers.SerializerMethodField()
    cuisine_types_names = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'slug', 'short_description', 'restaurant_type',
            'phone', 'price_range', 'average_meal_price',
            'currency', 'average_rating', 'total_reviews', 'primary_image',
            'cuisine_types_names', 'accepts_reservations', 'offers_delivery',
            'offers_takeout', 'is_open_now', 'is_featured', 'status'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
        return None
    
    def get_cuisine_types_names(self, obj):
        return [cuisine.name for cuisine in obj.cuisine_types.all()]
    
    def get_is_open_now(self, obj):
        from django.utils import timezone
        now = timezone.now()
        current_time = now.time()
        current_day = now.weekday()
        
        operating_hours = obj.operating_hours.filter(day_of_week=current_day).first()
        if not operating_hours or operating_hours.is_closed:
            return False
        
        if operating_hours.opening_time and operating_hours.closing_time:
            return operating_hours.opening_time <= current_time <= operating_hours.closing_time
        
        return True


class RestaurantDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for restaurant"""
    
    cuisine_types = CuisineTypeSerializer(many=True, read_only=True)
    images = RestaurantImageSerializer(many=True, read_only=True)
    operating_hours = RestaurantOperatingHoursSerializer(many=True, read_only=True)
    tables = TableSerializer(many=True, read_only=True)
    menu_categories = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'restaurant_type', 'phone', 'email', 'website', 'address',
            'license_number', 'health_permit', 'seating_capacity',
            'private_dining_rooms', 'accepts_reservations', 'offers_delivery',
            'offers_takeout', 'offers_catering', 'delivery_radius',
            'minimum_order_amount', 'delivery_fee', 'free_delivery_threshold',
            'dietary_options', 'price_range', 'average_meal_price', 'currency',
            'average_rating', 'total_reviews', 'status', 'features',
            'is_active', 'is_featured', 'is_verified', 'meta_title',
            'meta_description', 'cuisine_types', 'images', 'operating_hours',
            'tables', 'menu_categories', 'recent_reviews', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'average_rating', 'total_reviews']
    
    def get_menu_categories(self, obj):
        categories = MenuCategory.objects.filter(
            items__restaurant=obj,
            is_active=True
        ).distinct().order_by('order', 'name')
        return MenuCategorySerializer(categories, many=True).data
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.filter(is_published=True)[:3]
        return RestaurantReviewSerializer(recent_reviews, many=True, context=self.context).data


class RestaurantCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating restaurants"""
    
    cuisine_types_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    operating_hours_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'slug', 'description', 'short_description', 'restaurant_type',
            'phone', 'email', 'website', 'address', 'license_number', 'health_permit',
            'seating_capacity', 'private_dining_rooms', 'accepts_reservations',
            'offers_delivery', 'offers_takeout', 'offers_catering', 'delivery_radius',
            'minimum_order_amount', 'delivery_fee', 'free_delivery_threshold',
            'dietary_options', 'price_range', 'average_meal_price', 'currency',
            'features', 'meta_title', 'meta_description', 'cuisine_types_ids',
            'operating_hours_data'
        ]
    
    def validate_slug(self, value):
        if self.instance:
            if Restaurant.objects.exclude(pk=self.instance.pk).filter(slug=value).exists():
                raise serializers.ValidationError("Restaurant with this slug already exists.")
        else:
            if Restaurant.objects.filter(slug=value).exists():
                raise serializers.ValidationError("Restaurant with this slug already exists.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        cuisine_types_ids = validated_data.pop('cuisine_types_ids', [])
        operating_hours_data = validated_data.pop('operating_hours_data', [])
        restaurant = super().create(validated_data)
        
        # Set cuisine types
        if cuisine_types_ids:
            restaurant.cuisine_types.set(cuisine_types_ids)
        
        # Create operating hours
        for hours_data in operating_hours_data:
            RestaurantOperatingHours.objects.create(
                restaurant=restaurant,
                profile_id=restaurant.profile_id,
                created_by_id=restaurant.created_by_id,
                **hours_data
            )
        
        return restaurant
    
    @transaction.atomic
    def update(self, instance, validated_data):
        cuisine_types_ids = validated_data.pop('cuisine_types_ids', None)
        operating_hours_data = validated_data.pop('operating_hours_data', None)
        restaurant = super().update(instance, validated_data)
        
        # Update cuisine types if provided
        if cuisine_types_ids is not None:
            restaurant.cuisine_types.set(cuisine_types_ids)
        
        # Update operating hours if provided
        if operating_hours_data is not None:
            restaurant.operating_hours.all().delete()
            for hours_data in operating_hours_data:
                RestaurantOperatingHours.objects.create(
                    restaurant=restaurant,
                    profile_id=restaurant.profile_id,
                    modified_by_id=restaurant.modified_by_id,
                    **hours_data
                )
        
        return restaurant


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""
    
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_price = serializers.DecimalField(source='menu_item.price', max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'menu_item_name', 'menu_item_price',
            'quantity', 'unit_price', 'total_price', 'special_instructions',
            'customizations'
        ]
        read_only_fields = ['total_price']


class FoodBookingSerializer(serializers.ModelSerializer):
    """Serializer for food bookings"""
    
    restaurant_info = RestaurantListSerializer(source='restaurant', read_only=True)
    table_info = TableSerializer(source='table', read_only=True)
    order_items = OrderItemSerializer(many=True, required=False)
    
    class Meta:
        model = FoodBooking
        fields = [
            'id', 'booking_reference', 'restaurant', 'restaurant_info',
            'booking_type', 'customer_name', 'customer_email', 'customer_phone',
            'table', 'table_info', 'reservation_date', 'reservation_time',
            'party_size', 'delivery_address', 'delivery_city', 'delivery_instructions',
            'delivery_latitude', 'delivery_longitude', 'event_date', 'event_time',
            'event_location', 'expected_guests', 'subtotal', 'delivery_fee',
            'service_charge', 'taxes', 'discount_amount', 'tip_amount',
            'total_amount', 'currency', 'status', 'payment_status',
            'special_requests', 'dietary_requirements', 'booking_date',
            'confirmation_date', 'order_items'
        ]
        read_only_fields = [
            'booking_reference', 'total_amount', 'booking_date', 'confirmation_date'
        ]
    
    def validate(self, data):
        booking_type = data.get('booking_type')
        
        if booking_type == 'reservation':
            if not data.get('reservation_date') or not data.get('reservation_time'):
                raise serializers.ValidationError(
                    "Reservation date and time are required for table reservations"
                )
        elif booking_type == 'delivery':
            if not data.get('delivery_address'):
                raise serializers.ValidationError(
                    "Delivery address is required for delivery orders"
                )
        elif booking_type == 'catering':
            if not data.get('event_date') or not data.get('event_location'):
                raise serializers.ValidationError(
                    "Event date and location are required for catering services"
                )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        booking = super().create(validated_data)
        
        # Create order items
        subtotal = 0
        for item_data in order_items_data:
            menu_item = item_data['menu_item']
            item_data['unit_price'] = menu_item.price
            order_item = OrderItem.objects.create(booking=booking, **item_data)
            subtotal += order_item.total_price
        
        # Update booking totals
        booking.subtotal = subtotal
        booking.total_amount = (
            booking.subtotal + booking.delivery_fee + booking.service_charge +
            booking.taxes + booking.tip_amount - booking.discount_amount
        )
        booking.save()
        
        return booking


class RestaurantReviewSerializer(serializers.ModelSerializer):
    """Serializer for restaurant reviews"""
    
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = RestaurantReview
        fields = [
            'id', 'restaurant', 'restaurant_name', 'reviewer_name',
            'rating', 'title', 'comment', 'food_rating', 'service_rating',
            'ambiance_rating', 'value_rating', 'delivery_rating',
            'would_recommend', 'would_order_again', 'is_verified',
            'is_published', 'response', 'response_date', 'created_at'
        ]
        read_only_fields = ['created_at', 'is_verified', 'response', 'response_date']
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
