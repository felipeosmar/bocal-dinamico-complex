from django.db import models

class ActuatorConfig(models.Model):
    name = models.CharField(max_length=50)
    modbus_id = models.PositiveIntegerField(unique=True)
    
    # Calibration/Limits
    min_position = models.IntegerField(default=0)
    max_position = models.IntegerField(default=4095)
    
    # Offsets/Correction
    offset = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} (ID: {self.modbus_id})"

class ProfileConfig(models.Model):
    """Configuration for the Profilometer reading"""
    name = models.CharField(max_length=50, default="Main Profilometer")
    
    # Communication settings if different from default or dynamic
    # For now assuming fixed Serial/Modbus settings in driver, but good to have here if needed
    
    target_value = models.FloatField(help_text="Target profile reading value", default=0.0)
    tolerance = models.FloatField(help_text="Acceptable deviation (+/-)", default=0.5)

    def __str__(self):
        return self.name

class ControlSettings(models.Model):
    """Global control loop settings"""
    is_active = models.BooleanField(default=False)
    loop_interval_ms = models.PositiveIntegerField(default=100) # Control loop speed
    
    kp = models.FloatField(default=1.0, help_text="Proportional Gain")
    ki = models.FloatField(default=0.0, help_text="Integral Gain")
    kd = models.FloatField(default=0.0, help_text="Derivative Gain")

    def __str__(self):
        return f"Control Settings (Active: {self.is_active})"

    def save(self, *args, **kwargs):
        if not self.pk and ControlSettings.objects.exists():
            # There can be only one ControlSettings instance
            return
        return super(ControlSettings, self).save(*args, **kwargs)
