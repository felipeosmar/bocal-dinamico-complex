from django.contrib import admin
from .models import ActuatorConfig, ProfileConfig, ControlSettings

@admin.register(ActuatorConfig)
class ActuatorConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'modbus_id', 'min_position', 'max_position', 'offset')
    list_editable = ('min_position', 'max_position', 'offset')

@admin.register(ProfileConfig)
class ProfileConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_value', 'tolerance', 'is_simulated', 'simulated_value')
    list_editable = ('target_value', 'tolerance', 'is_simulated', 'simulated_value')

@admin.register(ControlSettings)
class ControlSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'loop_interval_ms', 'kp')
    list_editable = ('is_active', 'loop_interval_ms', 'kp')
