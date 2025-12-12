from django.urls import path
from .views import DashboardView, ControlStatusView, TestActuatorsView, ActuatorCommandView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('actuator-test/', TestActuatorsView.as_view(), name='test_actuators'),
    path('api/set-position/', ActuatorCommandView.as_view(), name='set_actuator_position'),
    path('toggle_control/', ControlStatusView.as_view(), name='toggle_control'),
]
