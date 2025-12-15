#!/usr/bin/env python3
"""
Programa de teste para comunicação RS485 com atuadores MightyZAP
via MAX485 no Raspberry Pi 4.

Configuração de pinos:
    MAX485 Pin    Raspberry Pi Pin    Function
    VCC           5V (Pin 2)          Power Supply
    GND           GND (Pin 6)         Ground
    RO            GPIO15 (Pin 10)     RS485 Data Receive (RX)
    DI            GPIO14 (Pin 8)      RS485 Data Transmit (TX)
    RE            GPIO18 (Pin 12)     Receive Enable (LOW to receive)
    DE            GPIO18 (Pin 12)     Driver Enable (HIGH to send)

Atuadores conectados:
    - Atuador 1: ID MODBUS = 1
    - Atuador 2: ID MODBUS = 2
"""

import time
import struct
import sys

# Configuração de pinos
DE_RE_PIN = 18  # GPIO18 (BCM) - controla DE e RE do MAX485

# Configuração serial
SERIAL_PORT = '/dev/serial0'  # UART principal do Raspberry Pi
BAUDRATE = 57600

# IDs dos atuadores
ACTUATOR_1_ID = 1
ACTUATOR_2_ID = 2

# Endereços MODBUS MightyZAP (conforme manual FC_MODBUS)
ADDR_GOAL_POSITION = 0x001E       # Goal Position (R/W) - 2 bytes
ADDR_PRESENT_POSITION = 0x0020   # Present Position (R) - 2 bytes
ADDR_PRESENT_CURRENT = 0x0024    # Present Current (R) - 2 bytes
ADDR_MOVING_SPEED = 0x0020       # Moving Speed
ADDR_ID = 0x0007                 # Servo ID

# Tenta importar bibliotecas necessárias
try:
    import serial
except ImportError:
    print("ERRO: Biblioteca 'pyserial' não instalada.")
    print("Execute: pip install pyserial")
    sys.exit(1)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("AVISO: RPi.GPIO não disponível - executando em modo simulado")
    GPIO_AVAILABLE = False


def calculate_crc16(data: bytes) -> bytes:
    """Calcula CRC16 MODBUS (Polynomial: 0xA001)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)  # Little-endian


class RS485Controller:
    """Controlador RS485 via MAX485 para atuadores MightyZAP."""

    def __init__(self, port=SERIAL_PORT, baudrate=BAUDRATE, de_re_pin=DE_RE_PIN):
        self.port = port
        self.baudrate = baudrate
        self.de_re_pin = de_re_pin
        self.serial = None
        self.gpio_initialized = False

    def setup(self) -> bool:
        """Configura GPIO e porta serial."""
        print(f"\n{'='*60}")
        print("CONFIGURANDO COMUNICAÇÃO RS485")
        print(f"{'='*60}")

        # Configura GPIO
        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self.de_re_pin, GPIO.OUT)
                GPIO.output(self.de_re_pin, GPIO.LOW)  # Inicia em modo recepção
                self.gpio_initialized = True
                print(f"[OK] GPIO {self.de_re_pin} configurado (DE/RE control)")
            except Exception as e:
                print(f"[ERRO] Falha ao configurar GPIO: {e}")
                return False
        else:
            print("[AVISO] GPIO não disponível - modo simulado")

        # Configura serial
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5
            )
            print(f"[OK] Porta serial {self.port} aberta @ {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"[ERRO] Falha ao abrir porta serial: {e}")
            print("\nVerifique:")
            print("  1. A UART está habilitada no raspi-config?")
            print("  2. O console serial está desabilitado?")
            print("  3. O usuário tem permissão? (sudo usermod -a -G dialout $USER)")
            return False

    def cleanup(self):
        """Libera recursos."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("[OK] Porta serial fechada")

        if self.gpio_initialized and GPIO_AVAILABLE:
            GPIO.cleanup(self.de_re_pin)
            print("[OK] GPIO liberado")

    def set_transmit_mode(self):
        """MAX485 em modo transmissão (DE=HIGH, RE=HIGH)."""
        if self.gpio_initialized:
            GPIO.output(self.de_re_pin, GPIO.HIGH)
            time.sleep(0.001)

    def set_receive_mode(self):
        """MAX485 em modo recepção (DE=LOW, RE=LOW)."""
        if self.gpio_initialized:
            time.sleep(0.002)  # Aguarda transmissão completar
            GPIO.output(self.de_re_pin, GPIO.LOW)

    def send_modbus(self, slave_id: int, function_code: int,
                    address: int, data: int) -> bytes:
        """
        Envia comando MODBUS RTU e retorna resposta.

        Args:
            slave_id: ID do escravo (1-247)
            function_code: Código da função (0x03=ler, 0x06=escrever)
            address: Endereço do registrador
            data: Valor para escrita ou quantidade de registros para leitura

        Returns:
            Resposta sem CRC ou bytes vazios em caso de erro
        """
        if not self.serial or not self.serial.is_open:
            print("[ERRO] Porta serial não está aberta")
            return b''

        # Monta frame MODBUS RTU
        frame = struct.pack('>BBHH', slave_id, function_code, address, data)
        crc = calculate_crc16(frame)
        frame += crc

        try:
            # Limpa buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

            # Transmite
            self.set_transmit_mode()
            self.serial.write(frame)
            self.serial.flush()

            # Muda para recepção
            self.set_receive_mode()

            # Aguarda resposta
            time.sleep(0.05)

            if self.serial.in_waiting > 0:
                response = self.serial.read(self.serial.in_waiting)

                if len(response) >= 5:
                    # Verifica CRC
                    received_crc = response[-2:]
                    calculated_crc = calculate_crc16(response[:-2])

                    if received_crc == calculated_crc:
                        return response[:-2]
                    else:
                        print(f"  [AVISO] CRC inválido")

            return b''

        except Exception as e:
            print(f"  [ERRO] {e}")
            return b''

    def read_position(self, actuator_id: int) -> int:
        """Lê posição atual do atuador."""
        response = self.send_modbus(
            slave_id=actuator_id,
            function_code=0x03,  # Read Holding Registers
            address=ADDR_PRESENT_POSITION,
            data=1  # 1 registrador
        )

        if len(response) >= 5:
            # Resposta: ID + Func + ByteCount + Data(2 bytes)
            position = struct.unpack('>H', response[3:5])[0]
            return position
        return -1

    def write_position(self, actuator_id: int, position: int) -> bool:
        """Escreve posição desejada no atuador."""
        position = max(0, min(4095, int(position)))

        response = self.send_modbus(
            slave_id=actuator_id,
            function_code=0x06,  # Write Single Register
            address=ADDR_GOAL_POSITION,
            data=position
        )

        return len(response) > 0


def test_communication(controller: RS485Controller, actuator_id: int) -> bool:
    """Testa comunicação com um atuador."""
    print(f"\n  Testando atuador ID {actuator_id}...")

    # Tenta ler posição atual
    position = controller.read_position(actuator_id)

    if position >= 0:
        print(f"  [OK] Atuador {actuator_id} respondeu - Posição atual: {position}")
        return True
    else:
        print(f"  [FALHA] Atuador {actuator_id} não respondeu")
        return False


def test_movement(controller: RS485Controller, actuator_id: int):
    """Testa movimento do atuador."""
    print(f"\n  Testando movimento do atuador {actuator_id}...")

    # Lê posição inicial
    initial_pos = controller.read_position(actuator_id)
    if initial_pos < 0:
        print("  [ERRO] Não foi possível ler posição inicial")
        return

    print(f"  Posição inicial: {initial_pos}")

    # Define posições de teste
    test_positions = [1000, 2000, 3000, initial_pos]

    for target in test_positions:
        print(f"  Movendo para posição {target}...", end=" ")

        if controller.write_position(actuator_id, target):
            time.sleep(1.5)  # Aguarda movimento

            current = controller.read_position(actuator_id)
            if current >= 0:
                error = abs(current - target)
                if error < 50:  # Tolerância de 50 unidades
                    print(f"[OK] Chegou em {current}")
                else:
                    print(f"[AVISO] Posição atual: {current} (erro: {error})")
            else:
                print("[ERRO] Falha ao ler posição")
        else:
            print("[ERRO] Falha ao enviar comando")


def run_tests():
    """Executa bateria de testes."""
    print("\n" + "="*60)
    print("TESTE DE COMUNICAÇÃO RS485 - ATUADORES MIGHTYZAP")
    print("="*60)
    print(f"\nConfiguração:")
    print(f"  - Porta serial: {SERIAL_PORT}")
    print(f"  - Baudrate: {BAUDRATE}")
    print(f"  - Pino DE/RE: GPIO{DE_RE_PIN}")
    print(f"  - Atuadores: ID {ACTUATOR_1_ID} e ID {ACTUATOR_2_ID}")

    controller = RS485Controller()

    if not controller.setup():
        print("\n[ERRO] Falha na configuração. Abortando.")
        return

    try:
        # Teste 1: Comunicação básica
        print(f"\n{'='*60}")
        print("TESTE 1: COMUNICAÇÃO BÁSICA")
        print(f"{'='*60}")

        actuator1_ok = test_communication(controller, ACTUATOR_1_ID)
        actuator2_ok = test_communication(controller, ACTUATOR_2_ID)

        if not actuator1_ok and not actuator2_ok:
            print("\n[ERRO] Nenhum atuador respondeu!")
            print("\nVerifique:")
            print("  1. Conexões A/B do RS485")
            print("  2. Alimentação dos atuadores")
            print("  3. IDs MODBUS dos atuadores")
            print("  4. Terminação de linha (resistor 120 ohm)")
            return

        # Teste 2: Leitura de posições
        print(f"\n{'='*60}")
        print("TESTE 2: LEITURA DE POSIÇÕES")
        print(f"{'='*60}")

        for actuator_id in [ACTUATOR_1_ID, ACTUATOR_2_ID]:
            pos = controller.read_position(actuator_id)
            if pos >= 0:
                print(f"  Atuador {actuator_id}: posição = {pos}")
            else:
                print(f"  Atuador {actuator_id}: sem resposta")

        # Teste 3: Movimento (opcional)
        print(f"\n{'='*60}")
        print("TESTE 3: TESTE DE MOVIMENTO")
        print(f"{'='*60}")

        response = input("\nDeseja testar movimentação? (s/N): ").strip().lower()

        if response == 's':
            if actuator1_ok:
                test_movement(controller, ACTUATOR_1_ID)
            if actuator2_ok:
                test_movement(controller, ACTUATOR_2_ID)
        else:
            print("  Teste de movimento ignorado.")

        # Resumo
        print(f"\n{'='*60}")
        print("RESUMO DOS TESTES")
        print(f"{'='*60}")
        print(f"  Atuador 1 (ID {ACTUATOR_1_ID}): {'OK' if actuator1_ok else 'FALHA'}")
        print(f"  Atuador 2 (ID {ACTUATOR_2_ID}): {'OK' if actuator2_ok else 'FALHA'}")

    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário.")

    finally:
        controller.cleanup()
        print("\nTeste finalizado.")


def interactive_mode():
    """Modo interativo para comandos manuais."""
    print("\n" + "="*60)
    print("MODO INTERATIVO - CONTROLE DOS ATUADORES")
    print("="*60)

    controller = RS485Controller()

    if not controller.setup():
        return

    print("\nComandos disponíveis:")
    print("  r <id>          - Ler posição do atuador")
    print("  w <id> <pos>    - Mover atuador para posição (0-4095)")
    print("  scan            - Escanear atuadores (ID 1-10)")
    print("  q               - Sair")

    try:
        while True:
            cmd = input("\n> ").strip().lower().split()

            if not cmd:
                continue

            if cmd[0] == 'q':
                break

            elif cmd[0] == 'r' and len(cmd) >= 2:
                actuator_id = int(cmd[1])
                pos = controller.read_position(actuator_id)
                if pos >= 0:
                    print(f"Posição do atuador {actuator_id}: {pos}")
                else:
                    print(f"Atuador {actuator_id} não respondeu")

            elif cmd[0] == 'w' and len(cmd) >= 3:
                actuator_id = int(cmd[1])
                position = int(cmd[2])
                if controller.write_position(actuator_id, position):
                    print(f"Comando enviado: atuador {actuator_id} -> {position}")
                else:
                    print("Falha ao enviar comando")

            elif cmd[0] == 'scan':
                print("Escaneando IDs 1-10...")
                for i in range(1, 11):
                    pos = controller.read_position(i)
                    if pos >= 0:
                        print(f"  ID {i}: ENCONTRADO (pos={pos})")
                    time.sleep(0.1)

            else:
                print("Comando inválido")

    except KeyboardInterrupt:
        pass

    finally:
        controller.cleanup()


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("#  PROGRAMA DE TESTE - RS485 MIGHTYZAP")
    print("#"*60)

    if len(sys.argv) > 1 and sys.argv[1] == '-i':
        interactive_mode()
    else:
        run_tests()
