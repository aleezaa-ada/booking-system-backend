from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Resource, Booking
from .serializers import ResourceSerializer, BookingSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit resources.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True # Allow GET, HEAD, OPTIONS for anyone
        return request.user and request.user.is_staff # Only staff (admin) can CUD

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [IsAdminOrReadOnly] # Use custom permission

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users can interact

    def get_queryset(self):
        """
        This view should return a list of all the bookings
        for the currently authenticated user, or all bookings for admin.
        """
        user = self.request.user
        if user.is_staff: # Admin users can see all bookings
            return Booking.objects.all()
        return Booking.objects.filter(user=user) # Regular users only see their own

    def perform_create(self, serializer):
        # Automatically set the user to the currently authenticated user
        serializer.save(user=self.request.user)

    # For advanced: Add perform_update to handle status changes if needed
    def perform_update(self, serializer):
        # Example: Only admin can change status
        if 'status' in serializer.validated_data and not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only administrators can change booking status.")
        serializer.save()

