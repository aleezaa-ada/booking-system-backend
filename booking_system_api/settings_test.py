"""
Test settings - overrides database to use SQLite in-memory
so tests run without a local PostgreSQL server.
"""
from .settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashing to speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use console email backend for tests (no SendGrid calls)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_USE = 'console'
SENDGRID_API_KEY = 'test-key'
FROM_EMAIL = 'test@example.com'
