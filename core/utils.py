from django.core.mail import send_mail
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_booking_notification_email(booking, subject, template_name):
    user_email = booking.user.email
    resource_name = booking.resource.name
    start_time = booking.start_time.strftime('%Y-%m-%d %H:%M')
    end_time = booking.end_time.strftime('%H:%M')
    notes = booking.notes if booking.notes else "No notes given"

    # Customize message based on event type
    if template_name == "booking_cancelled_template":
        status_text = "been cancelled"
    elif template_name == "booking_details_updated_template":
        status_text = "been updated"
    elif template_name == "booking_status_updated_template":
        status_text = f"status has been updated to {booking.status}"
    elif template_name == "booking_created_template":
        status_text = f"been confirmed with status: {booking.status}"
    else:
        status_text = f"been {booking.status}"

    # Plain text message
    plain_message = f"Dear {booking.user.username},\n\n" \
        f"Your booking for {resource_name} from {start_time} to {end_time} has {status_text}.\n" \
        f"Notes: {notes}\n\n" \
        f"Thank you for using our booking system."

    # HTML message (for SendGrid)
    html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
          <h2 style="color: #4a90e2; margin-bottom: 20px;">Booking Notification</h2>
          <p>Dear <strong>{booking.user.username}</strong>,</p>
          <p>Your booking for <strong style="color: #4a90e2;">{resource_name}</strong> has {status_text}.</p>
          <div style="background-color: white; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Time:</strong> {start_time} to {end_time}</p>
            <p style="margin: 5px 0;"><strong>Notes:</strong> {notes}</p>
          </div>
          <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
          <p style="color: #666; font-size: 14px;">Thank you for using our booking system.</p>
        </div>
      </body>
    </html>
    """

    # Check EMAIL_USE setting to determine which backend to use
    if settings.EMAIL_USE == 'sendgrid':
        # Use SendGrid API
        try:
            message = Mail(
                from_email=settings.FROM_EMAIL,
                to_emails=user_email,
                subject=subject,
                html_content=html_message
            )

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            print(f"✅ SendGrid email sent to {user_email}. Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ SendGrid error: {e}")
            # Fallback to console in case of error
            print(f"Email Content:\n{plain_message}")
            return False
    else:
        # Use Django's console backend (development)
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"📧 Console email sent to {user_email}")
