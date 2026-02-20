# Booking System Backend API

A robust Django REST Framework-based backend API for managing resource bookings with authentication, real-time availability tracking, and email notifications.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Local Development](#local-development)
  - [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Running the Development Server](#running-the-development-server)
  - [Admin Interface](#admin-interface)
  - [API Documentation](#api-documentation)
- [Authentication](#authentication)
  - [Token-Based Authentication](#token-based-authentication)
  - [User Registration & Login](#user-registration--login)
  - [Protected Endpoints](#protected-endpoints)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
  - [Render Deployment](#render-deployment)
  - [Environment Configuration](#environment-configuration)
  - [Build Process](#build-process)
- [Technical Decisions](#technical-decisions)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Booking System Backend is an enterprise-grade REST API built with Django 5.2 and Django REST Framework. It provides comprehensive booking management functionality with role-based access control, real-time resource availability, and automated email notifications.

**Key Features:**
- Token-based authentication with Djoser
- Resource booking management with conflict detection
- User profile management with profile pictures 
- Email notifications via SendGrid
- Role-based permissions (Admin/User)#
- Production-ready with PostgreSQL
- Real-time availability tracking
- Booking validation (30-minute advance booking rule)

---

## Architecture

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 5.2.11 |
| API Framework | Django REST Framework | 3.16.1 |
| Database | PostgreSQL | 2.9.11 (psycopg2) |
| Authentication | Djoser | 2.3.3 |
| Token Auth | djangorestframework-simplejwt | 5.5.1 |
| Email Service | SendGrid | 6.12.5 |
| Static Files | WhiteNoise | 6.11.0 |
| CORS | django-cors-headers | 4.9.0 |
| Environment Config | python-decouple | 3.8 |
| WSGI Server | Gunicorn | 25.1.0 |

### Project Structure

```
booking-system-backend/
├── booking_system_api/       # Django project configuration
│   ├── settings.py           # Application settings
│   ├── urls.py               # Root URL configuration
│   ├── views.py              # Health check endpoint
│   └── wsgi.py               # WSGI configuration
│
├── core/                     # Main application
│   ├── models.py             # Database models (User, Resource, Booking)
│   ├── serializers.py        # REST API serializers
│   ├── views.py              # API views and viewsets
│   ├── urls.py               # App-level URL routing
│   ├── utils.py              # Utility functions (email)
│   ├── admin.py              # Django admin configuration
│   ├── migrations/           # Database migrations
│   └── management/           # Custom management commands
│       └── commands/
│           ├── ensure_superuser.py
│           └── create_user_profiles.py
│
├── staticfiles/              # Collected static files
├── requirements.txt          # Python dependencies
├── Pipfile                   # Pipenv configuration
├── manage.py                 # Django management script
├── build.sh                  # Deployment build script
└── pytest.ini                # Test configuration
```

### Application Flow

```
Client Request
     ↓
CORS Middleware → Authentication → View/ViewSet
     ↓                               ↓
Serializer Validation → Model Logic → Database
     ↓
Email Notification (if applicable)
     ↓
JSON Response
```

---

## Prerequisites

- **Python**: 3.13 or higher
- **PostgreSQL**: 12 or higher
- **pip**: Latest version
- **Virtual Environment**: pipenv or venv recommended
- **Git**: For version control

---

## Setup Instructions

### Local Development

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd booking-system/booking-system-backend
   ```

2. **Create Virtual Environment**
   ```bash
   # Using pipenv (recommended)
   pipenv install

   # Or using venv
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate   # On Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL Database**
   ```bash
   # Create database
   psql postgres
   CREATE DATABASE booking_system_db;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE booking_system_db TO your_username;
   \q
   ```

5. **Configure Environment Variables**
   
   Create a `.env` file in the project root:
   ```env
   # Django Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/booking_system_db

   # Email Configuration
   EMAIL_USE=console  # Use 'sendgrid' for production
   SENDGRID_API_KEY=your-sendgrid-api-key
   FROM_EMAIL=aleezaahmed315@gmail.com
   TO_EMAIL=aleezaahmed315@gmail.com

   # Frontend URL (for CORS)
   FRONTEND_URL=http://localhost:5173
   ```

6. **Run Database Migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   # Or use the custom command
   python manage.py ensure_superuser
   ```

8. **Collect Static Files**
   ```bash
   python manage.py collectstatic --no-input
   ```

9. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

   The API will be available at `http://localhost:8000`

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key for cryptographic signing | Yes | - |
| `DEBUG` | Enable debug mode (never True in production) | No | False |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | No | localhost,127.0.0.1 |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `EMAIL_USE` | Email backend (`console` or `sendgrid`) | No | console |
| `SENDGRID_API_KEY` | SendGrid API key for email | Conditional | - |
| `FROM_EMAIL` | From email address | No | noreply@bookingsystem.local |
| `TO_EMAIL` | Admin notification email | No | - |
| `FRONTEND_URL` | Frontend URL for CORS | No | - |

---

## Usage

### Running the Development Server

```bash
# Standard Django development server
python manage.py runserver

# Specify port
python manage.py runserver 8080

# Bind to all interfaces
python manage.py runserver 0.0.0.0:8000
```

### Admin Interface

Access the Django admin panel at `http://localhost:8000/admin/`

**Admin Capabilities:**
- Manage users, resources, and bookings
- View all system data
- Perform CRUD operations
- Monitor booking status

### API Documentation

The API follows RESTful conventions and returns JSON responses.

**Base URL:** `http://localhost:8000/api/`

**Response Format:**
```json
{
  "id": 1,
  "field": "value",
  "timestamp": "2026-02-20T10:30:00Z"
}
```

**Error Format:**
```json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
```

---

## Authentication

### Token-Based Authentication

The system uses **Token Authentication** provided by Django REST Framework and Djoser.

**Authentication Flow:**
1. User registers or logs in
2. Server returns authentication token
3. Client includes token in subsequent requests
4. Server validates token and processes request

### User Registration & Login

#### Register New User
```http
POST /api/auth/users/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Login (Obtain Token)
```http
POST /api/auth/token/login/
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "auth_token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

#### Get Current User
```http
GET /api/auth/users/me/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

#### Logout
```http
POST /api/auth/token/logout/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### Protected Endpoints

All API endpoints require authentication except:
- Health check: `/health/`
- Admin login: `/admin/`

**Include token in requests:**
```http
Authorization: Token your-token-here
```

**Example with cURL:**
```bash
curl -H "Authorization: Token your-token-here" \
     http://localhost:8000/api/bookings/
```

---

## Database Schema

### Models

#### **User** (Django's built-in User model)
- `id`: Primary key
- `username`: Unique username
- `email`: Email address
- `first_name`: First name
- `last_name`: Last name
- `password`: Hashed password
- `is_staff`: Admin flag
- `is_active`: Active status

#### **UserProfile**
- `id`: Primary key
- `user`: OneToOne → User
- `profile_picture`: URL (Cloudinary)
- `cloudinary_public_id`: String
- `updated_at`: DateTime (auto)

#### **Resource**
- `id`: Primary key
- `name`: String (255 chars)
- `description`: Text
- `capacity`: Integer (default: 1)
- `is_available`: Boolean (default: True)

#### **Booking**
- `id`: Primary key
- `user`: ForeignKey → User
- `resource`: ForeignKey → Resource
- `start_time`: DateTime
- `end_time`: DateTime
- `status`: Choice (pending/confirmed/cancelled/rejected)
- `notes`: Text
- `created_at`: DateTime (auto)
- `updated_at`: DateTime (auto)

**Constraints:**
- Unique together: (resource, start_time, end_time, user)
- Ordering: By start_time

### Entity Relationship Diagram

```
User ──────┬──────> UserProfile (1:1)
           │
           └──────> Booking (1:N)
                        │
                        └──────> Resource (N:1)
```

---

## API Endpoints

### Authentication Endpoints (Djoser)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/users/` | Register new user | No |
| POST | `/api/auth/token/login/` | Login and get token | No |
| POST | `/api/auth/token/logout/` | Logout and invalidate token | Yes |
| GET | `/api/auth/users/me/` | Get current user details | Yes |
| PUT/PATCH | `/api/auth/users/me/` | Update user details | Yes |
| DELETE | `/api/auth/users/me/` | Delete user account | Yes |
| POST | `/api/auth/users/set_password/` | Change password | Yes |

### Resource Endpoints

| Method | Endpoint | Description | Auth Required | Admin Only |
|--------|----------|-------------|---------------|------------|
| GET | `/api/resources/` | List all resources | No | No |
| POST | `/api/resources/` | Create new resource | Yes | Yes |
| GET | `/api/resources/{id}/` | Get resource details | No | No |
| PUT/PATCH | `/api/resources/{id}/` | Update resource | Yes | Yes |
| DELETE | `/api/resources/{id}/` | Delete resource | Yes | Yes |

**Resource Response:**
```json
{
  "id": 1,
  "name": "Conference Room A",
  "description": "Main conference room with projector",
  "capacity": 10,
  "is_available": true,
  "availability_status": "available"
}
```

### Booking Endpoints

| Method | Endpoint | Description | Auth Required | Permissions |
|--------|----------|-------------|---------------|-------------|
| GET | `/api/bookings/` | List user's bookings (or all if admin) | Yes | Own bookings or admin |
| POST | `/api/bookings/` | Create new booking | Yes | Authenticated |
| GET | `/api/bookings/{id}/` | Get booking details | Yes | Owner or admin |
| PUT/PATCH | `/api/bookings/{id}/` | Update booking | Yes | Owner or admin |
| DELETE | `/api/bookings/{id}/` | Cancel booking | Yes | Owner or admin |

**Create Booking:**
```json
{
  "resource": 1,
  "start_time": "2026-02-21T14:00:00Z",
  "end_time": "2026-02-21T16:00:00Z",
  "status": "pending",
  "notes": "Team meeting"
}
```

**Booking Response:**
```json
{
  "id": 1,
  "user": 2,
  "username": "johndoe",
  "resource": 1,
  "resource_name": "Conference Room A",
  "start_time": "2026-02-21T14:00:00Z",
  "end_time": "2026-02-21T16:00:00Z",
  "status": "pending",
  "notes": "Team meeting",
  "created_at": "2026-02-20T10:30:00Z",
  "updated_at": "2026-02-20T10:30:00Z"
}
```

### Profile Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| PUT/PATCH | `/api/profile/picture/` | Update profile picture | Yes |
| DELETE | `/api/profile/picture/delete/` | Remove profile picture | Yes |

**Update Profile Picture:**
```json
{
  "profile_picture": "https://res.cloudinary.com/...",
  "cloudinary_public_id": "user_profiles/abc123"
}
```

### Health Check

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health/` | Server health check | No |

---

## Deployment

### Render Deployment

The application is configured for deployment on **Render** with automatic builds and deployments.

#### Prerequisites

1. Render account
2. PostgreSQL database on Render
3. SendGrid account (for email notifications)

#### Deployment Steps

1. **Create PostgreSQL Database on Render**
   - Go to Render Dashboard → New → PostgreSQL
   - Note the `Internal Database URL`

2. **Create Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect your Git repository
   - Configure settings:
     - **Name:** booking-system-backend
     - **Environment:** Python 3
     - **Build Command:** `./build.sh`
     - **Start Command:** `gunicorn booking_system_api.wsgi:application`

3. **Configure Environment Variables**

   Add the following environment variables in Render:

   ```env
   SECRET_KEY=<generate-secure-key>
   DEBUG=False
   ALLOWED_HOSTS=.onrender.com
   DATABASE_URL=<render-postgres-url>
   EMAIL_USE=sendgrid
   SENDGRID_API_KEY=<your-sendgrid-key>
   FROM_EMAIL=aleezaahmed315@gmail.com
   TO_EMAIL=aleezaahmed315@gmail.com
   FRONTEND_URL=https://your-frontend.onrender.com
   PYTHON_VERSION=3.13.0
   ```

4. **Deploy**
   - Render will automatically build and deploy
   - Monitor build logs for any issues

### Environment Configuration

#### Production Settings Checklist

- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY` (use Django's `get_random_secret_key()`)
- [ ] Proper `ALLOWED_HOSTS` configuration
- [ ] PostgreSQL database configured
- [ ] SendGrid API key set up
- [ ] CORS origins restricted to frontend domain
- [ ] Static files collected and served via WhiteNoise
- [ ] HTTPS enabled (automatic on Render)

### Build Process

The `build.sh` script handles the deployment build:

```bash
#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Create superuser if needed
python manage.py ensure_superuser

# Create user profiles for existing users
python manage.py create_user_profiles
```

**Build Steps:**
1. ✅ Install Python dependencies
2. ✅ Collect static files (Django admin, DRF)
3. ✅ Apply database migrations
4. ✅ Ensure superuser exists
5. ✅ Create user profiles

---

## Technical Decisions

### 1. **Django REST Framework (DRF)**
   - **Why:** Industry-standard for building REST APIs in Django
   - **Benefits:** Serialization, authentication, viewsets, browsable API
   - **Alternative considered:** Django Ninja (rejected for less mature ecosystem)

### 2. **Token Authentication with Djoser**
   - **Why:** Simple, stateless authentication
   - **Benefits:** Works well with SPAs, no session management
   - **Alternative considered:** JWT (rejected for complexity; simplejwt included for future)

### 3. **PostgreSQL Database**
   - **Why:** Robust, ACID-compliant, production-ready
   - **Benefits:** Complex queries, JSON fields, full-text search
   - **Alternative considered:** SQLite (rejected for production use)

### 4. **WhiteNoise for Static Files**
   - **Why:** Simplified static file serving without CDN
   - **Benefits:** Compression, caching headers, no extra service
   - **Alternative considered:** S3 (rejected for simplicity)

### 5. **SendGrid for Email**
   - **Why:** Reliable, scalable email delivery
   - **Benefits:** API-based, deliverability monitoring, templates
   - **Alternative considered:** AWS SES (rejected for complexity)

### 6. **Custom Permission Classes**
   - **Why:** Fine-grained access control
   - **Implementation:** `IsAdminOrReadOnly` for resources
   - **Benefit:** Users can view all resources but only admins can modify

### 7. **Booking Validation Logic**
   - **30-minute advance booking rule:** Prevents last-minute conflicts
   - **Overlap detection:** Prevents double-booking resources
   - **Status-based filtering:** Cancelled/rejected bookings don't block slots
   - **Soft validation on updates:** Allows admins to fix booking issues

### 8. **Email Notifications**
   - **Trigger points:** Create, update, cancel bookings
   - **Graceful degradation:** Falls back to console if SendGrid fails
   - **HTML + Plain text:** Ensures compatibility

### 9. **CORS Configuration**
   - **Development:** Regex patterns for localhost and Codespaces
   - **Production:** Explicit frontend URL whitelist
   - **Security:** Never `CORS_ALLOW_ALL_ORIGINS = True` in production

### 10. **Project Structure**
   - **Single app architecture:** Simple, focused on booking domain
   - **Separation of concerns:** Models, views, serializers, utils
   - **Custom management commands:** Deployment automation

---

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest core/tests.py

# Verbose output
pytest -v
```

### Test Configuration

Tests are configured in `pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = booking_system_api.settings
python_files = tests.py test_*.py *_tests.py
```

### Writing Tests

Example test structure:
```python
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

class BookingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_booking(self):
        # Test implementation
        pass
```

---

## Troubleshooting

### Common Issues

#### 1. **Database Connection Error**
```
django.db.utils.OperationalError: could not connect to server
```

**Solution:**
- Check PostgreSQL is running: `pg_isready`
- Verify `DATABASE_URL` in `.env`
- Ensure database exists: `psql -l`

#### 2. **Static Files Not Loading**
```
GET /static/admin/css/base.css 404
```

**Solution:**
```bash
python manage.py collectstatic --no-input
```

#### 3. **CORS Error**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
- Check `FRONTEND_URL` in environment variables
- Verify `CORS_ALLOWED_ORIGINS` in settings
- Ensure `corsheaders` middleware is enabled

#### 4. **Token Authentication Failed**
```
{"detail": "Invalid token."}
```

**Solution:**
- Verify token is included: `Authorization: Token <token>`
- Check token hasn't expired
- Re-login to get new token

#### 5. **Email Not Sending**
```
SendGrid error: 401 Unauthorized
```

**Solution:**
- Verify `SENDGRID_API_KEY` is correct
- Check SendGrid account status
- Set `EMAIL_USE=console` for testing

#### 6. **Migration Errors**
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**Solution:**
```bash
python manage.py migrate --fake-initial
# Or reset migrations (development only)
python manage.py migrate core zero
python manage.py migrate
```

### Debug Mode

Enable detailed error messages (development only):
```env
DEBUG=True
```

### Logging

Add logging configuration to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

---

## Contributing

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow PEP 8 style guide
   - Add tests for new functionality
   - Update documentation

3. **Run Tests and Linting**
   ```bash
   pytest
   flake8 .
   black .
   isort .
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style

- **Python:** PEP 8 (enforced by Black and Flake8)
- **Imports:** Sorted with isort
- **Line Length:** 120 characters
- **Docstrings:** Google style

### Git Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

---

## License

This project is proprietary and confidential. All rights reserved.

---

## Appendix

### Useful Commands

```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Create new migration
python manage.py makemigrations

# Django shell
python manage.py shell

# Database shell
python manage.py dbshell

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver

# Custom commands
python manage.py ensure_superuser
python manage.py create_user_profiles
```

### Useful URLs

- **Admin:** http://localhost:8000/admin/
- **API Root:** http://localhost:8000/api/
- **Health Check:** http://localhost:8000/health/
- **Browsable API:** http://localhost:8000/api/bookings/

### Dependencies Update

```bash
# Update all dependencies
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade django

# Freeze dependencies
pip freeze > requirements.txt
```

---

**Last Updated:** February 20, 2026  
**Version:** 1.0.0  
**Maintainer:** Aleeza Ahmed

### AI Declaration
I have used AI to plan my code and help write up this README file. I have reviewed and edited the content to ensure accuracy and clarity. The code and documentation reflect my understanding and implementation of the project requirements.

