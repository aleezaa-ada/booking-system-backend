from rest_framework import serializers
from .models import Resource, Booking, UserProfile
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class ResourceSerializer(serializers.ModelSerializer):
    availability_status = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = '__all__'

    def get_availability_status(self, obj):
        """
        Determine real-time availability status based on bookings.
        Returns: 'available', 'unavailable', or 'pending'
        """
        # If resource is manually disabled, it's unavailable
        if not obj.is_available:
            return 'unavailable'

        # Check for current or future bookings
        now = timezone.now()

        # Check for confirmed bookings (now or in the future)
        has_confirmed = obj.bookings.filter(
            status='confirmed',
            end_time__gt=now
        ).exists()

        if has_confirmed:
            return 'unavailable'

        # Check for pending bookings
        has_pending = obj.bookings.filter(
            status='pending',
            end_time__gt=now
        ).exists()

        if has_pending:
            return 'pending'

        return 'available'


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    resource_name = serializers.CharField(source='resource.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Status field is now editable by all users

    def validate(self, data):
        # Only validate timing/resource if those fields are being updated
        # (For PATCH requests, only specific fields are sent)

        if 'start_time' in data and 'end_time' in data and 'resource' in data:
            # Only apply the 30-minute advance booking rule for NEW bookings
            # When updating existing bookings, skip this validation
            if not self.instance:
                # Booking Cut-off Time (cannot book within 30 minutes of now)
                min_booking_lead_time = timezone.now() + timedelta(minutes=30)
                if data['start_time'] < min_booking_lead_time:
                    raise serializers.ValidationError(f"Bookings must be made at least 30 minutes in advance. Earliest available: {min_booking_lead_time.strftime('%Y-%m-%d %H:%M')}")

            # Ensure end_time is after start_time
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time.")

            # Only check if booking is in the past for NEW bookings
            # When updating, allow past times (user is just updating details like status)
            if not self.instance and data['start_time'] < timezone.now():
                raise serializers.ValidationError("Cannot book in the past.")

            # Check for overlapping bookings for the same resource
            resource = data['resource']
            start_time = data['start_time']
            end_time = data['end_time']

            # Exclude the current booking if it's an update
            # Also exclude cancelled and rejected bookings as they don't block the slot
            if self.instance:
                overlapping_bookings = Booking.objects.filter(
                    resource=resource,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(pk=self.instance.pk).exclude(status__in=['cancelled', 'rejected'])
            else:
                overlapping_bookings = Booking.objects.filter(
                    resource=resource,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(status__in=['cancelled', 'rejected'])

            if overlapping_bookings.exists():
                # Get information about the conflicting booking(s)
                conflict_details = []
                for booking in overlapping_bookings[:3]:  # Show up to 3 conflicts
                    conflict_details.append(
                        f"{booking.start_time.strftime('%Y-%m-%d %H:%M')} - {booking.end_time.strftime('%H:%M')}"
                    )

                # Walk forward through all future bookings for this resource until
                # we find a gap that is large enough for the requested duration.
                duration = end_time - start_time

                all_future_bookings = Booking.objects.filter(
                    resource=resource,
                    end_time__gt=timezone.now()
                ).exclude(status__in=['cancelled', 'rejected']).order_by('end_time')

                if self.instance:
                    all_future_bookings = all_future_bookings.exclude(pk=self.instance.pk)

                suggestion = None
                candidate_start = overlapping_bookings.order_by('-end_time').first().end_time

                for _ in range(20):  # cap iterations to avoid infinite loop
                    candidate_end = candidate_start + duration
                    clash = all_future_bookings.filter(
                        start_time__lt=candidate_end,
                        end_time__gt=candidate_start
                    ).first()
                    if clash is None:
                        # No clash — this slot is free
                        suggestion = f"{candidate_start.strftime('%Y-%m-%d %H:%M')} - {candidate_end.strftime('%H:%M')}"
                        break
                    # Move past the clashing booking and try again
                    candidate_start = clash.end_time

                error_msg = "Cannot create booking - this resource is already booked during your selected time. "
                error_msg += f"Conflicting booking(s): {', '.join(conflict_details)}. "

                if suggestion:
                    error_msg += f"Suggested available time: {suggestion}."
                else:
                    error_msg += "Please check the resource availability and try a different time."

                raise serializers.ValidationError(error_msg)

        return data


# Custom User Serializer for Djoser to include is_staff field
class CustomUserSerializer(serializers.ModelSerializer):
    """
    Custom user serializer that includes is_staff field
    so frontend can check if user is admin
    """
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff', 'is_active', 'profile_picture')
        read_only_fields = ('id', 'is_staff', 'is_active')

    def get_profile_picture(self, obj):
        try:
            if hasattr(obj, 'profile') and obj.profile.profile_picture:
                return obj.profile.profile_picture
        except UserProfile.DoesNotExist:
            pass
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile picture
    """
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'cloudinary_public_id', 'updated_at')
        read_only_fields = ('updated_at',)


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """
    Custom user creation serializer that enforces email uniqueness
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate_email(self, value):
        """
        Check that the email is unique
        """
        if not value:
            raise serializers.ValidationError("Email is required.")

        # Normalize email to lowercase for consistency
        value = value.lower().strip()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use. Please use another email or login to your existing account.")

        return value

    def validate_username(self, value):
        """
        Check that the username is unique (Django does this by default, but we add a clearer error message)
        """
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")

        return value

    def create(self, validated_data):
        """
        Create a new user with encrypted password
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'].lower().strip(),
            password=validated_data['password']
        )
        return user
