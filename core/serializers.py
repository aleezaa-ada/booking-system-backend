from rest_framework import serializers
from .models import Resource, Booking
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    resource_name = serializers.CharField(source='resource.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at') # Status can be updated by admins via perform_update

    def validate(self, data):
        # Only validate timing/resource if those fields are being updated
        # (For PATCH requests, only specific fields are sent)
        
        if 'start_time' in data and 'end_time' in data and 'resource' in data:
            # Booking Cut-off Time (cannot book within 30 minutes of now)
            min_booking_lead_time = timezone.now() + timezone.timedelta(minutes=30)
            if data['start_time'] < min_booking_lead_time:
                raise serializers.ValidationError(f"Bookings must be made at least 30 minutes in advance. Earliest available: {min_booking_lead_time.strftime('%Y-%m-%d %H:%M')}")
            
            # Ensure end_time is after start_time
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time.")

            # Ensure booking is not in the past
            if data['start_time'] < timezone.now():
                raise serializers.ValidationError("Cannot book in the past.")

            # Check for overlapping bookings for the same resource
            resource = data['resource']
            start_time = data['start_time']
            end_time = data['end_time']

            # Exclude the current booking if it's an update
            if self.instance:
                overlapping_bookings = Booking.objects.filter(
                    resource=resource,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(pk=self.instance.pk)
            else:
                overlapping_bookings = Booking.objects.filter(
                    resource=resource,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )

            if overlapping_bookings.exists():
                # Get information about the conflicting booking(s)
                conflict_details = []
                for booking in overlapping_bookings[:3]:  # Show up to 3 conflicts
                    conflict_details.append(
                        f"{booking.start_time.strftime('%Y-%m-%d %H:%M')} - {booking.end_time.strftime('%H:%M')}"
                    )

                # Find next available time slot after the requested time
                all_bookings_today = Booking.objects.filter(
                    resource=resource,
                    start_time__date=start_time.date(),
                    start_time__gte=timezone.now()
                ).order_by('start_time')

                suggestions = []
                if all_bookings_today.exists():
                    # Suggest time after the last conflicting booking
                    last_conflict = overlapping_bookings.order_by('-end_time').first()
                    if last_conflict:
                        suggested_start = last_conflict.end_time
                        # Check if there's enough time before the next booking
                        next_booking = all_bookings_today.filter(start_time__gt=suggested_start).first()
                        duration = end_time - start_time
                        suggested_end = suggested_start + duration

                        if not next_booking or suggested_end <= next_booking.start_time:
                            suggestions.append(
                                f"{suggested_start.strftime('%Y-%m-%d %H:%M')} - {suggested_end.strftime('%H:%M')}"
                            )

                error_msg = f"Cannot create booking - this resource is already booked during your selected time. "
                error_msg += f"Conflicting booking(s): {', '.join(conflict_details)}. "

                if suggestions:
                    error_msg += f"Suggested available time: {suggestions[0]}."
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
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff', 'is_active')
        read_only_fields = ('id', 'is_staff', 'is_active')


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """
    Custom user creation serializer that enforces email uniqueness
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

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


