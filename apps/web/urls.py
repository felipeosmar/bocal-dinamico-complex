from django.urls import path
from .views import DashboardView, ControlStatusView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('toggle_control/', ControlStatusView.as_view(), name='toggle_control'),
]
