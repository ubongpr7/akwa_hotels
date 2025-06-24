"""
Food and Dining Microservice Views
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    CuisineType, Restaurant, MenuCategory, MenuItem, Table,
    FoodBooking, RestaurantReview
)
from .serializers import (
    CuisineTypeSerializer, RestaurantListSerializer, RestaurantDetailSerializer,
    RestaurantCreateUpdateSerializer, MenuCategorySerializer, MenuItemSerializer,
    MenuItemCreateUpdateSerializer, TableSerializer, FoodBookingSerializer,
    RestaurantReviewSerializer
)
from .filters import RestaurantFilter, MenuItemFilter, FoodBookingFilter
from .permissions import IsOwnerOrReadOnly, IsProfileMember


class CuisineTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for cuisine types"""
    
    queryset = CuisineType.objects.all()
    serializer_class = CuisineTypeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'origin_country']
    ordering = ['name']


class RestaurantViewSet(viewsets.ModelViewSet):
    """ViewSet for restaurant management"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RestaurantFilter
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['created_at', 'average_rating', 'name', 'average_meal_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Restaurant.objects.prefetch_related(
            'cuisine_types', 'images', 'operating_hours'
        )
        
        if self.request.user.is_authenticated:
            profile_id = self.request.headers.get('X-Profile-ID')
            if profile_id and self.action in ['create', 'update', 'partial_update', 'destroy']:
                queryset = queryset.filter(profile_id=profile_id)
        
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RestaurantListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RestaurantCreateUpdateSerializer
        return RestaurantDetailSerializer
    
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
    def menu(self, request, pk=None):
        """Get full menu for restaurant"""
        restaurant = self.get_object()
        categories = MenuCategory.objects.filter(
            items__restaurant=restaurant,
            is_active=True
        ).distinct().prefetch_related('items').order_by('order', 'name')
        
        menu_data = []
        for category in categories:
            items = category.items.filter(
                restaurant=restaurant,
                is_available=True
            ).order_by('order', 'name')
            
            category_data = MenuCategorySerializer(category).data
            category_data['items'] = MenuItemSerializer(
                items, many=True, context={'request': request}
            ).data
            menu_data.append(category_data)
        
        return Response(menu_data)
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Check table availability for reservation"""
        restaurant = self.get_object()
        date = request.query_params.get('date')
        time = request.query_params.get('time')
        party_size = request.query_params.get('party_size', 1)
        
        if not date or not time:
            return Response(
                {'error': 'date and time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reservation_date = datetime.strptime(date, '%Y-%m-%d').date()
            reservation_time = datetime.strptime(time, '%H:%M').time()
            party_size = int(party_size)
        except ValueError:
            return Response(
                {'error': 'Invalid date/time format or party size'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get available tables
        available_tables = restaurant.tables.filter(
            capacity__gte=party_size,
            is_available=True
        ).exclude(
            bookings__reservation_date=reservation_date,
            bookings__reservation_time=reservation_time,
            bookings__status__in=['confirmed', 'checked_in']
        )
        
        serializer = TableSerializer(available_tables, many=True)
        return Response({
            'available_tables': serializer.data,
            'total_available': available_tables.count()
        })
    
    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        """Upload multiple images for restaurant"""
        restaurant = self.get_object()
        images = request.FILES.getlist('images')
        
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .models import RestaurantImage
        created_images = []
        for i, image in enumerate(images):
            image_data = {
                'image': image,
                'caption': request.data.get(f'caption_{i}', ''),
                'alt_text': request.data.get(f'alt_text_{i}', ''),
                'order': request.data.get(f'order_{i}', i)
            }
            
            image_instance = RestaurantImage.objects.create(
                restaurant=restaurant,
                profile_id=restaurant.profile_id,
                created_by_id=str(request.user.id),
                **image_data
            )
            created_images.append(image_instance)
        
        from .serializers import RestaurantImageSerializer
        serializer = RestaurantImageSerializer(created_images, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured restaurants"""
        featured = self.get_queryset().filter(is_featured=True)[:10]
        serializer = RestaurantListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def open_now(self, request):
        """Get restaurants that are currently open"""
        open_restaurants = self.get_queryset().open_now()
        page = self.paginate_queryset(open_restaurants)
        if page is not None:
            serializer = RestaurantListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = RestaurantListSerializer(open_restaurants, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for restaurants"""
        queryset = self.get_queryset()
        
        # Location search
        # city = request.query_params.get('city')
        # if city:
        #     queryset = queryset.filter(city__icontains=city)
        
        # Cuisine type
        cuisine = request.query_params.get('cuisine')
        if cuisine:
            queryset = queryset.filter(cuisine_types__slug=cuisine)
        
        # Restaurant type
        restaurant_type = request.query_params.get('type')
        if restaurant_type:
            queryset = queryset.filter(restaurant_type=restaurant_type)
        
        # Price range
        price_range = request.query_params.get('price_range')
        if price_range:
            queryset = queryset.filter(price_range=price_range)
        
        # Delivery options
        offers_delivery = request.query_params.get('delivery')
        if offers_delivery == 'true':
            queryset = queryset.filter(offers_delivery=True)
        
        # Rating
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        # Dietary options
        dietary = request.query_params.getlist('dietary')
        if dietary:
            for diet in dietary:
                queryset = queryset.filter(dietary_options__contains=[diet])
        
        # Open now
        open_now = request.query_params.get('open_now')
        if open_now == 'true':
            queryset = queryset.open_now()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RestaurantListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = RestaurantListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class MenuItemViewSet(viewsets.ModelViewSet):
    """ViewSet for menu item management"""
    
    permission_classes = [IsAuthenticated, IsProfileMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MenuItemFilter
    search_fields = ['name', 'description', 'ingredients']
    ordering_fields = ['name', 'price', 'order', 'order_count']
    ordering = ['category', 'order', 'name']
    
    def get_queryset(self):
        profile_id = self.request.headers.get('X-Profile-ID')
        return MenuItem.objects.filter(
            profile_id=profile_id
        ).select_related('restaurant', 'category').prefetch_related('images')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MenuItemCreateUpdateSerializer
        return MenuItemSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ['create', 'update', 'partial_update']:
            restaurant_id = self.request.data.get('restaurant')
            context['restaurant_id'] = restaurant_id
        return context
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )
    
    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        """Upload images for menu item"""
        menu_item = self.get_object()
        images = request.FILES.getlist('images')
        
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .models import MenuItemImage
        from .serializers import MenuItemImageSerializer
        
        created_images = []
        for i, image in enumerate(images):
            image_data = {
                'image': image,
                'caption': request.data.get(f'caption_{i}', ''),
                'alt_text': request.data.get(f'alt_text_{i}', ''),
                'order': request.data.get(f'order_{i}', i)
            }
            
            image_instance = MenuItemImage.objects.create(
                menu_item=menu_item,
                profile_id=menu_item.profile_id,
                created_by_id=str(request.user.id),
                **image_data
            )
            created_images.append(image_instance)
        
        serializer = MenuItemImageSerializer(created_images, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TableViewSet(viewsets.ModelViewSet):
    """ViewSet for table management"""
    
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated, IsProfileMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['table_number', 'location']
    ordering = ['restaurant', 'table_number']
    
    def get_queryset(self):
        profile_id = self.request.headers.get('X-Profile-ID')
        return Table.objects.filter(profile_id=profile_id).select_related('restaurant')
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )


class FoodBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for food bookings"""
    
    serializer_class = FoodBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = FoodBookingFilter
    ordering = ['-booking_date']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        queryset = FoodBooking.objects.select_related(
            'restaurant', 'table'
        ).prefetch_related('order_items__menu_item')
        
        if profile_id:
            return queryset.filter(
                Q(customer_user_id=user_id) | Q(profile_id=profile_id)
            )
        else:
            return queryset.filter(customer_user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        serializer.save(
            customer_user_id=user_id,
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
        if booking.status in ['completed', 'delivered', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed, delivered or already cancelled booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.cancellation_date = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update booking status (for restaurant staff)"""
        booking = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_statuses = [choice[0] for choice in FoodBooking.BookingStatus.choices]
        if new_status not in valid_statuses:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = new_status
        
        # Update timestamps based on status
        if new_status == 'preparing':
            booking.preparation_start_time = timezone.now()
        elif new_status == 'ready':
            booking.ready_time = timezone.now()
        elif new_status == 'out_for_delivery':
            booking.delivery_start_time = timezone.now()
        elif new_status in ['delivered', 'completed']:
            booking.completion_time = timezone.now()
        
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)


class RestaurantReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for restaurant reviews"""
    
    serializer_class = RestaurantReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        queryset = RestaurantReview.objects.select_related('restaurant', 'booking')
        
        if profile_id:
            return queryset.filter(
                Q(reviewer_user_id=user_id) | Q(profile_id=profile_id)
            )
        else:
            return queryset.filter(reviewer_user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        serializer.save(
            reviewer_user_id=user_id,
            reviewer_name=self.request.user.get_full_name() or self.request.user.email,
            profile_id=profile_id or 'customer',
            created_by_id=user_id
        )
