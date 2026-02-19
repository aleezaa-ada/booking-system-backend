"""
Views for booking_system_api project.
"""
from django.http import JsonResponse


def health_check(request):
    """Health check endpoint for Render deployment."""
    return JsonResponse({"status": "ok"}, status=200)
