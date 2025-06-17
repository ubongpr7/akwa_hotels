"""
Accommodation Microservice Models
Handles hotels, vacation rentals, hostels, and other accommodation bookings
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

class AccommodationManager(models.Manager):
    """Custom manager for accommodation-related models"""
    
    def for_profile(self, profile_id):
        return self.get_queryset().filter(profile_id=profile_id)
    
    def active(self):
        return self.get_queryset().filter(is_active=True)
    
    def available_for_dates(self, check_in, check_out):
        return self.get_queryset().filter(
            is_active=True,
            availability__date__range=[check_in, check_out],
            availability__is_available=True
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
    
    objects = AccommodationManager()
    
    class Meta:
        abstract = True


class AccommodationType(models.TextChoices):
    HOTEL = 'hotel', _('Hotel')
    VACATION_RENTAL = 'vacation_rental', _('Vacation Rental')
    HOSTEL = 'hostel', _('Hostel')
    APARTMENT = 'apartment', _('Apartment')
    VILLA = 'villa', _('Villa')
    RESORT = 'resort', _('Resort')
    GUESTHOUSE = 'guesthouse', _('Guest House')
    BED_AND_BREAKFAST = 'bnb', _('Bed & Breakfast')


class AccommodationStatus(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
    SUSPENDED = 'suspended', _('Suspended')
    ARCHIVED = 'archived', _('Archived')


class Accommodation(ProfileMixin):
    """Main accommodation model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    accommodation_type = models.CharField(
        max_length=20,
        choices=AccommodationType.choices,
        default=AccommodationType.HOTEL
    )
    
    status = models.CharField(
        max_length=20,
        choices=AccommodationStatus.choices,
        default=AccommodationStatus.DRAFT
    )
    
    # Location Information
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name='accommodations',
        null=True,
        blank=True,
        help_text="Reference to Address model"
    )
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Ratings and Reviews
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base price per night"
    )
    currency_id = models.CharField(max_length=255, null=True, blank=True, help_text="Reference to Currency ID from currency service")
    
    # Policies
    check_in_time = models.TimeField(default='14:00')
    check_out_time = models.TimeField(default='11:00')
    cancellation_policy = models.TextField(blank=True)
    house_rules = models.TextField(blank=True)
    
    # Features
    total_rooms = models.PositiveIntegerField(default=1)
    max_guests = models.PositiveIntegerField(default=2)
    
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
            models.Index(fields=['profile_id', 'status']),
            models.Index(fields=['accommodation_type']),
            models.Index(fields=['is_active', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.name}"


class RoomType(ProfileMixin):
    """Different room types within an accommodation"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='room_types'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Room specifications
    max_occupancy = models.PositiveIntegerField(default=2)
    bed_type = models.CharField(max_length=100, blank=True)
    room_size = models.PositiveIntegerField(null=True, blank=True, help_text="Size in square meters")
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    weekend_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Availability
    total_rooms = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['accommodation', 'name']
        unique_together = ['accommodation', 'name']
    
    def __str__(self):
        return f"{self.accommodation.name} - {self.name}"


class Amenity(models.Model):
    """Amenities available at accommodations"""
    
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name


class AccommodationAmenity(models.Model):
    """Many-to-many relationship between accommodations and amenities"""
    
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='amenities'
    )
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    is_free = models.BooleanField(default=True)
    additional_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ['accommodation', 'amenity']


class AccommodationImage(ProfileMixin):
    """Images for accommodations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='images'
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='images'
    )
    
    image = models.ImageField(upload_to='accommodations/%Y/%m/%d/')
    video =models.FileField(
        upload_to='accommodations/videos/%Y/%m/%d/',
        blank=True,
        null=True
    )
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'created_at']


class AccommodationAvailability(ProfileMixin):
    """Daily availability and pricing for accommodations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='availability'
    )
    
    date = models.DateField()
    available_rooms = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stay = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    
    # Special pricing
    is_weekend = models.BooleanField(default=False)
    is_holiday = models.BooleanField(default=False)
    special_event = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ['accommodation', 'room_type', 'date']
        indexes = [
            models.Index(fields=['accommodation', 'date']),
            models.Index(fields=['date', 'is_available']),
        ]


class BookingStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    CONFIRMED = 'confirmed', _('Confirmed')
    CHECKED_IN = 'checked_in', _('Checked In')
    CHECKED_OUT = 'checked_out', _('Checked Out')
    CANCELLED = 'cancelled', _('Cancelled')
    NO_SHOW = 'no_show', _('No Show')


class AccommodationBooking(ProfileMixin):
    """Booking records for accommodations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True)
    
    # Accommodation details
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bookings'
    )
    
    # Guest information (references to users service)
    guest_user_id = models.CharField(
        max_length=50,
        help_text="Reference to User ID from users service",
        null=True,
        blank=True
    )
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20)
    
    # Booking details
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField(default=1)
    number_of_rooms = models.PositiveIntegerField(default=1)
    
    # Pricing
    room_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_nights = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency_id = models.CharField(max_length=255, null=True, blank=True, help_text="Reference to Currency ID from currency service")
    
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
    check_out_time = models.DateTimeField(null=True, blank=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['profile_id', 'status']),
            models.Index(fields=['guest_user_id']),
            models.Index(fields=['check_in_date', 'check_out_date']),
            models.Index(fields=['booking_reference']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.accommodation.name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        
        # Calculate totals
        self.total_nights = (self.check_out_date - self.check_in_date).days
        self.subtotal = self.room_rate * self.total_nights * self.number_of_rooms
        self.total_amount = self.subtotal + self.taxes + self.fees
        
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        prefix = "ACC"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}{self.profile_id}{suffix}"


class AccommodationReview(ProfileMixin):
    """Reviews and ratings for accommodations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        AccommodationBooking,
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
    cleanliness_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    location_rating = models.PositiveIntegerField(
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
    
    # Response from accommodation
    response = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['accommodation', 'is_published']),
            models.Index(fields=['reviewer_user_id']),
        ]
    
    def __str__(self):
        return f"Review for {self.accommodation.name} by {self.reviewer_name}"
