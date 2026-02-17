from django.core.mail import send_mail
from django.conf import settings

def send_booking_notification_email(booking, subject, template_name):
    user_email = booking.user.email
    resource_name = booking.resource.name
    start_time = booking.start_time.strftime('%Y-%m-%d %H:%M')
    end_time = booking.end_time.strftime('%H:%M')
    notes = booking.notes if booking.notes else "No notes given"

    # Customize message based on event type
    if template_name == "booking_cancelled_template":
        status_text = "been cancelled"
    else:
        status_text = f"been {booking.status}"

    message = f"Dear {booking.user.username},\n\n" \
                f"Your booking for {resource_name} from {start_time} to {end_time} has {status_text}.\n" \
                f"Notes: {notes}\n\n" \
                f"Thank you."

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL, 
        [user_email],
        fail_silently=False,
    )