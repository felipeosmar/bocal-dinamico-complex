from django.test import TestCase
from apps.hardware.models import ActuatorConfig, ProfileConfig, ControlSettings
from django.core.management import call_command

class HardwareModelTests(TestCase):
    def test_actuator_creation(self):
        actuator = ActuatorConfig.objects.create(name="Test Actuator", modbus_id=1)
        self.assertEqual(actuator.name, "Test Actuator")
        self.assertEqual(actuator.modbus_id, 1)

    def test_control_settings_singleton(self):
        s1 = ControlSettings.objects.create(is_active=True)
        self.assertTrue(s1.is_active)
        s2 = ControlSettings.objects.create(is_active=False)
        self.assertEqual(ControlSettings.objects.count(), 1)

    def test_init_data_command(self):
        call_command('init_data')
        self.assertTrue(ControlSettings.objects.exists())
        self.assertTrue(ProfileConfig.objects.exists())
        self.assertEqual(ActuatorConfig.objects.count(), 3)
