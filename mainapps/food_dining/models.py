"""
Food and Dining Microservice Models
Handles restaurants, catering, food delivery, and bakeries bookings
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Address(models.Model):

    
    country = models.CharField(
        max_length=255,
        verbose_name=_('Country'),
        help_text=_('Country of the address'),
        null=True,
        blank=True
    )
    region = models.CharField(
        max_length=255,
        verbose_name=_('Region/State'),
        help_text=_('Region or state within the country'),
        null=True,
        blank=True
    )
    subregion = models.CharField(
        max_length=255,
        verbose_name=_('Subregion/Province'),
        help_text=_('Subregion or province within the region'),
        null=True,
        blank=True
    )
    city = models.CharField(
        max_length=255,
        verbose_name=_('City'),
        help_text=_('City of the address'),
        null=True,
        blank=True
    )
    apt_number = models.PositiveIntegerField(
        verbose_name=_('Apartment number'),
        null=True,
        blank=True
    )
    street_number = models.PositiveIntegerField(
        verbose_name=_('Street number'),
        null=True,
        blank=True
    )
    street = models.CharField(max_length=255,blank=False,null=True)

    postal_code = models.CharField(
        max_length=10,
        verbose_name=_('Postal code'),
        help_text=_('Postal code'),
        blank=True,
        null=True,
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Latitude'),
        help_text=_('Geographical latitude of the address'),
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Longitude'),
        help_text=_('Geographical longitude of the address'),
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.street}, {self.city}, {self.region}, {self.country}'

class FoodManager(models.Manager):
    """Custom manager for food and dining related models"""
    
    def for_profile(self, profile_id):
        return self.get_queryset().filter(profile_id=profile_id)
    
    def active(self):
        return self.get_queryset().filter(is_active=True)
    
    def open_now(self):
        from django.utils import timezone
        now = timezone.now()
        current_time = now.time()
        current_day = now.weekday()
        
        return self.get_queryset().filter(
            operating_hours__day_of_week=current_day,
            operating_hours__opening_time__lte=current_time,
            operating_hours__closing_time__gte=current_time,
            is_active=True
        ).distinct()


class ProfileMixin(models.Model):
    """Abstract model providing multi-tenant functionality"""
    
    profile_id = models.CharField(
        max_length=50,
        help_text="Reference to CompanyProfile ID from users service"
    )
    created_by_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Reference to User ID from users service"
    )
    modified_by_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Reference to User ID from users service"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = FoodManager()
    
    class Meta:
        abstract = True


class RestaurantType(models.TextChoices):
    RESTAURANT = 'restaurant', _('Restaurant')
    FAST_FOOD = 'fast_food', _('Fast Food')
    CAFE = 'cafe', _('Cafe')
    BAR = 'bar', _('Bar & Pub')
    BAKERY = 'bakery', _('Bakery')
    CATERING = 'catering', _('Catering Service')
    FOOD_TRUCK = 'food_truck', _('Food Truck')
    FINE_DINING = 'fine_dining', _('Fine Dining')
    BUFFET = 'buffet', _('Buffet')
    STREET_FOOD = 'street_food', _('Street Food')


class CuisineType(models.Model):
    """Types of cuisine offered"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    origin_country = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Restaurant(ProfileMixin):
    """Main restaurant/food establishment model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    restaurant_type = models.CharField(
        max_length=20,
        choices=RestaurantType.choices,
        default=RestaurantType.RESTAURANT
    )
    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Location Information
    address = models.ForeignKey(Address, on_delete=models.SET_NULL,null=True, blank=True)
    
    # Business Details
    license_number = models.CharField(max_length=100, blank=True)
    health_permit = models.CharField(max_length=100, blank=True)
    
    # Operational Details
    seating_capacity = models.PositiveIntegerField(null=True, blank=True)
    private_dining_rooms = models.PositiveIntegerField(default=0)
    
    # Service Options
    accepts_reservations = models.BooleanField(default=True)
    offers_delivery = models.BooleanField(default=False)
    offers_takeout = models.BooleanField(default=True)
    offers_catering = models.BooleanField(default=False)
    
    # Delivery Details
    delivery_radius = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Delivery radius in kilometers"
    )
    minimum_order_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    delivery_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00')
    )
    free_delivery_threshold = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Cuisine and Dietary Options
    cuisine_types = models.ManyToManyField(
        CuisineType,
        related_name='restaurants',
        blank=True
    )
    dietary_options = models.JSONField(
        default=list,
        help_text="Vegetarian, Vegan, Halal, Gluten-free, etc."
    )
    
    # Pricing
    price_range = models.CharField(
        max_length=10,
        choices=[
            ('$', _('Budget ($)')),
            ('$$', _('Moderate ($$)')),
            ('$$$', _('Expensive ($$$)')),
            ('$$$$', _('Very Expensive ($$$$)')),
        ],
        default='$$'
    )
    average_meal_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=50, null=True,blank=True)
    
    # Ratings and Reviews
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', _('Open')),
            ('closed', _('Closed')),
            ('busy', _('Busy')),
            ('temp_closed', _('Temporarily Closed')),
        ],
        default='open'
    )
    
    # Features and Amenities
    features = models.JSONField(
        default=list,
        help_text="WiFi, Parking, Outdoor Seating, etc."
    )
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile_id', 'is_active']),
            # models.Index(fields=['city', 'country']),
            models.Index(fields=['restaurant_type']),
            models.Index(fields=['is_active', 'is_featured']),
            # models.Index(fields=['offers_delivery', 'city']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"


class MenuCategory(models.Model):
    """Categories for menu items"""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Menu Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class MenuItem(ProfileMixin):
    """Menu items for restaurants"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=8, decimal_places=2)
    cost_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost to make this item"
    )
    
    # Item Details
    preparation_time = models.DurationField(null=True, blank=True)
    calories = models.PositiveIntegerField(null=True, blank=True)
    serving_size = models.CharField(max_length=100, blank=True)
    
    # Ingredients and Allergens
    ingredients = models.JSONField(default=list)
    allergens = models.JSONField(default=list)
    
    # Dietary Information
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_halal = models.BooleanField(default=False)
    is_kosher = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    spice_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Availability
    is_available = models.BooleanField(default=True)
    available_from = models.TimeField(null=True, blank=True)
    available_until = models.TimeField(null=True, blank=True)
    available_days = models.JSONField(
        default=list,
        help_text="List of available days (0=Monday, 6=Sunday)"
    )
    
    # Popularity and Features
    is_popular = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_chef_special = models.BooleanField(default=False)
    order_count = models.PositiveIntegerField(default=0)
    
    # Display Order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['category', 'order', 'name']
        unique_together = ['restaurant', 'slug']
        indexes = [
            models.Index(fields=['restaurant', 'category']),
            models.Index(fields=['is_available', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class MenuItemImage(ProfileMixin):
    """Images for menu items"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image = models.ImageField(upload_to='menu_items/%Y/%m/%d/')
    caption = models.CharField(max_length=255, blank=True)
    video =models.FileField(
        upload_to='menu_items/videos/%Y/%m/%d/',
        blank=True,
        null=True
    )
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']


class RestaurantImage(ProfileMixin):
    """Images for restaurants"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image = models.ImageField(upload_to='restaurants/%Y/%m/%d/')
    video =models.FileField(
        upload_to='restaurants/videos/%Y/%m/%d/',
        blank=True,
        null=True
    )
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']


class RestaurantOperatingHours(ProfileMixin):
    """Operating hours for restaurants"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='operating_hours'
    )
    
    day_of_week = models.PositiveIntegerField(
        choices=[
            (0, _('Monday')), (1, _('Tuesday')), (2, _('Wednesday')),
            (3, _('Thursday')), (4, _('Friday')), (5, _('Saturday')), (6, _('Sunday'))
        ]
    )
    
    is_closed = models.BooleanField(default=False)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    
    # For restaurants with split hours (lunch and dinner)
    lunch_opening = models.TimeField(null=True, blank=True)
    lunch_closing = models.TimeField(null=True, blank=True)
    dinner_opening = models.TimeField(null=True, blank=True)
    dinner_closing = models.TimeField(null=True, blank=True)
    
    # Special notes
    notes = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ['restaurant', 'day_of_week']
        ordering = ['restaurant', 'day_of_week']


class Table(ProfileMixin):
    """Restaurant tables for reservations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='tables'
    )
    
    table_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Window, patio, private room, etc."
    )
    
    # Features
    is_wheelchair_accessible = models.BooleanField(default=False)
    has_power_outlet = models.BooleanField(default=False)
    is_quiet_area = models.BooleanField(default=False)
    
    # Status
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['restaurant', 'table_number']
        ordering = ['restaurant', 'table_number']
    
    def __str__(self):
        return f"{self.restaurant.name} - Table {self.table_number}"


class BookingType(models.TextChoices):
    RESERVATION = 'reservation', _('Table Reservation')
    DELIVERY = 'delivery', _('Food Delivery')
    TAKEOUT = 'takeout', _('Takeout Order')
    CATERING = 'catering', _('Catering Service')


class BookingStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    CONFIRMED = 'confirmed', _('Confirmed')
    PREPARING = 'preparing', _('Preparing')
    READY = 'ready', _('Ready')
    OUT_FOR_DELIVERY = 'out_for_delivery', _('Out for Delivery')
    DELIVERED = 'delivered', _('Delivered')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')
    NO_SHOW = 'no_show', _('No Show')


class FoodBooking(ProfileMixin):
    """Food and dining booking records"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True)
    
    # Restaurant details
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    
    booking_type = models.CharField(
        max_length=20,
        choices=BookingType.choices,
        default=BookingType.RESERVATION
    )
    
    # Customer information (references to users service)
    customer_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service"
    )
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # Reservation Details (for table reservations)
    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    reservation_date = models.DateField(null=True, blank=True)
    reservation_time = models.TimeField(null=True, blank=True)
    party_size = models.PositiveIntegerField(default=1)
    
    # Delivery Details (for delivery orders)
    delivery_address = models.TextField(blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_instructions = models.TextField(blank=True)
    delivery_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True
    )
    delivery_longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
    )
    
    # Catering Details (for catering services)
    event_date = models.DateField(null=True, blank=True)
    event_time = models.TimeField(null=True, blank=True)
    event_location = models.TextField(blank=True)
    expected_guests = models.PositiveIntegerField(null=True, blank=True)
    
    # Order Details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    service_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    taxes = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    tip_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=50, null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    
    # Payment information (references to payment service)
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference to payment record in payment service"
    )
    payment_status = models.CharField(max_length=20, default='pending')
    
    # Special requests and notes
    special_requests = models.TextField(blank=True)
    dietary_requirements = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    booking_date = models.DateTimeField(default=timezone.now)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    preparation_start_time = models.DateTimeField(null=True, blank=True)
    ready_time = models.DateTimeField(null=True, blank=True)
    delivery_start_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['profile_id', 'status']),
            models.Index(fields=['customer_user_id']),
            models.Index(fields=['restaurant', 'booking_type']),
            models.Index(fields=['booking_reference']),
            models.Index(fields=['reservation_date', 'reservation_time']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.restaurant.name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        
        # Calculate total amount
        self.total_amount = (
            self.subtotal +
            self.delivery_fee +
            self.service_charge +
            self.taxes +
            self.tip_amount -
            self.discount_amount
        )
        
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        prefix = "FD"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}-{self.profile_id}-{suffix}"


class OrderItem(models.Model):
    """Individual items in a food order"""
    
    booking = models.ForeignKey(
        FoodBooking,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customizations
    special_instructions = models.TextField(blank=True)
    customizations = models.JSONField(
        default=dict,
        help_text="Item customizations (extra cheese, no onions, etc.)"
    )
    
    class Meta:
        ordering = ['booking', 'menu_item']
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"


class RestaurantReview(ProfileMixin):
    """Reviews and ratings for restaurants"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        FoodBooking,
        on_delete=models.CASCADE,
        related_name='review',
        null=True,
        blank=True
    )
    
    # Reviewer information (references to users service)
    reviewer_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service"
    )
    reviewer_name = models.CharField(max_length=255)
    
    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    
    # Detailed ratings
    food_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    service_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    ambiance_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    delivery_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Recommendation
    would_recommend = models.BooleanField(null=True, blank=True)
    would_order_again = models.BooleanField(null=True, blank=True)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Response from restaurant
    response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'is_published']),
            models.Index(fields=['reviewer_user_id']),
        ]
    
    def __str__(self):
        return f"Review for {self.restaurant.name} by {self.reviewer_name}"
