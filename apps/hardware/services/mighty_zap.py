import logging
import time
import struct
import serial

# Tenta importar RPi.GPIO para controle de direção do MAX485
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

logger = logging.getLogger(__name__)

# Endereços MODBUS para MightyZAP (Conforme manual FC_MODBUS)
ADDR_GOAL_POSITION = 0x001E       # Goal Position (R/W)
ADDR_PRESENT_POSITION = 0x0020   # Present Position (R)
ADDR_PRESENT_CURRENT = 0x0024    # Present Current (R)
ADDR_PRESENT_MOTOR_OP_MODE = 0x0026  # Motor Operating Mode (R)

# Configuração padrão do GPIO para controle de direção RS485
DEFAULT_DE_RE_PIN = 18  # GPIO 18 (BCM) - controle DE/RE do MAX485

# Configuração serial padrão
DEFAULT_SERIAL_PORT = '/dev/serial0'  # UART do Raspberry Pi
DEFAULT_BAUDRATE = 57600


def calculate_crc16(data: bytes) -> bytes:
    """Calcula CRC16 MODBUS."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)  # Little-endian


class MightyZapDriver:
    """
    Driver para atuadores MightyZAP via MODBUS RTU sobre RS485.

    Usa a UART do Raspberry Pi com controle de direção via GPIO
    para o transceptor MAX485.
    """

    def __init__(self, port=DEFAULT_SERIAL_PORT, baudrate=DEFAULT_BAUDRATE,
                 de_re_pin=DEFAULT_DE_RE_PIN, simulated=False):
        """
        Inicializa o driver.

        Args:
            port: Porta serial (ex: '/dev/serial0', '/dev/ttyAMA0', '/dev/ttyUSB0')
            baudrate: Taxa de transmissão (padrão 57600)
            de_re_pin: Pino GPIO (BCM) para controle DE/RE do MAX485
            simulated: Se True, apenas simula sem comunicação real
        """
        self.port = port
        self.baudrate = baudrate
        self.de_re_pin = de_re_pin
        self.simulated = simulated
        self.serial = None
        self.gpio_initialized = False

    def connect(self):
        """Conecta à porta serial e configura GPIO."""
        if self.simulated:
            logger.info(f"[SIMULAÇÃO] Driver MightyZap em modo simulado")
            return True

        try:
            # Configura GPIO para controle de direção
            if GPIO_AVAILABLE:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self.de_re_pin, GPIO.OUT)
                GPIO.output(self.de_re_pin, GPIO.LOW)  # Modo recepção inicial
                self.gpio_initialized = True
                logger.info(f"GPIO {self.de_re_pin} configurado para controle DE/RE")
            else:
                logger.warning("RPi.GPIO não disponível - controle de direção desabilitado")

            # Abre porta serial
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5
            )

            logger.info(f"Conectado à porta serial {self.port} @ {self.baudrate} baud")
            return True

        except serial.SerialException as e:
            logger.error(f"Erro ao abrir porta serial {self.port}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False

    def disconnect(self):
        """Fecha conexão e libera recursos."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info("Porta serial fechada")

        if self.gpio_initialized and GPIO_AVAILABLE:
            GPIO.cleanup(self.de_re_pin)
            self.gpio_initialized = False
            logger.info("GPIO liberado")

    def _set_transmit_mode(self):
        """Coloca MAX485 em modo transmissão (DE/RE = HIGH)."""
        if self.gpio_initialized and GPIO_AVAILABLE:
            GPIO.output(self.de_re_pin, GPIO.HIGH)
            time.sleep(0.001)  # Pequeno delay para estabilização

    def _set_receive_mode(self):
        """Coloca MAX485 em modo recepção (DE/RE = LOW)."""
        if self.gpio_initialized and GPIO_AVAILABLE:
            time.sleep(0.001)  # Aguarda transmissão terminar
            GPIO.output(self.de_re_pin, GPIO.LOW)

    def _send_modbus_command(self, slave_id: int, function_code: int,
                             start_address: int, data: int) -> bytes:
        """
        Envia comando MODBUS RTU e retorna resposta.

        Args:
            slave_id: ID do dispositivo (1-247)
            function_code: Código da função MODBUS (0x03=ler, 0x06=escrever)
            start_address: Endereço inicial do registrador
            data: Dados (quantidade de registros para leitura, valor para escrita)

        Returns:
            Resposta do dispositivo (sem CRC) ou bytes vazios em caso de erro
        """
        if self.simulated or not self.serial:
            return b''

        # Monta frame MODBUS RTU
        frame = struct.pack('>BBHH', slave_id, function_code, start_address, data)
        frame += calculate_crc16(frame)

        try:
            # Limpa buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

            # Transmite
            self._set_transmit_mode()
            self.serial.write(frame)
            self.serial.flush()  # Aguarda transmissão completa

            # Muda para recepção
            self._set_receive_mode()

            # Aguarda e lê resposta
            time.sleep(0.05)  # Tempo para dispositivo responder

            if self.serial.in_waiting > 0:
                response = self.serial.read(self.serial.in_waiting)

                # Valida resposta (mínimo 5 bytes: id + func + data + crc)
                if len(response) >= 5:
                    # Verifica CRC
                    received_crc = response[-2:]
                    calculated_crc = calculate_crc16(response[:-2])

                    if received_crc == calculated_crc:
                        return response[:-2]  # Retorna sem CRC
                    else:
                        logger.warning(f"CRC inválido na resposta do atuador {slave_id}")

            return b''

        except serial.SerialException as e:
            logger.error(f"Erro de comunicação serial: {e}")
            return b''

    def set_position(self, actuator_id: int, position: int):
        """
        Define a posição do atuador.

        Args:
            actuator_id: ID MODBUS do atuador (1-247)
            position: Posição desejada (0-4095)
        """
        # Limita posição ao range válido
        position = max(0, min(4095, int(position)))

        if self.simulated:
            logger.info(f"[SIMULAÇÃO] Atuador {actuator_id} -> posição {position}")
            return

        if not self.serial or not self.serial.is_open:
            logger.error("Porta serial não conectada")
            return

        logger.info(f"Enviando posição {position} para atuador {actuator_id}")

        # Função 0x06 = Write Single Register
        response = self._send_modbus_command(
            slave_id=actuator_id,
            function_code=0x06,
            start_address=ADDR_GOAL_POSITION,
            data=position
        )

        if response:
            logger.debug(f"Resposta recebida: {response.hex()}")
        else:
            logger.warning(f"Sem resposta do atuador {actuator_id}")

    def get_position(self, actuator_id: int) -> int:
        """
        Lê a posição atual do atuador.

        Args:
            actuator_id: ID MODBUS do atuador (1-247)

        Returns:
            Posição atual (0-4095) ou 0 em caso de erro
        """
        if self.simulated:
            logger.info(f"[SIMULAÇÃO] Lendo posição do atuador {actuator_id}")
            return 0

        if not self.serial or not self.serial.is_open:
            logger.error("Porta serial não conectada")
            return 0

        # Função 0x03 = Read Holding Registers
        response = self._send_modbus_command(
            slave_id=actuator_id,
            function_code=0x03,
            start_address=ADDR_PRESENT_POSITION,
            data=1  # Quantidade de registros
        )

        if len(response) >= 5:
            # Resposta: slave_id + func + byte_count + data (2 bytes)
            position = struct.unpack('>H', response[3:5])[0]
            logger.debug(f"Posição atual do atuador {actuator_id}: {position}")
            return position

        logger.warning(f"Falha ao ler posição do atuador {actuator_id}")
        return 0


# Instância global para uso pelo sistema
_driver_instance = None

def get_driver(simulated=None) -> MightyZapDriver:
    """
    Retorna instância singleton do driver.

    Args:
        simulated: Força modo simulado (None = detecta automaticamente)
    """
    global _driver_instance

    if _driver_instance is None:
        # Auto-detecta se deve simular
        if simulated is None:
            simulated = not GPIO_AVAILABLE

        _driver_instance = MightyZapDriver(simulated=simulated)
        _driver_instance.connect()

    return _driver_instance
