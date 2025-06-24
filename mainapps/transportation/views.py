"""
Transportation Microservice Views
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime

from .models import (
    TransportationProvider, Vehicle, Route, Schedule,
    TransportationBooking, PassengerDetail, TransportationReview
)
from .serializers import (
    TransportationProviderListSerializer, TransportationProviderDetailSerializer,
    VehicleSerializer, RouteSerializer, ScheduleSerializer,
    TransportationBookingSerializer, TransportationReviewSerializer
)
from .filters import TransportationProviderFilter, ScheduleFilter, TransportationBookingFilter


class TransportationProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for transportation provider management"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TransportationProviderFilter
    search_fields = ['name', 'description', 'headquarters_city']
    ordering_fields = ['created_at', 'average_rating', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = TransportationProvider.objects.prefetch_related(
            'vehicles', 'routes'
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
            return TransportationProviderListSerializer
        return TransportationProviderDetailSerializer
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )
    
    @action(detail=True, methods=['get'])
    def routes(self, request, pk=None):
        """Get routes for a provider"""
        provider = self.get_object()
        routes = provider.routes.filter(is_active=True)
        serializer = RouteSerializer(routes, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
        """Get schedules for a provider"""
        provider = self.get_object()
        date = request.query_params.get('date')
        
        schedules = Schedule.objects.filter(
            route__provider=provider,
            status='scheduled'
        )
        
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                schedules = schedules.filter(departure_date=date_obj)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = ScheduleSerializer(schedules, many=True, context={'request': request})
        return Response(serializer.data)


class VehicleViewSet(viewsets.ModelViewSet):
    """ViewSet for vehicle management"""
    
    serializer_class = VehicleSerializer
    # permission_classes = [IsAuthenticated, IsProfileMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'vehicle_number', 'vehicle_type']
    ordering = ['provider', 'name']
    
    def get_queryset(self):
        profile_id = self.request.headers.get('X-Profile-ID')
        return Vehicle.objects.filter(profile_id=profile_id).select_related('provider')
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )


class RouteViewSet(viewsets.ModelViewSet):
    """ViewSet for route management"""
    
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'origin_city', 'destination_city']
    ordering = ['origin_city', 'destination_city']
    
    def get_queryset(self):
        queryset = Route.objects.select_related('provider')
        
        if self.request.user.is_authenticated:
            profile_id = self.request.headers.get('X-Profile-ID')
            if profile_id and self.action in ['create', 'update', 'partial_update', 'destroy']:
                queryset = queryset.filter(profile_id=profile_id)
        
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )
    
    @action(detail=False, methods=['get'])
    def search_routes(self, request):
        """Search routes by origin and destination"""
        origin = request.query_params.get('origin')
        destination = request.query_params.get('destination')
        date = request.query_params.get('date')
        
        if not origin or not destination:
            return Response(
                {'error': 'origin and destination are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        routes = self.get_queryset().filter(
            origin_city__icontains=origin,
            destination_city__icontains=destination
        )
        
        if date:
            # Filter routes that have schedules on the specified date
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                routes = routes.filter(
                    schedules__departure_date=date_obj,
                    schedules__status='scheduled'
                ).distinct()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)


class ScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for schedule management"""
    
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ScheduleFilter
    ordering = ['departure_date', 'departure_time']
    
    def get_queryset(self):
        queryset = Schedule.objects.select_related('route', 'vehicle')
        
        if self.request.user.is_authenticated:
            profile_id = self.request.headers.get('X-Profile-ID')
            if profile_id and self.action in ['create', 'update', 'partial_update', 'destroy']:
                queryset = queryset.filter(profile_id=profile_id)
        
        return queryset
    
    def perform_create(self, serializer):
        profile_id = self.request.headers.get('X-Profile-ID')
        user_id = str(self.request.user.id)
        serializer.save(
            profile_id=profile_id,
            created_by_id=user_id
        )
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available schedules for booking"""
        queryset = self.get_queryset().filter(
            status='scheduled',
            available_seats__gt=0,
            departure_date__gte=timezone.now().date()
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TransportationBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for transportation bookings"""
    
    serializer_class = TransportationBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TransportationBookingFilter
    ordering = ['-booking_date']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        queryset = TransportationBooking.objects.select_related(
            'schedule__route', 'schedule__vehicle'
        )
        
        if profile_id:
            return queryset.filter(
                Q(passenger_user_id=user_id) | Q(profile_id=profile_id)
            )
        else:
            return queryset.filter(passenger_user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        serializer.save(
            passenger_user_id=user_id,
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


class TransportationReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for transportation reviews"""
    
    serializer_class = TransportationReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_id = str(self.request.user.id)
        profile_id = self.request.headers.get('X-Profile-ID')
        
        queryset = TransportationReview.objects.select_related('provider', 'booking')
        
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
