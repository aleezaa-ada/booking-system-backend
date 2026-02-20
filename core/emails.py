"""
Custom email classes for password reset using SendGrid
"""
from djoser.email import PasswordResetEmail as BasePasswordResetEmail
from .utils import send_password_reset_email


class PasswordResetEmail(BasePasswordResetEmail):
    """
    Custom password reset email that uses SendGrid
    """
    template_name = 'email/password_reset.html'

    def send(self, to, *args, **kwargs):
        """
        Send password reset email via SendGrid
        """
        context = self.get_context_data()

        # Get the password reset URL components
        uid = context.get('uid')
        token = context.get('token')
        protocol = context.get('protocol', 'http')
        domain = context.get('domain')
        user = context.get('user')

        # Use the utility function to send the email
        return send_password_reset_email(user, uid, token, protocol, domain)
