import logging
import random

logger = logging.getLogger(__name__)

class ProfilometerDriver:
    def __init__(self):
        pass

    def read_value(self):
        """
        Reads the current value from the profilometer.
        Returns a float.
        """
        # Simulation: Return a random value around a target
        val = random.gauss(10.0, 0.5)
        logger.debug(f"[SIMULATION] Profilometer read: {val:.2f}")
        return val
