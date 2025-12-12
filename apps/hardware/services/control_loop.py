import time
import logging
from apps.hardware.models import ControlSettings, ActuatorConfig, ProfileConfig
from .mighty_zap import MightyZapDriver
from .profilometer import ProfilometerDriver

logger = logging.getLogger(__name__)

class ControlLoop:
    def __init__(self):
        self.actuator_driver = MightyZapDriver()
        self.profilometer_driver = ProfilometerDriver()
        self.running = False

    def start(self):
        logger.info("Starting Control Loop...")
        self.actuator_driver.connect()
        self.running = True
        self.loop()

    def loop(self):
        while self.running:
            try:
                settings = ControlSettings.objects.first()
                if not settings or not settings.is_active:
                    logger.info("Control inactive. Waiting...")
                    time.sleep(1)
                    continue

                # Read Profilometer
                current_value = self.profilometer_driver.read_value()
                
                # Get Target
                profile_config = ProfileConfig.objects.first()
                if not profile_config:
                    logger.warning("No Profile Configuration found.")
                    time.sleep(1)
                    continue
                
                target = profile_config.target_value
                error = target - current_value
                
                logger.info(f"Target: {target}, Current: {current_value:.2f}, Error: {error:.2f}")

                # Simple Logic: If error is positive, move actuators one way, else other way
                # This is a placeholder for real PID
                actuators = ActuatorConfig.objects.all()
                for actuator in actuators:
                    # Logic: New Position = Current Position + (Error * KP)
                    # For simulation, we just calculate a dummy new position
                    current_pos = self.actuator_driver.get_position(actuator.modbus_id)
                    
                    # Disclaimer: This logic assumes direct correlation which might be inverse
                    correction = int(error * settings.kp * 10) 
                    new_pos = max(actuator.min_position, min(actuator.max_position, current_pos + correction))
                    
                    self.actuator_driver.set_position(actuator.modbus_id, new_pos)

                time.sleep(settings.loop_interval_ms / 1000.0)

            except KeyboardInterrupt:
                logger.info("Stopping Control Loop...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in control loop: {e}")
                time.sleep(1)
