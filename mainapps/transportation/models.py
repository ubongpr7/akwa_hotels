"""
Transportation Microservice Models
Handles flights, buses, trains, car rentals, and ride-hailing bookings
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



class TransportationManager(models.Manager):
    """Custom manager for transportation-related models"""
    
    def for_profile(self, profile_id):
        return self.get_queryset().filter(profile_id=profile_id)
    
    def active(self):
        return self.get_queryset().filter(is_active=True)
    
    def available_for_route(self, origin, destination, date):
        return self.get_queryset().filter(
            routes__origin_city=origin,
            routes__destination_city=destination,
            schedules__departure_date=date,
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
    
    objects = TransportationManager()
    
    class Meta:
        abstract = True


class TransportationType(models.TextChoices):
    FLIGHT = 'flight', _('Flight')
    BUS = 'bus', _('Bus')
    TRAIN = 'train', _('Train')
    CAR_RENTAL = 'car_rental', _('Car Rental')
    RIDE_HAILING = 'ride_hailing', _('Ride Hailing')
    TAXI = 'taxi', _('Taxi')
    FERRY = 'ferry', _('Ferry')
    MOTORCYCLE = 'motorcycle', _('Motorcycle')


class TransportationStatus(models.TextChoices):
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
    MAINTENANCE = 'maintenance', _('Under Maintenance')
    SUSPENDED = 'suspended', _('Suspended')


class TransportationProvider(ProfileMixin):
    """Transportation service providers (airlines, bus companies, etc.)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    transportation_type = models.CharField(
        max_length=20,
        choices=TransportationType.choices
    )
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Business Information
    license_number = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    
    # Location
    address= models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    headquarters_city = models.CharField(max_length=100)
    headquarters_state = models.CharField(max_length=100)
    headquarters_country = models.CharField(max_length=100, default='Nigeria')
    
    # Ratings
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=TransportationStatus.choices,
        default=TransportationStatus.ACTIVE
    )
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['profile_id', 'transportation_type']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_transportation_type_display()})"


class Vehicle(ProfileMixin):
    """Vehicles used by transportation providers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        TransportationProvider,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    
    # Vehicle Information
    name = models.CharField(max_length=255)
    vehicle_number = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=100)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    
    # Capacity
    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()
    
    # Features
    has_wifi = models.BooleanField(default=False)
    has_ac = models.BooleanField(default=False)
    has_entertainment = models.BooleanField(default=False)
    has_charging_ports = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=TransportationStatus.choices,
        default=TransportationStatus.ACTIVE
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['provider', 'name']
        unique_together = ['provider', 'vehicle_number']
    
    def __str__(self):
        return f"{self.provider.name} - {self.name} ({self.vehicle_number})"


class Route(ProfileMixin):
    """Transportation routes between locations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        TransportationProvider,
        on_delete=models.CASCADE,
        related_name='routes'
    )
    
    name = models.CharField(max_length=255)
    route_code = models.CharField(max_length=20, blank=True)
    
    # Origin
    origin_city = models.CharField(max_length=100)
    origin_state = models.CharField(max_length=100)
    origin_terminal = models.CharField(max_length=255, blank=True)
    origin_address = models.TextField(blank=True)
    
    # Destination
    destination_city = models.CharField(max_length=100)
    destination_state = models.CharField(max_length=100)
    destination_terminal = models.CharField(max_length=255, blank=True)
    destination_address = models.TextField(blank=True)
    
    # Route Details
    distance_km = models.PositiveIntegerField(null=True, blank=True)
    estimated_duration = models.DurationField(help_text="Estimated travel time")
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=50, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['origin_city', 'destination_city']
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['origin_city', 'destination_city']),
        ]
    
    def __str__(self):
        return f"{self.origin_city} → {self.destination_city}"


class Schedule(ProfileMixin):
    """Transportation schedules for routes"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    
    # Schedule Information
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    
    # Pricing (can override route base price)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Availability
    available_seats = models.PositiveIntegerField()
    booked_seats = models.PositiveIntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', _('Scheduled')),
            ('boarding', _('Boarding')),
            ('departed', _('Departed')),
            ('arrived', _('Arrived')),
            ('cancelled', _('Cancelled')),
            ('delayed', _('Delayed')),
        ],
        default='scheduled'
    )
    
    # Special flags
    is_express = models.BooleanField(default=False)
    is_luxury = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['departure_date', 'departure_time']
        indexes = [
            models.Index(fields=['route', 'departure_date']),
            models.Index(fields=['departure_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.route} - {self.departure_date} {self.departure_time}"


class BookingStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    CONFIRMED = 'confirmed', _('Confirmed')
    CHECKED_IN = 'checked_in', _('Checked In')
    BOARDED = 'boarded', _('Boarded')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')
    NO_SHOW = 'no_show', _('No Show')


class TransportationBooking(ProfileMixin):
    """Transportation booking records"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True)
    
    # Schedule details
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    
    # Passenger information (references to users service)
    passenger_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service"
    )
    passenger_name = models.CharField(max_length=255)
    passenger_email = models.EmailField()
    passenger_phone = models.CharField(max_length=20)
    
    # Booking details
    number_of_passengers = models.PositiveIntegerField(default=1)
    seat_numbers = models.JSONField(default=list, blank=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, blank=True,null=True)
    
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
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    booking_date = models.DateTimeField(default=timezone.now)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    boarding_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['profile_id', 'status']),
            models.Index(fields=['passenger_user_id']),
            models.Index(fields=['schedule']),
            models.Index(fields=['booking_reference']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.schedule.route}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        
        # Calculate totals
        self.subtotal = self.unit_price * self.number_of_passengers
        self.total_amount = self.subtotal + self.taxes + self.fees
        
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        prefix = "TRP"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}-{self.profile_id}-{suffix}"


class PassengerDetail(models.Model):
    """Individual passenger details for bookings"""
    
    booking = models.ForeignKey(
        TransportationBooking,
        on_delete=models.CASCADE,
        related_name='passengers'
    )
    
    # Passenger Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True
    )
    
    # Travel documents
    id_type = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    
    # Seat assignment
    seat_number = models.CharField(max_length=10, blank=True)
    
    class Meta:
        ordering = ['booking', 'last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TransportationReview(ProfileMixin):
    """Reviews and ratings for transportation services"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        TransportationProvider,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        TransportationBooking,
        on_delete=models.CASCADE,
        related_name='review'
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
    punctuality_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    comfort_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    service_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Response from provider
    response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'is_published']),
            models.Index(fields=['reviewer_user_id']),
        ]
    
    def __str__(self):
        return f"Review for {self.provider.name} by {self.reviewer_name}"
