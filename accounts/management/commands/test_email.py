"""
Management command to test email configuration.
Usage: python manage.py test_email your@email.com
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP configuration'

    def add_arguments(self, parser):
        parser.add_argument('recipient', nargs='?', default=None,
                            help='Email address to send test to (defaults to EMAIL_HOST_USER)')

    def handle(self, *args, **options):
        recipient = options['recipient'] or settings.EMAIL_HOST_USER

        self.stdout.write(f"\n📧 Email Configuration:")
        self.stdout.write(f"   Backend  : {settings.EMAIL_BACKEND}")
        self.stdout.write(f"   Host     : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"   User     : {settings.EMAIL_HOST_USER or '(not set)'}")
        self.stdout.write(f"   Password : {'✓ set' if settings.EMAIL_HOST_PASSWORD else '✗ NOT SET'}")
        self.stdout.write(f"   From     : {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"   To       : {recipient}\n")

        if not settings.EMAIL_HOST_USER or settings.EMAIL_HOST_USER == 'your-gmail@gmail.com':
            self.stderr.write(self.style.ERROR(
                "✗ EMAIL_HOST_USER is not set in .env\n"
                "  Edit Local_khoj/.env and set your real Gmail address."
            ))
            return

        if not settings.EMAIL_HOST_PASSWORD or settings.EMAIL_HOST_PASSWORD == 'your-16-char-app-password':
            self.stderr.write(self.style.ERROR(
                "✗ EMAIL_HOST_PASSWORD is not set in .env\n"
                "  Get an App Password from: https://myaccount.google.com/apppasswords"
            ))
            return

        self.stdout.write("Sending test email...")
        try:
            send_mail(
                subject='✅ Local Khoj — Email Test',
                message=(
                    'This is a test email from Local Khoj.\n\n'
                    'If you received this, your email configuration is working correctly!\n\n'
                    '— Local Khoj Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(
                f"✓ Test email sent successfully to {recipient}\n"
                f"  Check your inbox (and spam folder)."
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"✗ Failed to send email:\n  {e}\n"))
            if '535' in str(e) or 'BadCredentials' in str(e):
                self.stderr.write(self.style.WARNING(
                    "\n  FIX: You used your Gmail login password.\n"
                    "  You need an App Password instead:\n"
                    "  → https://myaccount.google.com/apppasswords\n"
                    "  (Requires 2-Step Verification to be ON)"
                ))
            elif 'Connection refused' in str(e):
                self.stderr.write(self.style.WARNING(
                    "\n  FIX: Cannot connect to smtp.gmail.com:587\n"
                    "  Try: EMAIL_PORT=465 and EMAIL_USE_SSL=True in .env"
                ))
