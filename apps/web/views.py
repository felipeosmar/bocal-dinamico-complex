from django.views.generic import TemplateView, View
from django.shortcuts import redirect
from django.http import JsonResponse
import json
import logging

from apps.hardware.models import ActuatorConfig, ProfileConfig, ControlSettings
from apps.hardware.services.mighty_zap import MightyZapDriver

logger = logging.getLogger(__name__)

class DashboardView(TemplateView):
    template_name = "web/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actuators'] = ActuatorConfig.objects.all()
        context['profile_config'] = ProfileConfig.objects.first()
        context['control_settings'] = ControlSettings.objects.first()
        return context

class ControlStatusView(View):
    def post(self, request, *args, **kwargs):
        settings = ControlSettings.objects.first()
        if settings:
            settings.is_active = not settings.is_active
            settings.save()
        return redirect('dashboard')

class TestActuatorsView(TemplateView):
    template_name = "web/test_actuators.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actuators'] = ActuatorConfig.objects.all()
        return context

class ActuatorCommandView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            actuator_id = data.get('actuator_id')
            position = data.get('position')
            
            if actuator_id is None or position is None:
                return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)
                
            driver = MightyZapDriver()
            if driver.connect():
                # Note: connect() currently returns True always or logs success as per previous file view
                # Ideally we check if real connection worked, but for now we follow existing pattern
                driver.set_position(int(actuator_id), int(position))
                return JsonResponse({'status': 'success', 'message': f'Moved ID {actuator_id} to {position}'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to connect to driver'}, status=500)
                
        except Exception as e:
            logger.error(f"API Error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


