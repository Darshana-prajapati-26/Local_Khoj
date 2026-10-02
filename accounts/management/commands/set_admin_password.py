from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('username', nargs='?', default='admin')
        parser.add_argument('password', nargs='?', default='admin123')

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username=options['username'])
            user.set_password(options['password'])
            user.save()
            self.stdout.write(self.style.SUCCESS('Password updated'))
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username=options['username'],
                email='admin@example.com',
                password=options['password']
            )
            self.stdout.write(self.style.SUCCESS('Admin user created'))
