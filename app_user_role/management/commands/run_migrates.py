from django.core.management.base import BaseCommand

from app_user_role.challenge import IMigrate


class Command(BaseCommand):
    help = 'For run challenge migrates'

    def handle(self, *args, **options):
        IMigrate.auto_migrate()
        self.stdout.write(self.style.SUCCESS('Challenge migrates end'))
