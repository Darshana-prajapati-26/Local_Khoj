"""
Sets up Google OAuth in the database using credentials from .env
Usage: python manage.py setup_google_oauth
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Configure Google OAuth app in database from .env credentials'

    def handle(self, *args, **options):
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp

        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
        secret    = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()

        if not client_id or not secret:
            self.stderr.write(self.style.ERROR(
                '\n✗ GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in .env\n'
                '  Get them from: https://console.cloud.google.com\n'
                '  → APIs & Services → Credentials → Create OAuth 2.0 Client ID\n'
                '  Redirect URI to add: http://localhost:8000/accounts/google/login/callback/\n'
            ))
            return

        # Ensure site is correct
        site, _ = Site.objects.get_or_create(id=settings.SITE_ID)
        site.domain = 'localhost:8000'
        site.name   = 'Local Khoj'
        site.save()
        self.stdout.write(f'✓ Site set to: {site.domain}')

        # Create or update Google SocialApp
        app, created = SocialApp.objects.update_or_create(
            provider='google',
            defaults={
                'name':      'Google',
                'client_id': client_id,
                'secret':    secret,
                'key':       '',
            }
        )
        app.sites.add(site)
        app.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ {action} Google OAuth app\n'
            f'  Client ID : {client_id[:40]}...\n'
            f'  Site      : {site.domain}\n\n'
            f'  Google login is now active at:\n'
            f'  http://localhost:8000/login/\n'
        ))
