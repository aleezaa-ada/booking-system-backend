from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ResourceViewSet, BookingViewSet, update_profile_picture, delete_profile_picture

router = DefaultRouter()
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('profile/picture/', update_profile_picture, name='update-profile-picture'),
    path('profile/picture/delete/', delete_profile_picture, name='delete-profile-picture'),
] + router.urls
