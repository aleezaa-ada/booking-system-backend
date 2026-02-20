from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()  # Gets the currently active user model (Django's default or a custom one)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.URLField(max_length=500, blank=True, null=True)  # Store Cloudinary URL
    cloudinary_public_id = models.CharField(max_length=255, blank=True, null=True)  # For deletion
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Resource(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    capacity = models.IntegerField(default=1)
    is_available = models.BooleanField(default=True)  # Can be used to temporarily disable a resource

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        # Add a unique constraint to prevent exact duplicate bookings (will refine with overlap check)
        unique_together = ('resource', 'start_time', 'end_time', 'user')

    def __str__(self):
        return f"Booking for {self.resource.name} by {self.user.username} from {self.start_time.strftime('%Y-%m-%d %H:%M')} to {self.end_time.strftime('%H:%M')}"
