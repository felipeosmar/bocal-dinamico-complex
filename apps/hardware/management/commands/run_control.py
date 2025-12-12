from django.core.management.base import BaseCommand
from apps.hardware.services import ControlLoop

class Command(BaseCommand):
    help = 'Runs the main control loop for actuators and profilometer'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Initializing Control Loop...'))
        loop = ControlLoop()
        loop.start()
