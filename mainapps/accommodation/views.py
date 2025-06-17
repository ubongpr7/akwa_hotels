"""
Accommodation Microservice Views
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Accommodation, RoomType, Amenity, AccommodationImage,
    AccommodationAvailability, AccommodationBooking, AccommodationReview
)
from .serializers import (
    AccommodationListSerializer, AccommodationDetailSerializer,
    AccommodationCreateUpdateSerializer, RoomTypeSerializer,
    AmenitySerializer, AccommodationImageSerializer,
    AccommodationAvailabilitySerializer, AccommodationBookingSerializer,
    AccommodationReviewSerializer
)
from .filters import AccommodationFilter, AccommodationBookingFilter
from .permissions import IsOwnerOrReadOnly, IsProfileMember


class AccommodationViewSet(viewsets.ModelViewSet):
    """ViewSet for accommodation management"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AccommodationFilter
    search_fields = ['name', 'description',]
    ordering_fields = ['created_at', 'average_rating', 'base_price', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Accommodation.objects.select_related().prefetch_related(
            'room_types', 'images', 'amenities__amenity'
        )
        
        # Filter by profile for authenticated users
        if self.request.user.is_authenticated:
            profile_id = self.request.headers.get('X-Profile-ID')
            if profile_id and self.action in ['create', 'update', 'partial_update', 'destroy']:
                queryset = queryset.filter(profile_id=profile_id)
        
        # Public listings for read operations
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AccommodationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AccommodationCreateUpdateSerializer
        return AccommodationDetailSerializer
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )
    
    def perform_update(self, serializer):
        user_id = str(self.request.user.id)
        serializer.save(modified_by_id=user_id)
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get availability for specific dates"""
        accommodation = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        availability = AccommodationAvailability.objects.filter(
            accommodation=accommodation,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        serializer = AccommodationAvailabilitySerializer(availability, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        """Upload multiple images for accommodation"""
        accommodation = self.get_object()
        images = request.FILES.getlist('images')
        
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_images = []
        for i, image in enumerate(images):
            image_data = {
                'image': image,
                'caption': request.data.get(f'caption_{i}', ''),
                'alt_text': request.data.get(f'alt_text_{i}', ''),
                'order': request.data.get(f'order_{i}', i)
            }
            
            image_instance = AccommodationImage.objects.create(
                accommodation=accommodation,
                profile_id=accommodation.profile_id,
                created_by_id=str(request.user.id),
                **image_data
            )
            created_images.append(image_instance)
        
        serializer = AccommodationImageSerializer(created_images, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get reviews for accommodation"""
        accommodation = self.get_object()
        reviews = accommodation.reviews.filter(is_published=True).order_by('-created_at')
        
        # Pagination
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = AccommodationReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = AccommodationReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured accommodations"""
        featured = self.get_queryset().filter(is_featured=True)[:10]
        serializer = AccommodationListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for accommodations"""
        queryset = self.get_queryset()
        
        # Location search
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(address__city=city)
        
        # Date availability
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')
        if check_in and check_out:
            # Add availability filtering logic here
            pass
        
        # Price range
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        
        # Amenities
        amenities = request.query_params.getlist('amenities')
        if amenities:
            queryset = queryset.filter(amenities__amenity__id__in=amenities).distinct()
        
        # Rating
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AccommodationListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = AccommodationListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class RoomTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for room type management"""
    
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated, IsProfileMember]
    filter_backends = [filters.OrderingFilter]
    ordering = ['accommodation', 'name']
    
    def get_queryset(self):
        profile_id = self.request.headers.get('X-Profile-ID')
        return RoomType.objects.filter(profile_id=profile_id).select_related('accommodation')
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for amenities (read-only)"""
    
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category']
    ordering = ['category', 'name']


class AccommodationBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for accommodation bookings"""
    
    serializer_class = AccommodationBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AccommodationBookingFilter
    ordering = ['-booking_date']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        # Users can see their own bookings or bookings for their profile
        queryset = AccommodationBooking.objects.select_related(
            'accommodation', 'room_type'
        )
        
        if profile_id:
            # Profile members can see all bookings for their accommodations
            return queryset.filter(
                Q(guest_user_id=user_id) | Q(profile_id=profile_id)
            )
        else:
            # Regular users can only see their own bookings
            return queryset.filter(guest_user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        serializer.save(
            guest_user_id=user_id,
            profile_id=profile_id or 'customer',
            created_by_id=user_id
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking"""
        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {'error': 'Only pending bookings can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'confirmed'
        booking.confirmation_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed or already cancelled booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.cancellation_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)


class AccommodationReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for accommodation reviews"""
    
    serializer_class = AccommodationReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        queryset = AccommodationReview.objects.select_related('accommodation', 'booking')
        
        if profile_id:
            # Profile members can see all reviews for their accommodations
            return queryset.filter(
                Q(reviewer_user_id=user_id) | Q(profile_id=profile_id)
            )
        else:
            # Regular users can only see their own reviews
            return queryset.filter(reviewer_user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        serializer.save(
            reviewer_user_id=user_id,
            reviewer_name=self.request.user.get_full_name or self.request.user.email,
            profile_id=profile_id or 'customer',
            created_by_id=user_id
        )
