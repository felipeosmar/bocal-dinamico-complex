from django.test import TestCase, Client
from django.urls import reverse
from apps.hardware.models import ControlSettings

class DashboardViewTests(TestCase):
    def test_dashboard_status_code(self):
        client = Client()
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/dashboard.html')

    def test_control_toggle(self):
        client = Client()
        ControlSettings.objects.create(is_active=False)
        
        response = client.post(reverse('toggle_control'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        settings = ControlSettings.objects.first()
        self.assertTrue(settings.is_active)
        
        response = client.post(reverse('toggle_control'), follow=True)
        settings.refresh_from_db()
        self.assertFalse(settings.is_active)


