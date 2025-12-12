from django.views.generic import TemplateView, View
from django.shortcuts import redirect
from apps.hardware.models import ActuatorConfig, ProfileConfig, ControlSettings

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

class UpdateSimulationView(View):
    def post(self, request, *args, **kwargs):
        profile = ProfileConfig.objects.first()
        if profile:
            # Case 1: Slider update
            val = request.POST.get('simulated_value')
            if val is not None:
                try:
                    profile.simulated_value = float(val)
                    profile.is_simulated = True # Auto-enable
                    profile.save()
                except ValueError:
                    pass
            
            # Case 2: Toggle update (Hidden input 'toggle_update' tells us this form was sent)
            if 'toggle_update' in request.POST:
                is_sim = request.POST.get('is_simulated')
                profile.is_simulated = (is_sim == 'on')
                profile.save()
                 
        return redirect('dashboard')
