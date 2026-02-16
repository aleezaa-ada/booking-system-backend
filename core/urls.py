from rest_framework.routers import DefaultRouter
from .views import ResourceViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = router.urls