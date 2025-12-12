import logging
import random
from apps.hardware.models import ProfileConfig

logger = logging.getLogger(__name__)

class ProfilometerDriver:
    def __init__(self):
        pass

    def read_value(self):
        """
        Reads the current value from the profilometer.
        Returns a float.
        """
        try:
            config = ProfileConfig.objects.first()
            if config and config.is_simulated:
                val = config.simulated_value
                logger.debug(f"[SIMULATION] Profilometer read (Manual): {val:.2f}")
                return val
        except Exception:
            pass # Fallback to random simulation if DB fails/not found

        # Default random simulation (or real driver code in future)
        val = random.gauss(10.0, 0.5)
        logger.debug(f"[SIMULATION] Profilometer read (Random): {val:.2f}")
        return val
