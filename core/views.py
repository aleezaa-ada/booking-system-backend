from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Resource, Booking
from .serializers import ResourceSerializer, BookingSerializer, UserProfileSerializer
from .utils import send_booking_notification_email


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit resources.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True  # Allow GET, HEAD, OPTIONS for anyone
        return request.user and request.user.is_staff  # Only staff (admin) can CUD


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [IsAdminOrReadOnly]  # Use custom permission


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the bookings
        for the currently authenticated user, or all bookings for admin.
        """
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=user)

    def get_object(self):
        """
        Override to check all bookings first, then raise 403 if user doesn't own it.
        This ensures we return 403 Forbidden instead of 404 Not Found.
        """
        queryset = Booking.objects.all()  # Check all bookings first
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = queryset.filter(**filter_kwargs).first()

        if obj is None:
            from rest_framework.exceptions import NotFound
            raise NotFound()

        # Check if user has permission to access this booking
        if not self.request.user.is_staff and obj.user != self.request.user:
            raise PermissionDenied("You can only access your own bookings.")

        return obj

    def check_object_permissions(self, request, obj):
        """
        Check if user has permission to modify/delete this booking.
        Regular users can only modify/delete their own bookings.
        Admins can modify/delete any booking.
        """
        super().check_object_permissions(request, obj)

        # For update and delete operations, ensure user owns the booking or is admin
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            if not request.user.is_staff and obj.user != request.user:
                raise PermissionDenied("You can only modify your own bookings.")

    def perform_create(self, serializer):
        # Automatically set the user to the currently authenticated user
        booking = serializer.save(user=self.request.user)
        send_booking_notification_email(booking, "Booking Confirmation", "booking_created_template")

    def perform_update(self, serializer):
        """
        Handle booking updates.
        - Users can update their own bookings including status
        """
        old_status = self.get_object().status
        booking = serializer.save()

        # Send different emails based on what changed
        if old_status != booking.status:
            # Status changed
            send_booking_notification_email(booking, f"Booking Status Updated to {booking.status.capitalize()}", "booking_status_updated_template")
        else:
            # User updated booking details (time, notes, etc.)
            send_booking_notification_email(booking, "Booking Updated", "booking_details_updated_template")

    def perform_destroy(self, instance):
        send_booking_notification_email(instance, "Booking Cancellation", "booking_cancelled_template")
        instance.delete()


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile_picture(request):
    """
    Update the user's profile picture with Cloudinary URL and public_id
    """
    from .models import UserProfile

    # Get or create profile if it doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    serializer = UserProfileSerializer(profile, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_profile_picture(request):
    """
    Remove the user's profile picture
    """
    from .models import UserProfile

    # Get or create profile if it doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    profile.profile_picture = None
    profile.cloudinary_public_id = None
    profile.save()

    return Response({'message': 'Profile picture removed successfully'}, status=status.HTTP_200_OK)
