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
