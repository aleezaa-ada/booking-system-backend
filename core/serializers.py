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
        read_only_fields = ('status', 'created_at', 'updated_at') # Status will be managed by admin or specific logic

    def validate(self, data):
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
        if self.instance: # If updating an existing booking
            overlapping_bookings = Booking.objects.filter(
                resource=resource,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(pk=self.instance.pk)
        else: # If creating a new booking
            overlapping_bookings = Booking.objects.filter(
                resource=resource,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

        if overlapping_bookings.exists():
            raise serializers.ValidationError("This resource is already booked for the selected time slot.")

        return data