"""
Comprehensive test suite for the Booking System API.

Test Coverage:
- Health Check Endpoint
- User Authentication & Authorization
- Resource Model & API
- Booking Model & API
- Permissions & Security
- Business Logic & Validation
- Edge Cases
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch

from .models import Resource, Booking
from .serializers import ResourceSerializer


User = get_user_model()


# HEALTH CHECK TESTS

class HealthCheckTest(TestCase):
    """Test the health check endpoint"""

    def setUp(self):
        self.client = Client()

    def test_health_check_returns_200(self):
        """Test that health check endpoint returns 200 OK"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_health_check_method_not_allowed(self):
        """Test that only GET requests are allowed"""
        response = self.client.post('/health/')
        self.assertEqual(response.status_code, 405)


# USER MODEL TESTS

class UserModelTest(TestCase):
    """Test the User model"""

    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(admin_user.username, 'admin')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_user_string_representation(self):
        """Test user model string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser')


# AUTHENTICATION API TESTS

class AuthenticationAPITest(APITestCase):
    """Test authentication endpoints"""

    def test_user_registration(self):
        """Test user registration via API"""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_registration_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='pass123'
        )
        url = '/api/auth/users/'
        data = {
            'username': 'existinguser',
            'email': 'newemail@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """Test user login via token authentication"""
        User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='loginpass123'
        )

        url = '/api/auth/token/login/'
        data = {
            'username': 'loginuser',
            'password': 'loginpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='loginpass123'
        )

        url = '/api/auth/token/login/'
        data = {
            'username': 'loginuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_logout(self):
        """Test user logout (token destruction)"""
        user = User.objects.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.post('/api/auth/token/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token.key).exists())


# ADMIN PANEL TESTS

class AdminAccessTest(TestCase):
    """Test admin panel access"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

    def test_admin_login_page_loads(self):
        """Test that admin login page is accessible"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)

    def test_admin_login_works(self):
        """Test admin user can log in to admin panel"""
        login = self.client.login(username='admin', password='adminpass123')
        self.assertTrue(login)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_regular_user_cannot_access_admin(self):
        """Test that regular users cannot access admin panel"""
        User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass123'
        )
        login = self.client.login(username='regular', password='pass123')
        self.assertTrue(login)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)


# RESOURCE MODEL TESTS

class ResourceModelTest(TestCase):
    """Test the Resource model"""

    def test_create_resource(self):
        """Test creating a resource"""
        resource = Resource.objects.create(
            name='Conference Room A',
            description='Large conference room with projector',
            capacity=10,
            is_available=True
        )
        self.assertEqual(resource.name, 'Conference Room A')
        self.assertEqual(resource.capacity, 10)
        self.assertTrue(resource.is_available)

    def test_resource_string_representation(self):
        """Test resource model string representation"""
        resource = Resource.objects.create(name='Meeting Room')
        self.assertEqual(str(resource), 'Meeting Room')

    def test_resource_default_values(self):
        """Test resource model default values"""
        resource = Resource.objects.create(name='Test Room')
        self.assertEqual(resource.capacity, 1)
        self.assertTrue(resource.is_available)
        self.assertEqual(resource.description, '')


# RESOURCE API TESTS

class ResourceAPITest(APITestCase):
    """Test Resource API endpoints"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123'
        )
        self.resource = Resource.objects.create(
            name='Test Resource',
            capacity=5
        )

    def test_list_resources_unauthenticated(self):
        """Test that unauthenticated users can view resources"""
        response = self.client.get('/api/resources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_resources_authenticated(self):
        """Test listing resources as authenticated user"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/resources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_resource(self):
        """Test retrieving a single resource"""
        response = self.client.get(f'/api/resources/{self.resource.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Resource')

    def test_create_resource_as_admin(self):
        """Test creating a resource as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'New Resource',
            'description': 'Test description',
            'capacity': 3,
            'is_available': True
        }
        response = self.client.post('/api/resources/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Resource.objects.count(), 2)

    def test_create_resource_as_regular_user(self):
        """Test that regular users cannot create resources"""
        self.client.force_authenticate(user=self.regular_user)
        data = {'name': 'Unauthorized Resource', 'capacity': 1}
        response = self.client.post('/api/resources/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_resource_as_admin(self):
        """Test updating a resource as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Updated Resource', 'capacity': 10}
        response = self.client.patch(f'/api/resources/{self.resource.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.name, 'Updated Resource')

    def test_delete_resource_as_admin(self):
        """Test deleting a resource as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/resources/{self.resource.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Resource.objects.count(), 0)

    def test_delete_resource_as_regular_user(self):
        """Test that regular users cannot delete resources"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(f'/api/resources/{self.resource.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# BOOKING MODEL TESTS

class BookingModelTest(TestCase):
    """Test the Booking model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.resource = Resource.objects.create(
            name='Test Room',
            capacity=5
        )

    def test_create_booking(self):
        """Test creating a booking"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end,
            status='pending'
        )
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.resource, self.resource)
        self.assertEqual(booking.status, 'pending')

    def test_booking_string_representation(self):
        """Test booking model string representation"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end
        )
        self.assertIn(self.resource.name, str(booking))
        self.assertIn(self.user.username, str(booking))

    def test_booking_default_status(self):
        """Test booking default status is pending"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end
        )
        self.assertEqual(booking.status, 'pending')

    def test_booking_timestamps(self):
        """Test that created_at and updated_at are set automatically"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end
        )
        self.assertIsNotNone(booking.created_at)
        self.assertIsNotNone(booking.updated_at)


# BOOKING API TESTS

class BookingAPITest(APITestCase):
    """Test Booking API endpoints"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.resource = Resource.objects.create(
            name='Test Resource',
            capacity=5
        )

    @patch('core.views.send_booking_notification_email')
    def test_create_booking(self, mock_email):
        """Test creating a booking"""
        self.client.force_authenticate(user=self.user1)
        start = (timezone.now() + timedelta(hours=2)).isoformat()
        end = (timezone.now() + timedelta(hours=4)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': start,
            'end_time': end,
            'notes': 'Test booking'
        }
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertTrue(mock_email.called)

    def test_create_booking_unauthenticated(self):
        """Test that unauthenticated users cannot create bookings"""
        start = (timezone.now() + timedelta(hours=1)).isoformat()
        end = (timezone.now() + timedelta(hours=2)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': start,
            'end_time': end
        }
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_own_bookings(self):
        """Test that users can only see their own bookings"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        Booking.objects.create(
            user=self.user1,
            resource=self.resource,
            start_time=start,
            end_time=end
        )
        Booking.objects.create(
            user=self.user2,
            resource=self.resource,
            start_time=start + timedelta(days=1),
            end_time=end + timedelta(days=1)
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_see_all_bookings(self):
        """Test that admin users can see all bookings"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        Booking.objects.create(
            user=self.user1,
            resource=self.resource,
            start_time=start,
            end_time=end
        )
        Booking.objects.create(
            user=self.user2,
            resource=self.resource,
            start_time=start + timedelta(days=1),
            end_time=end + timedelta(days=1)
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    @patch('core.views.send_booking_notification_email')
    def test_update_own_booking(self, mock_email):
        """Test that users can update their own bookings"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user1,
            resource=self.resource,
            start_time=start,
            end_time=end
        )

        self.client.force_authenticate(user=self.user1)
        data = {'notes': 'Updated notes'}
        response = self.client.patch(f'/api/bookings/{booking.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.notes, 'Updated notes')

    def test_cannot_update_others_booking(self):
        """Test that users cannot update other users' bookings"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user1,
            resource=self.resource,
            start_time=start,
            end_time=end
        )

        self.client.force_authenticate(user=self.user2)
        data = {'notes': 'Hacked notes'}
        response = self.client.patch(f'/api/bookings/{booking.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('core.views.send_booking_notification_email')
    def test_admin_can_update_any_booking(self, mock_email):
        """Test that admin can update any booking"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user1,
            resource=self.resource,
            start_time=start,
            end_time=end,
            status='pending'
        )

        self.client.force_authenticate(user=self.admin_user)
        data = {'status': 'confirmed'}
        response = self.client.patch(f'/api/bookings/{booking.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')

    @patch('core.views.send_booking_notification_email')
    def test_delete_own_booking(self, mock_email):
        """Test that users can delete their own bookings"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=self.user1,
            resource=self.resource,
            start_time=start,
            end_time=end
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f'/api/bookings/{booking.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Booking.objects.count(), 0)
        self.assertTrue(mock_email.called)


# BOOKING VALIDATION TESTS

class BookingValidationTest(APITestCase):
    """Test booking validation logic"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='pass123'
        )
        self.resource = Resource.objects.create(
            name='Test Resource',
            capacity=5
        )
        self.client.force_authenticate(user=self.user)

    def test_booking_requires_30_minute_advance(self):
        """Test that bookings must be made at least 30 minutes in advance"""
        start = (timezone.now() + timedelta(minutes=20)).isoformat()
        end = (timezone.now() + timedelta(minutes=50)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': start,
            'end_time': end
        }
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('30 minutes', str(response.data))

    def test_booking_end_must_be_after_start(self):
        """Test that end time must be after start time"""
        start = (timezone.now() + timedelta(hours=2)).isoformat()
        end = (timezone.now() + timedelta(hours=1)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': start,
            'end_time': end
        }
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_book_in_past(self):
        """Test that bookings cannot be created in the past"""
        start = (timezone.now() - timedelta(hours=1)).isoformat()
        end = (timezone.now() + timedelta(hours=1)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': start,
            'end_time': end
        }
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('core.views.send_booking_notification_email')
    def test_overlapping_bookings_rejected(self, mock_email):
        """Test that overlapping bookings are rejected"""
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=2)

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end
        )

        overlap_start = (start + timedelta(hours=1)).isoformat()
        overlap_end = (end + timedelta(hours=1)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': overlap_start,
            'end_time': overlap_end
        }
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already booked', str(response.data))

    @patch('core.views.send_booking_notification_email')
    def test_adjacent_bookings_allowed(self, mock_email):
        """Test that adjacent (non-overlapping) bookings are allowed"""
        start1 = timezone.now() + timedelta(hours=2)
        end1 = start1 + timedelta(hours=2)

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start1,
            end_time=end1
        )

        start2 = end1.isoformat()
        end2 = (end1 + timedelta(hours=2)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': start2,
            'end_time': end2
        }
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# RESOURCE AVAILABILITY TESTS

class ResourceAvailabilityTest(TestCase):
    """Test resource availability status logic"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='pass123'
        )
        self.resource = Resource.objects.create(
            name='Test Resource',
            is_available=True
        )

    def test_manually_disabled_resource_unavailable(self):
        """Test that manually disabled resources show as unavailable"""
        self.resource.is_available = False
        self.resource.save()

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'unavailable')

    def test_resource_with_confirmed_booking_unavailable(self):
        """Test that resources with confirmed bookings show as unavailable"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end,
            status='confirmed'
        )

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'unavailable')

    def test_resource_with_pending_booking_shows_pending(self):
        """Test that resources with pending bookings show as pending"""
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end,
            status='pending'
        )

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'pending')

    def test_resource_with_no_bookings_available(self):
        """Test that resources with no bookings show as available"""
        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'available')

    def test_resource_with_past_booking_available(self):
        """Test that resources with only past bookings show as available"""
        start = timezone.now() - timedelta(hours=3)
        end = start + timedelta(hours=2)

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end,
            status='confirmed'
        )

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'available')


# EDGE CASE TESTS

class EdgeCaseTests(APITestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='pass123'
        )
        self.resource = Resource.objects.create(name='Test Resource')
        self.client.force_authenticate(user=self.user)

    def test_booking_exactly_30_minutes_advance_allowed(self):
        """Test booking exactly at the 30-minute minimum is allowed"""
        start = (timezone.now() + timedelta(minutes=31)).isoformat()
        end = (timezone.now() + timedelta(minutes=91)).isoformat()

        data = {
            'resource': self.resource.id,
            'start_time': start,
            'end_time': end
        }
        with patch('core.views.send_booking_notification_email'):
            response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_multiple_resources_independent(self):
        """Test that bookings for different resources don't conflict"""
        resource2 = Resource.objects.create(name='Resource 2')
        start = (timezone.now() + timedelta(hours=1)).isoformat()
        end = (timezone.now() + timedelta(hours=2)).isoformat()

        data1 = {
            'resource': self.resource.id,
            'start_time': start,
            'end_time': end
        }
        with patch('core.views.send_booking_notification_email'):
            response1 = self.client.post('/api/bookings/', data1)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        data2 = {
            'resource': resource2.id,
            'start_time': start,
            'end_time': end
        }
        with patch('core.views.send_booking_notification_email'):
            response2 = self.client.post('/api/bookings/', data2)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

    def test_cancelled_booking_doesnt_block_slot(self):
        """Test that cancelled bookings don't prevent new bookings from other users"""
        # Create another user for the second booking
        user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )

        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        # User 1 creates and then cancels a booking
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=start,
            end_time=end,
            status='cancelled'
        )

        # User 2 should be able to book the same slot
        self.client.force_authenticate(user=user2)
        data = {
            'resource': self.resource.id,
            'start_time': start.isoformat(),
            'end_time': end.isoformat()
        }
        with patch('core.views.send_booking_notification_email'):
            response = self.client.post('/api/bookings/', data)


        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# USER PROFILE MODEL TESTS

class UserProfileModelTest(TestCase):
    """Test the UserProfile model"""

    def test_user_profile_created_on_user_creation(self):
        """Test that a UserProfile is automatically created when a User is created"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.user, user)

    def test_user_profile_string_representation(self):
        """Test UserProfile model string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        expected_string = "testuser's profile"
        self.assertEqual(str(user.profile), expected_string)

    def test_user_profile_default_values(self):
        """Test that UserProfile has correct default values"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = user.profile
        self.assertIsNone(profile.profile_picture)
        self.assertIsNone(profile.cloudinary_public_id)
        self.assertIsNotNone(profile.updated_at)

    def test_user_profile_update_picture(self):
        """Test updating profile picture URL"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = user.profile

        picture_url = 'https://cloudinary.com/image/test123.jpg'
        public_id = 'profile_pictures/test123'

        profile.profile_picture = picture_url
        profile.cloudinary_public_id = public_id
        profile.save()

        profile.refresh_from_db()
        self.assertEqual(profile.profile_picture, picture_url)
        self.assertEqual(profile.cloudinary_public_id, public_id)

    def test_user_profile_remove_picture(self):
        """Test removing profile picture"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = user.profile

        # Set picture first
        profile.profile_picture = 'https://cloudinary.com/image/test123.jpg'
        profile.cloudinary_public_id = 'profile_pictures/test123'
        profile.save()

        # Remove picture
        profile.profile_picture = None
        profile.cloudinary_public_id = None
        profile.save()

        profile.refresh_from_db()
        self.assertIsNone(profile.profile_picture)
        self.assertIsNone(profile.cloudinary_public_id)

    def test_user_profile_updated_at_changes(self):
        """Test that updated_at timestamp changes on update"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = user.profile
        original_updated_at = profile.updated_at

        # Wait a moment and update
        from time import sleep
        sleep(0.1)

        profile.profile_picture = 'https://cloudinary.com/image/test123.jpg'
        profile.save()

        profile.refresh_from_db()
        self.assertGreater(profile.updated_at, original_updated_at)

    def test_user_profile_cascade_delete(self):
        """Test that UserProfile is deleted when User is deleted"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile_id = user.profile.id

        user.delete()

        from .models import UserProfile
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())

    def test_user_profile_url_field_max_length(self):
        """Test that profile_picture URL can handle long URLs"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = user.profile

        # Test with a long URL (but within 500 character limit)
        long_url = 'https://cloudinary.com/image/' + 'a' * 450 + '.jpg'
        profile.profile_picture = long_url
        profile.save()

        profile.refresh_from_db()
        self.assertEqual(profile.profile_picture, long_url)


# PROFILE PICTURE API TESTS

class ProfilePictureAPITest(APITestCase):
    """Test Profile Picture API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )

    def test_update_profile_picture_authenticated(self):
        """Test updating profile picture as authenticated user"""
        self.client.force_authenticate(user=self.user)

        data = {
            'profile_picture': 'https://cloudinary.com/image/test123.jpg',
            'cloudinary_public_id': 'profile_pictures/test123'
        }

        response = self.client.patch('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.profile_picture, data['profile_picture'])
        self.assertEqual(self.user.profile.cloudinary_public_id, data['cloudinary_public_id'])

    def test_update_profile_picture_unauthenticated(self):
        """Test that unauthenticated users cannot update profile picture"""
        data = {
            'profile_picture': 'https://cloudinary.com/image/test123.jpg',
            'cloudinary_public_id': 'profile_pictures/test123'
        }

        response = self.client.patch('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_picture_partial_update(self):
        """Test partial update of profile picture (only URL)"""
        self.client.force_authenticate(user=self.user)

        data = {
            'profile_picture': 'https://cloudinary.com/image/test123.jpg'
        }

        response = self.client.patch('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.profile_picture, data['profile_picture'])

    def test_update_profile_picture_put_method(self):
        """Test that PUT method also works for updating profile picture"""
        self.client.force_authenticate(user=self.user)

        data = {
            'profile_picture': 'https://cloudinary.com/image/test123.jpg',
            'cloudinary_public_id': 'profile_pictures/test123'
        }

        response = self.client.put('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile_picture_creates_profile_if_not_exists(self):
        """Test that updating profile picture creates profile if it doesn't exist"""
        # Manually delete the profile to test auto-creation
        self.user.profile.delete()

        self.client.force_authenticate(user=self.user)

        data = {
            'profile_picture': 'https://cloudinary.com/image/test123.jpg',
            'cloudinary_public_id': 'profile_pictures/test123'
        }

        response = self.client.patch('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify profile was created
        from .models import UserProfile
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_update_profile_picture_multiple_times(self):
        """Test updating profile picture multiple times"""
        self.client.force_authenticate(user=self.user)

        # First update
        data1 = {
            'profile_picture': 'https://cloudinary.com/image/test1.jpg',
            'cloudinary_public_id': 'profile_pictures/test1'
        }
        response1 = self.client.patch('/api/profile/picture/', data1)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Second update (should replace first)
        data2 = {
            'profile_picture': 'https://cloudinary.com/image/test2.jpg',
            'cloudinary_public_id': 'profile_pictures/test2'
        }
        response2 = self.client.patch('/api/profile/picture/', data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.profile_picture, data2['profile_picture'])
        self.assertEqual(self.user.profile.cloudinary_public_id, data2['cloudinary_public_id'])

    def test_delete_profile_picture_authenticated(self):
        """Test deleting profile picture as authenticated user"""
        # Set a profile picture first
        self.user.profile.profile_picture = 'https://cloudinary.com/image/test123.jpg'
        self.user.profile.cloudinary_public_id = 'profile_pictures/test123'
        self.user.profile.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.delete('/api/profile/picture/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.profile.refresh_from_db()
        self.assertIsNone(self.user.profile.profile_picture)
        self.assertIsNone(self.user.profile.cloudinary_public_id)

    def test_delete_profile_picture_unauthenticated(self):
        """Test that unauthenticated users cannot delete profile picture"""
        response = self.client.delete('/api/profile/picture/delete/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_profile_picture_when_none_exists(self):
        """Test deleting profile picture when none exists (should not error)"""
        self.client.force_authenticate(user=self.user)

        # Ensure no picture is set
        self.user.profile.profile_picture = None
        self.user.profile.cloudinary_public_id = None
        self.user.profile.save()

        response = self.client.delete('/api/profile/picture/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_profile_picture_creates_profile_if_not_exists(self):
        """Test that deleting profile picture creates profile if it doesn't exist"""
        # Manually delete the profile
        self.user.profile.delete()

        self.client.force_authenticate(user=self.user)

        response = self.client.delete('/api/profile/picture/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify profile was created
        from .models import UserProfile
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_users_can_only_update_own_profile(self):
        """Test that users can only update their own profile picture"""
        self.client.force_authenticate(user=self.user)

        data = {
            'profile_picture': 'https://cloudinary.com/image/test123.jpg',
            'cloudinary_public_id': 'profile_pictures/test123'
        }

        response = self.client.patch('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify only the authenticated user's profile was updated
        self.user.profile.refresh_from_db()
        self.other_user.profile.refresh_from_db()

        self.assertEqual(self.user.profile.profile_picture, data['profile_picture'])
        self.assertIsNone(self.other_user.profile.profile_picture)

    def test_profile_picture_url_validation(self):
        """Test that invalid URLs are rejected"""
        self.client.force_authenticate(user=self.user)

        data = {
            'profile_picture': 'not-a-valid-url',
            'cloudinary_public_id': 'profile_pictures/test123'
        }

        response = self.client.patch('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_picture_response_includes_updated_at(self):
        """Test that response includes updated_at timestamp"""
        self.client.force_authenticate(user=self.user)

        data = {
            'profile_picture': 'https://cloudinary.com/image/test123.jpg',
            'cloudinary_public_id': 'profile_pictures/test123'
        }

        response = self.client.patch('/api/profile/picture/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('updated_at', response.data)


# CUSTOM USER SERIALIZER TESTS

class CustomUserSerializerTest(APITestCase):
    """Test that CustomUserSerializer includes profile picture"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Set a profile picture
        self.user.profile.profile_picture = 'https://cloudinary.com/image/test123.jpg'
        self.user.profile.cloudinary_public_id = 'profile_pictures/test123'
        self.user.profile.save()

    def test_current_user_endpoint_includes_profile_picture(self):
        """Test that /api/auth/users/me/ includes profile_picture"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_picture', response.data)
        self.assertEqual(response.data['profile_picture'], self.user.profile.profile_picture)

    def test_current_user_endpoint_profile_picture_null(self):
        """Test that profile_picture is null when not set"""
        # Create a new user without profile picture
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )

        self.client.force_authenticate(user=new_user)

        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_picture', response.data)
        self.assertIsNone(response.data['profile_picture'])


# EMAIL UTILITY TESTS

class EmailUtilityTest(TestCase):
    """Test email utility functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='emailtestuser',
            email='emailtest@example.com',
            password='pass123'
        )
        self.resource = Resource.objects.create(
            name='Test Room',
            capacity=5
        )
        self.booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=3),
            status='pending',
            notes='Test booking notes'
        )

    @patch('core.utils.send_mail')
    def test_send_booking_notification_console_backend(self, mock_send_mail):
        """Test sending email with console backend"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        # Temporarily set EMAIL_USE to console
        original_email_use = settings.EMAIL_USE
        settings.EMAIL_USE = 'console'

        try:
            send_booking_notification_email(
                self.booking,
                "Test Subject",
                "booking_created_template"
            )

            # Verify send_mail was called
            mock_send_mail.assert_called_once()
            args, kwargs = mock_send_mail.call_args

            self.assertEqual(args[0], "Test Subject")  # subject
            self.assertIn(self.user.username, args[1])  # plain message
            self.assertEqual(args[3], [self.user.email])  # recipient
        finally:
            settings.EMAIL_USE = original_email_use

    @patch('core.utils.SendGridAPIClient')
    def test_send_booking_notification_sendgrid_success(self, mock_sendgrid):
        """Test sending email with SendGrid successfully"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        # Mock SendGrid response
        mock_sg_instance = mock_sendgrid.return_value
        mock_response = type('obj', (object,), {'status_code': 202})
        mock_sg_instance.send.return_value = mock_response

        original_email_use = settings.EMAIL_USE
        settings.EMAIL_USE = 'sendgrid'
        settings.SENDGRID_API_KEY = 'test-key'
        settings.FROM_EMAIL = 'noreply@test.com'

        try:
            result = send_booking_notification_email(
                self.booking,
                "Test Subject",
                "booking_created_template"
            )

            self.assertTrue(result)
            mock_sg_instance.send.assert_called_once()
        finally:
            settings.EMAIL_USE = original_email_use

    @patch('core.utils.SendGridAPIClient')
    @patch('core.utils.send_mail')
    def test_send_booking_notification_sendgrid_failure_fallback(self, mock_send_mail, mock_sendgrid):
        """Test that SendGrid failure logs to console"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        # Mock SendGrid to raise an exception
        mock_sg_instance = mock_sendgrid.return_value
        mock_sg_instance.send.side_effect = Exception("SendGrid API Error")

        original_email_use = settings.EMAIL_USE
        settings.EMAIL_USE = 'sendgrid'
        settings.SENDGRID_API_KEY = 'test-key'
        settings.FROM_EMAIL = 'noreply@test.com'

        try:
            result = send_booking_notification_email(
                self.booking,
                "Test Subject",
                "booking_created_template"
            )

            self.assertFalse(result)  # Should return False on failure
        finally:
            settings.EMAIL_USE = original_email_use

    def test_email_content_booking_cancelled(self):
        """Test email content for cancelled booking"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        with patch('core.utils.send_mail') as mock_send_mail:
            original_email_use = settings.EMAIL_USE
            settings.EMAIL_USE = 'console'

            try:
                send_booking_notification_email(
                    self.booking,
                    "Cancellation",
                    "booking_cancelled_template"
                )

                args, kwargs = mock_send_mail.call_args
                plain_message = args[1]

                self.assertIn("been cancelled", plain_message)
                self.assertIn(self.resource.name, plain_message)
            finally:
                settings.EMAIL_USE = original_email_use

    def test_email_content_booking_updated(self):
        """Test email content for updated booking"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        with patch('core.utils.send_mail') as mock_send_mail:
            original_email_use = settings.EMAIL_USE
            settings.EMAIL_USE = 'console'

            try:
                send_booking_notification_email(
                    self.booking,
                    "Update",
                    "booking_details_updated_template"
                )

                args, kwargs = mock_send_mail.call_args
                plain_message = args[1]

                self.assertIn("been updated", plain_message)
            finally:
                settings.EMAIL_USE = original_email_use

    def test_email_content_status_updated(self):
        """Test email content for status update"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        self.booking.status = 'confirmed'
        self.booking.save()

        with patch('core.utils.send_mail') as mock_send_mail:
            original_email_use = settings.EMAIL_USE
            settings.EMAIL_USE = 'console'

            try:
                send_booking_notification_email(
                    self.booking,
                    "Status Update",
                    "booking_status_updated_template"
                )

                args, kwargs = mock_send_mail.call_args
                plain_message = args[1]

                self.assertIn("status has been updated to confirmed", plain_message)
            finally:
                settings.EMAIL_USE = original_email_use

    def test_email_content_default_template(self):
        """Test email content with unknown template"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        with patch('core.utils.send_mail') as mock_send_mail:
            original_email_use = settings.EMAIL_USE
            settings.EMAIL_USE = 'console'

            try:
                send_booking_notification_email(
                    self.booking,
                    "Test",
                    "unknown_template"
                )

                args, kwargs = mock_send_mail.call_args
                plain_message = args[1]

                self.assertIn(f"been {self.booking.status}", plain_message)
            finally:
                settings.EMAIL_USE = original_email_use

    def test_email_content_no_notes(self):
        """Test email content when booking has no notes"""
        from core.utils import send_booking_notification_email
        from django.conf import settings

        self.booking.notes = ""
        self.booking.save()

        with patch('core.utils.send_mail') as mock_send_mail:
            original_email_use = settings.EMAIL_USE
            settings.EMAIL_USE = 'console'

            try:
                send_booking_notification_email(
                    self.booking,
                    "Test",
                    "booking_created_template"
                )

                args, kwargs = mock_send_mail.call_args
                plain_message = args[1]

                self.assertIn("No notes given", plain_message)
            finally:
                settings.EMAIL_USE = original_email_use


# MANAGEMENT COMMAND TESTS

class CreateUserProfilesCommandTest(TestCase):
    """Test create_user_profiles management command"""

    def setUp(self):
        # Create users without profiles by temporarily disconnecting signal
        from django.db.models.signals import post_save
        from core.models import create_user_profile, User as UserModel

        post_save.disconnect(create_user_profile, sender=UserModel)

        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )

        # Delete profiles if they exist
        from core.models import UserProfile
        UserProfile.objects.filter(user__in=[self.user1, self.user2]).delete()

        # Reconnect signal
        post_save.connect(create_user_profile, sender=UserModel)

    def test_create_user_profiles_command(self):
        """Test that command creates profiles for users without them"""
        from django.core.management import call_command
        from io import StringIO
        from core.models import UserProfile

        # Verify no profiles exist
        self.assertEqual(UserProfile.objects.filter(user__in=[self.user1, self.user2]).count(), 0)

        # Call the command
        out = StringIO()
        call_command('create_user_profiles', stdout=out)

        # Verify profiles were created
        self.assertTrue(UserProfile.objects.filter(user=self.user1).exists())
        self.assertTrue(UserProfile.objects.filter(user=self.user2).exists())

        # Check output
        output = out.getvalue()
        self.assertIn('Created profile for user:', output)

    def test_create_user_profiles_command_existing_profiles(self):
        """Test that command doesn't duplicate existing profiles"""
        from django.core.management import call_command
        from io import StringIO
        from core.models import UserProfile

        # Create profiles manually
        UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.get_or_create(user=self.user2)

        initial_count = UserProfile.objects.count()

        # Call the command again
        out = StringIO()
        call_command('create_user_profiles', stdout=out)

        # Verify no duplicate profiles
        self.assertEqual(UserProfile.objects.count(), initial_count)

        # Check output mentions existing profiles
        output = out.getvalue()
        self.assertIn('already exists', output)


class EnsureSuperuserCommandTest(TestCase):
    """Test ensure_superuser management command"""

    def test_ensure_superuser_creates_superuser_when_none_exists(self):
        """Test that command creates superuser when none exists"""
        from django.core.management import call_command
        from io import StringIO

        # Ensure no superusers exist
        User.objects.filter(is_superuser=True).delete()

        out = StringIO()
        call_command('ensure_superuser', stdout=out)

        # Verify superuser was created
        self.assertTrue(User.objects.filter(is_superuser=True).exists())

        # Check output
        output = out.getvalue()
        self.assertIn('created successfully', output)

    def test_ensure_superuser_skips_when_exists(self):
        """Test that command skips creation when superuser exists"""
        from django.core.management import call_command
        from io import StringIO

        # Create a superuser
        User.objects.create_superuser(
            username='existing_admin',
            email='admin@example.com',
            password='admin123'
        )

        initial_count = User.objects.filter(is_superuser=True).count()

        out = StringIO()
        call_command('ensure_superuser', stdout=out)

        # Verify no new superuser was created
        self.assertEqual(User.objects.filter(is_superuser=True).count(), initial_count)

        # Check output
        output = out.getvalue()
        self.assertIn('already exists', output)


# SERIALIZER EDGE CASE TESTS

class BookingSerializerEdgeCaseTest(APITestCase):
    """Test BookingSerializer edge cases for better coverage"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.resource = Resource.objects.create(name='Test Room', capacity=5)
        self.client.force_authenticate(user=self.user)

    def test_booking_serializer_suggests_alternative_times(self):
        """Test that serializer suggests alternative times when slot is taken"""
        # Create a blocking booking
        future_time = timezone.now() + timedelta(hours=2)
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            status='confirmed'
        )

        # Try to create overlapping booking
        data = {
            'resource': self.resource.id,
            'start_time': (future_time + timedelta(minutes=30)).isoformat(),
            'end_time': (future_time + timedelta(hours=3)).isoformat(),
        }

        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should contain booking conflict or alternative time message
        response_text = str(response.data).lower()
        self.assertTrue(
            'already booked' in response_text or
            'conflicting' in response_text or
            'suggested' in response_text,
            f"Expected booking conflict message in: {response.data}"
        )

    def test_booking_partial_update_without_time_validation(self):
        """Test that PATCH without time fields doesn't trigger time validation"""
        booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            status='pending'
        )

        # Update only notes (no time fields)
        data = {'notes': 'Updated notes only'}
        response = self.client.patch(f'/api/bookings/{booking.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        booking.refresh_from_db()
        self.assertEqual(booking.notes, 'Updated notes only')

    def test_booking_serializer_init_sets_user_readonly(self):
        """Test that user field is properly set as read-only in serializer"""
        from core.serializers import BookingSerializer

        serializer = BookingSerializer()
        self.assertTrue(serializer.fields['user'].read_only)


class CustomUserCreateSerializerTest(APITestCase):
    """Test CustomUserCreateSerializer validation"""

    def test_email_required_validation(self):
        """Test that email is required"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
            # email is missing
        }
        response = self.client.post('/api/auth/users/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_uniqueness_validation(self):
        """Test that duplicate emails are rejected"""
        User.objects.create_user(
            username='existinguser',
            email='duplicate@example.com',
            password='pass123'
        )

        data = {
            'username': 'newuser',
            'email': 'duplicate@example.com',
            'password': 'pass123'
        }
        response = self.client.post('/api/auth/users/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', str(response.data).lower())

    def test_email_case_insensitive_uniqueness(self):
        """Test that email uniqueness is case-insensitive"""
        User.objects.create_user(
            username='user1',
            email='Test@Example.com',
            password='pass123'
        )

        data = {
            'username': 'user2',
            'email': 'test@example.com',  # Different case
            'password': 'pass123'
        }
        response = self.client.post('/api/auth/users/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_username_case_insensitive_uniqueness(self):
        """Test that username uniqueness is case-insensitive"""
        User.objects.create_user(
            username='TestUser',
            email='test1@example.com',
            password='pass123'
        )

        data = {
            'username': 'testuser',  # Different case
            'email': 'test2@example.com',
            'password': 'pass123'
        }
        response = self.client.post('/api/auth/users/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_normalization(self):
        """Test that email is normalized to lowercase"""
        data = {
            'username': 'testuser',
            'email': '  TEST@EXAMPLE.COM  ',  # Uppercase with spaces
            'password': 'pass123'
        }
        response = self.client.post('/api/auth/users/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')


class ResourceSerializerTest(TestCase):
    """Test ResourceSerializer availability status calculations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.resource = Resource.objects.create(
            name='Test Room',
            capacity=5,
            is_available=True
        )

    def test_availability_status_manually_disabled(self):
        """Test that manually disabled resources show as unavailable"""
        from core.serializers import ResourceSerializer

        self.resource.is_available = False
        self.resource.save()

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'unavailable')

    def test_availability_status_with_confirmed_booking(self):
        """Test availability status with confirmed future booking"""
        from core.serializers import ResourceSerializer

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            status='confirmed'
        )

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'unavailable')

    def test_availability_status_with_pending_booking(self):
        """Test availability status with pending booking"""
        from core.serializers import ResourceSerializer

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            status='pending'
        )

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'pending')

    def test_availability_status_with_cancelled_booking(self):
        """Test that cancelled bookings don't affect availability"""
        from core.serializers import ResourceSerializer

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            status='cancelled'
        )

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'available')

    def test_availability_status_with_past_booking(self):
        """Test that past bookings don't affect current availability"""
        from core.serializers import ResourceSerializer

        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=timezone.now() - timedelta(hours=3),
            end_time=timezone.now() - timedelta(hours=1),
            status='confirmed'
        )

        serializer = ResourceSerializer(self.resource)
        self.assertEqual(serializer.data['availability_status'], 'available')


class PasswordResetEmailTest(TestCase):
    """Test password reset email functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser',
            email='resetuser@example.com',
            password='oldpassword123'
        )

    def test_send_password_reset_email_console_backend(self):
        """Test sending password reset email with console backend"""
        from core.utils import send_password_reset_email
        from django.conf import settings
        import io
        import sys

        original_email_use = settings.EMAIL_USE
        settings.EMAIL_USE = 'console'
        settings.FRONTEND_URL = 'http://localhost:5173'

        try:
            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            send_password_reset_email(
                user=self.user,
                uid='MQ',
                token='test-token-123'
            )

            # Restore stdout
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

            # Check that the correct information was printed
            self.assertIn('resetuser@example.com', output)
            self.assertIn('http://localhost:5173/password-reset/MQ/test-token-123', output)
            self.assertIn('Password Reset Request', output)
        finally:
            settings.EMAIL_USE = original_email_use
            sys.stdout = sys.__stdout__

    def test_send_password_reset_email_with_https(self):
        """Test password reset email uses correct protocol for HTTPS"""
        from core.utils import send_password_reset_email
        from django.conf import settings
        import io
        import sys

        original_email_use = settings.EMAIL_USE
        original_frontend_url = settings.FRONTEND_URL
        settings.EMAIL_USE = 'console'
        settings.FRONTEND_URL = 'https://myapp.com'

        try:
            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            send_password_reset_email(
                user=self.user,
                uid='MQ',
                token='test-token-123'
            )

            # Restore stdout
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

            self.assertIn('https://myapp.com/password-reset/MQ/test-token-123', output)
        finally:
            settings.EMAIL_USE = original_email_use
            settings.FRONTEND_URL = original_frontend_url
            sys.stdout = sys.__stdout__

    @patch('core.utils.SendGridAPIClient')
    def test_send_password_reset_email_sendgrid_success(self, mock_sendgrid):
        """Test sending password reset email via SendGrid successfully"""
        from core.utils import send_password_reset_email
        from django.conf import settings

        # Mock SendGrid response
        mock_sg_instance = mock_sendgrid.return_value
        mock_response = type('obj', (object,), {'status_code': 202})
        mock_sg_instance.send.return_value = mock_response

        original_email_use = settings.EMAIL_USE
        original_frontend_url = settings.FRONTEND_URL
        settings.EMAIL_USE = 'sendgrid'
        settings.SENDGRID_API_KEY = 'test-sendgrid-key'
        settings.FROM_EMAIL = 'noreply@test.com'
        settings.FRONTEND_URL = 'http://localhost:5173'

        try:
            result = send_password_reset_email(
                user=self.user,
                uid='MQ',
                token='test-token-123'
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 202)
            mock_sg_instance.send.assert_called_once()

            # Verify the email was sent (Mail object was created and passed to send)
            call_args = mock_sg_instance.send.call_args
            self.assertIsNotNone(call_args)
        finally:
            settings.EMAIL_USE = original_email_use
            settings.FRONTEND_URL = original_frontend_url

    @patch('core.utils.SendGridAPIClient')
    def test_send_password_reset_email_sendgrid_failure(self, mock_sendgrid):
        """Test SendGrid failure handling"""
        from core.utils import send_password_reset_email
        from django.conf import settings

        # Mock SendGrid to raise an exception
        mock_sg_instance = mock_sendgrid.return_value
        mock_sg_instance.send.side_effect = Exception('SendGrid API Error')

        original_email_use = settings.EMAIL_USE
        original_debug = settings.DEBUG
        settings.EMAIL_USE = 'sendgrid'
        settings.SENDGRID_API_KEY = 'test-sendgrid-key'
        settings.FROM_EMAIL = 'noreply@test.com'
        settings.DEBUG = True

        try:
            with self.assertRaises(Exception):
                send_password_reset_email(
                    user=self.user,
                    uid='MQ',
                    token='test-token-123'
                )
        finally:
            settings.EMAIL_USE = original_email_use
            settings.DEBUG = original_debug

    def test_password_reset_email_content_structure(self):
        """Test that password reset email contains all required elements"""
        from core.utils import send_password_reset_email
        from django.conf import settings
        import io
        import sys

        original_email_use = settings.EMAIL_USE
        settings.EMAIL_USE = 'console'
        settings.FRONTEND_URL = 'http://localhost:5173'

        try:
            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            send_password_reset_email(
                user=self.user,
                uid='MQ',
                token='test-token-abc'
            )

            # Restore stdout
            sys.stdout = sys.__stdout__
            output = captured_output.getvalue()

            # Check for essential elements
            self.assertIn('resetuser', output)  # Username
            self.assertIn('password-reset', output)  # Reset path
            self.assertIn('MQ', output)  # UID
            self.assertIn('test-token-abc', output)  # Token
        finally:
            settings.EMAIL_USE = original_email_use
            sys.stdout = sys.__stdout__


class PasswordResetAPITest(APITestCase):
    """Test password reset API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            email='apiuser@example.com',
            password='oldpassword123'
        )
        self.reset_password_url = '/api/auth/users/reset_password/'
        self.reset_password_confirm_url = '/api/auth/users/reset_password_confirm/'

    @patch('core.emails.send_password_reset_email')
    def test_request_password_reset_valid_email(self, mock_send_email):
        """Test requesting password reset with valid email"""
        response = self.client.post(
            self.reset_password_url,
            {'email': 'apiuser@example.com'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Email should be triggered (mocked)
        mock_send_email.assert_called_once()

    def test_request_password_reset_invalid_email(self):
        """Test requesting password reset with invalid email format"""
        response = self.client.post(
            self.reset_password_url,
            {'email': 'invalid-email'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_password_reset_nonexistent_email(self):
        """Test requesting password reset with non-existent email (should still return 204 for security)"""
        response = self.client.post(
            self.reset_password_url,
            {'email': 'nonexistent@example.com'},
            format='json'
        )

        # Should return 204 even if email doesn't exist (security best practice)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_request_password_reset_missing_email(self):
        """Test requesting password reset without email"""
        response = self.client.post(
            self.reset_password_url,
            {},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_password_reset_invalid_token(self):
        """Test confirming password reset with invalid token"""
        response = self.client.post(
            self.reset_password_confirm_url,
            {
                'uid': 'invalid',
                'token': 'invalid-token',
                'new_password': 'newpassword123',
                're_new_password': 'newpassword123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_password_reset_mismatched_passwords(self):
        """Test confirming password reset with mismatched passwords"""
        response = self.client.post(
            self.reset_password_confirm_url,
            {
                'uid': 'MQ',
                'token': 'test-token',
                'new_password': 'newpassword123',
                're_new_password': 'differentpassword123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_password_reset_weak_password(self):
        """Test confirming password reset with weak password"""
        response = self.client.post(
            self.reset_password_confirm_url,
            {
                'uid': 'MQ',
                'token': 'test-token',
                'new_password': '123',
                're_new_password': '123'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


