from django.core.management.base import BaseCommand
from apps.hardware.models import ActuatorConfig, ProfileConfig, ControlSettings

class Command(BaseCommand):
    help = 'Seeds initial data for Actuators, ProfileConfig, and ControlSettings'

    def handle(self, *args, **kwargs):
        # Control Settings
        if not ControlSettings.objects.exists():
            ControlSettings.objects.create(is_active=False, loop_interval_ms=100, kp=1.0)
            self.stdout.write(self.style.SUCCESS('Created default ControlSettings.'))
        else:
            self.stdout.write('ControlSettings already exist.')

        # Profile Config
        if not ProfileConfig.objects.exists():
            ProfileConfig.objects.create(name="Default Profile", target_value=12.0, tolerance=0.5)
            self.stdout.write(self.style.SUCCESS('Created default ProfileConfig.'))
        else:
            self.stdout.write('ProfileConfig already exists.')

        # Actuators
        desired_ids = [1, 2, 3] # As per documentation/standard setup
        for mid in desired_ids:
            obj, created = ActuatorConfig.objects.get_or_create(
                modbus_id=mid,
                defaults={
                    'name': f'Actuator {mid}',
                    'min_position': 0,
                    'max_position': 4095
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Actuator {mid}.'))
            else:
                self.stdout.write(f'Actuator {mid} already exists.')
