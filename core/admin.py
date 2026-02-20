from django.contrib import admin
from .models import Resource, Booking, UserProfile

admin.site.register(Resource)
admin.site.register(Booking)
admin.site.register(UserProfile)
