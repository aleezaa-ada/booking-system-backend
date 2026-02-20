"""
Views for booking_system_api project.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """Health check endpoint for Render deployment."""
    return JsonResponse({"status": "ok"}, status=200)
