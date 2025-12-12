# Conexão RS485 - Raspberry Pi 4 com Módulo MAX485

Este documento descreve como conectar o módulo RS485 (MAX485) ao Raspberry Pi 4 para comunicação com os atuadores MightyZap.

## Componentes

- Raspberry Pi 4
- Módulo RS485 para Arduino (chip MAX485)
- Resistores: 1kΩ e 2kΩ (ou 3x 1kΩ)
- Atuadores MightyZap

## Diagrama de Conexão

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RASPBERRY PI 4                                    │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  Pino 1  [3.3V]                                                 │       │
│   │  Pino 2  [5V]  ─────────────────────────► VCC do módulo         │       │
│   │  Pino 6  [GND] ─────────────────────────► GND do módulo         │       │
│   │  Pino 8  [TX/GPIO14] ───────────────────► DI  (Driver Input)    │       │
│   │  Pino 10 [RX/GPIO15] ◄── DIVISOR ◄──────  RO  (Receiver Output) │       │
│   │  Pino 12 [GPIO18] ──────────────────────► DE + RE (jumpeados)   │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Pinagem Detalhada

| Raspberry Pi 4   | Pino Físico | Módulo RS485 | Observação                    |
|------------------|-------------|--------------|-------------------------------|
| 5V               | 2           | VCC          | Alimentação do módulo         |
| GND              | 6           | GND          | Terra comum                   |
| TX (GPIO 14)     | 8           | DI           | Dados Pi → Módulo             |
| RX (GPIO 15)     | 10          | RO           | **Via divisor de tensão!**    |
| GPIO 18          | 12          | DE + RE      | Controle de direção TX/RX     |

## IMPORTANTE: Divisor de Tensão no RO

O MAX485 é um chip de **5V**. O Raspberry Pi usa **3.3V** nos GPIOs.

**Conectar RO direto no GPIO 15 pode DANIFICAR o Raspberry Pi!**

### Circuito do Divisor de Tensão

```
    MÓDULO MAX485                                    RASPBERRY PI
    ┌───────────┐
    │           │
    │   RO ─────┼────┬────[1kΩ]────┬────[2kΩ]────► GND (Pino 6)
    │           │    │             │
    │           │    │             └──────────────► GPIO 15 (Pino 10)
    │           │    │
    └───────────┘    │
                     │
              (5V saindo do RO)

    Cálculo: Vout = 5V × (2kΩ / 3kΩ) = 3.33V ✓
```

### Alternativa com 3 resistores de 1kΩ

Se você só tem resistores de 1kΩ:

```
    RO ────[1kΩ]────┬────[1kΩ]────[1kΩ]────► GND
                    │
                    └──────────────────────► GPIO 15
```

## Conexão DE/RE (Controle de Direção)

O pino GPIO 18 controla a direção da comunicação:

- **GPIO 18 = HIGH**: Modo transmissão (Pi envia dados)
- **GPIO 18 = LOW**: Modo recepção (Pi recebe dados)

**Importante**: Os pinos DE e RE do módulo devem estar **conectados juntos** (jumper ou solda).

```
    GPIO 18 ──────────┬──────► DE
                      │
                      └──────► RE
```

## Barramento RS485 → Atuadores MightyZap

```
    MÓDULO MAX485              ATUADOR MIGHTYZAP
    ┌───────────┐              ┌───────────────┐
    │           │              │               │
    │   A+ ─────┼──────────────┼─► A+ (Data+)  │
    │           │              │               │
    │   B- ─────┼──────────────┼─► B- (Data-)  │
    │           │              │               │
    │   GND ────┼──────────────┼─► GND         │
    │           │              │               │
    └───────────┘              └───────────────┘
```

**Nota**: O GND deve ser comum entre o Raspberry Pi, módulo RS485 e fonte de alimentação dos atuadores.

## Diagrama Completo

```
                                    FONTE 12V
                                        │
                                        ▼
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│ RASPBERRY PI │     │ MÓDULO MAX485│     │ ATUADOR MIGHTYZAP│
│              │     │              │     │                 │
│  5V (Pino 2)─┼────►│ VCC          │     │  12V ◄──────────┼─── +12V
│              │     │              │     │                 │
│ GND (Pino 6)─┼────►│ GND ─────────┼─────┼─► GND           │
│              │     │              │     │                 │
│  TX (Pino 8)─┼────►│ DI           │     │                 │
│              │     │              │     │                 │
│  RX (Pino10)◄┼─[R]─│ RO           │     │                 │
│              │     │              │     │                 │
│GPIO18(Pino12)┼────►│ DE ──┬── RE  │     │                 │
│              │     │      └──────►│     │                 │
│              │     │              │     │                 │
│              │     │ A+ ──────────┼────►│ A+ (Data+)      │
│              │     │              │     │                 │
│              │     │ B- ──────────┼────►│ B- (Data-)      │
│              │     │              │     │                 │
└──────────────┘     └──────────────┘     └─────────────────┘

[R] = Divisor de tensão (1kΩ + 2kΩ)
```

## Configuração do Raspberry Pi

### 1. Habilitar UART

```bash
sudo raspi-config
# Interface Options → Serial Port
# - Login shell over serial: NÃO
# - Serial port hardware enabled: SIM
```

Ou adicione ao `/boot/firmware/config.txt`:

```
enable_uart=1
```

### 2. Verificar porta serial

```bash
ls -la /dev/serial0
# Deve mostrar: /dev/serial0 -> ttyS0
```

### 3. Verificar permissões

O usuário deve estar no grupo `dialout`:

```bash
sudo usermod -a -G dialout $USER
# Faça logout e login novamente
```

## Parâmetros de Comunicação

| Parâmetro   | Valor   |
|-------------|---------|
| Porta       | /dev/serial0 |
| Baudrate    | 57600   |
| Data bits   | 8       |
| Paridade    | None    |
| Stop bits   | 1       |
| Protocolo   | MODBUS RTU |

## Teste de Comunicação

Após conectar tudo, execute o servidor Django:

```bash
cd /home/senai/work/bocal-dinamico-complex
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Acesse a aba de testes:

```
http://<IP_DO_RASPBERRY>:8000/actuator-test/
```

## Solução de Problemas

### Sem resposta do atuador

1. **Verificar alimentação**: Atuador precisa de 12V externa
2. **Verificar fiação A+/B-**: Podem estar invertidos
3. **Verificar ID MODBUS**: Padrão dos atuadores é 1, 2, 3
4. **Verificar baudrate**: MightyZap usa 57600 por padrão
5. **Verificar divisor de tensão**: RO não pode ir direto no GPIO

### LED do atuador

- **Vermelho**: Sem comunicação ou erro
- **Verde**: Comunicação OK
- **Pisca**: Recebendo comandos

### Comando de teste manual

```bash
# Envia posição 2000 para atuador ID 1
curl -X POST http://localhost:8000/api/set-position/ \
  -H "Content-Type: application/json" \
  -d '{"actuator_id": 1, "position": 2000}'
```

## Referências

- [Manual MODBUS MightyZap](docs/FC_MODBUS_mightyZAP-User-Manual_ENG_23H08_V3.4.pdf)
- [Pinout Raspberry Pi 4](docs/raspberry%20pi%204%20pinout.png)
- [Datasheet MAX485](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX1487-MAX491.pdf)
