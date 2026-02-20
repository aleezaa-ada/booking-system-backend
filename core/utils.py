from django.core.mail import send_mail
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging

logger = logging.getLogger(__name__)


def send_password_reset_email(user, uid, token, protocol='http', domain=None):
    """
    Send password reset email via SendGrid or console
    """
    # Use FRONTEND_URL from settings, which includes the protocol
    frontend_url = settings.FRONTEND_URL

    # If domain is provided by Djoser, ignore it and use our FRONTEND_URL instead
    # Parse protocol and domain from FRONTEND_URL
    if frontend_url.startswith('https://'):
        protocol = 'https'
        domain = frontend_url.replace('https://', '')
    elif frontend_url.startswith('http://'):
        protocol = 'http'
        domain = frontend_url.replace('http://', '')
    else:
        # No protocol in FRONTEND_URL, add default
        domain = frontend_url

    # Construct the reset URL
    reset_url = f"{protocol}://{domain}/password-reset/{uid}/{token}"
    username = user.username if user else 'User'
    user_email = user.email

    # Email subject and body
    subject = "Password Reset Request - Booking System"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #f9f9f9;
                border-radius: 10px;
                padding: 30px;
                border: 1px solid #ddd;
            }}
            .header {{
                background-color: #007bff;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px 10px 0 0;
                margin: -30px -30px 20px -30px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #007bff;
                color: white !important;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
            }}
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <p>Hello {username},</p>
            <p>We received a request to reset your password for your Booking System account.</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                {reset_url}
            </p>
            <div class="warning">
                <strong>⚠️ Security Notice:</strong>
                <ul>
                    <li>This link will expire in 1 hour</li>
                    <li>If you didn't request this reset, please ignore this email</li>
                    <li>Your password won't change until you create a new one</li>
                </ul>
            </div>
            <div class="footer">
                <p>This is an automated message from Booking System. Please do not reply to this email.</p>
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """

    plain_content = f"""
    Hello {username},

    We received a request to reset your password for your Booking System account.

    Click the link below to reset your password:
    {reset_url}

    This link will expire in 1 hour.

    If you didn't request this reset, please ignore this email. Your password won't change until you create a new one.

    This is an automated message from Booking System. Please do not reply to this email.
    """

    # Check if SendGrid is configured
    if settings.EMAIL_USE == 'sendgrid' and hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
        try:
            message = Mail(
                from_email=settings.FROM_EMAIL,
                to_emails=user_email,
                subject=subject,
                plain_text_content=plain_content,
                html_content=html_content
            )

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)

            logger.info(f"Password reset email sent to {user_email}. Status code: {response.status_code}")
            return response

        except Exception as e:
            logger.error(f"Failed to send password reset email via SendGrid: {str(e)}")
            # Fall back to console backend in development
            if settings.DEBUG:
                logger.info(f"Falling back to console email backend")
                logger.info(f"Password reset link: {reset_url}")
            raise
    else:
        # Console backend for development
        print(f"SendGrid not configured. Would send email to: {user_email}")
        print(f"Password reset link: {reset_url}")
        print(f"Subject: {subject}")
        return None


def send_booking_notification_email(booking, subject, template_name):
    user_email = booking.user.email
    resource_name = booking.resource.name
    start_time = booking.start_time.strftime('%Y-%m-%d %H:%M')
    end_time = booking.end_time.strftime('%H:%M')
    notes = booking.notes if booking.notes else "No notes given"

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

    plain_message = f"Dear {booking.user.username},\n\n" \
        f"Your booking for {resource_name} from {start_time} to {end_time} has {status_text}.\n" \
        f"Notes: {notes}\n\n" \
        f"Thank you for using our booking system."

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

    if settings.EMAIL_USE == 'sendgrid':
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
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        print(f"📧 Console email sent to {user_email}")
