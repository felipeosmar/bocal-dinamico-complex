# Diagrama de Conexão de Hardware

Este documento ilustra a interconexão dos componentes eletrônicos do sistema **Bocal Dinâmico**.

## Topologia do Sistema

O sistema é centrado em um **Raspberry Pi 4**, que atua como controlador principal. Ele se comunica com:
1.  **3x Atuadores Mighty Zap** via protocolo **Modbus RTU** sobre barramento **RS-485**.
2.  **1x Profilômetro** via comunicação Serial (geralmente RS-232 convertido para USB).

### Diagrama Funcional (Mermaid)

```mermaid

flowchart TB

```

## Detalhes das Conexões

### 1. Barramento RS-485 (Atuadores)
*   **Adaptador**: USB para RS-485.
*   **Fios**:
    *   **Data+ (A)**: Conecta ao pino Data+ de todos os atuadores.
    *   **Data- (B)**: Conecta ao pino Data- de todos os atuadores.
    *   **GND**: Comum entre a fonte dos atuadores e o adaptador (recomendado).
*   **Configuração Serial**:
    *   Baudrate: `57600` (Padrão do driver)
    *   Data bits: `8`
    *   Parity: `None`
    *   Stop bits: `1`

### 2. Alimentação
*   **Atuadores Mighty Zap**: Requerem alimentação externa robusta (verificar voltagem nominal, geralmente 12V). **NÃO** alimentar diretamente pelos pinos 5V do Raspberry Pi.
*   **Raspberry Pi**: Fonte dedicada USB-C 5V 3A.

### 3. Profilômetro
*   Conectado tipicamente via USB direto ou adaptador Serial-USB.
*   Verifique o dispositivo correto com `ls /dev/tty*` (ex: `/dev/ttyACM0` ou `/dev/ttyUSB1`).

---

## Alternativa: Conexão via GPIO (Sem USB)

É possível comunicar diretamente via pinos GPIO (UART) usando um módulo **Transceptor TTL-RS485** (ex: Chip MAX3485 ou MAX485).

> **⚠️ CUIDADO: Níveis de Tensão (3.3V vs 5V)**
> *   O Raspberry Pi opera com lógica **3.3V**.
> *   O chip **MAX485** (comum) opera a **5V**. Ligar o pino de saída do MAX485 direto no RX do Pi pode **queimar a porta GPIO**.
> *   **Recomendação**: Use um chip **MAX3485** (nativo 3.3V) ou utilize um **Conversor de Nível Lógico (Logic Level Shifter)** entre o módulo 5V e o Raspberry Pi.

### Diagrama GPIO (Modo UART)

```mermaid
graph TD
    classDef gpio fill:#eebb99,stroke:#333,stroke-width:2px;
    classDef shifter fill:#ddd,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5;
    
    subgraph RPI_GPIO [Raspberry Pi Header]
        TX[GPIO 14 / TXD]:::gpio
        RX[GPIO 15 / RXD]:::gpio
        CTRL[GPIO 18 / RTS]:::gpio
        GND_PI[Ground]:::gpio
        V33[3.3V Power]:::gpio
    end

    subgraph Level_Shifter [Conversor de Nível (Se usar MAX485 5V)]
        LV_HV[3.3V <--> 5V]:::shifter
    end

    subgraph RS485_Module [Módulo MAX485 / MAX3485]
        DI[DI - Driver Input]
        RO[RO - Receiver Output]
        DE_RE[DE/RE - Direction Ctrl]
        A[A+]
        B[B-]
        VCC_MOD[VCC]
        GND_MOD[GND]
    end

    %% Wiring
    TX --> LV_HV --> DI
    RX <-- LV_HV <-- RO
    CTRL --> LV_HV --> DE_RE
    
    GND_PI -- Comum --> GND_MOD
    
    %% Actuators connection
    A --> BusA[Barramento A+]
    B --> BusB[Barramento B-]
```

### Pinagem Típica
| Função | Pino RPi (Board) | Módulo RS485 | Obs |
| :--- | :--- | :--- | :--- |
| **TX** | GPIO 14 (Pin 8) | **DI** | Envia dados para o barramento |
| **RX** | GPIO 15 (Pin 10) | **RO** | Recebe dados do barramento |
| **Controle** | GPIO 18 (Pin 12) | **DE** & **RE** | Jumper entre DE e RE. HIGH=Tx, LOW=Rx. |
| **GND** | Ground (Pin 6) | **GND** | Referência comum obrigatória |
| **VCC** | 3.3V (Pin 1) | **VCC** | Se módulo for MAX3485 (3.3V) |

*Nota: Para controle automático do pino DE/RE, recomenda-se habilitar o overlay `rts-gpio` no config.txt do Raspberry Pi.*
