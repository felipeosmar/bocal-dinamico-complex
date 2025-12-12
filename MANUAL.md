# Manual de Uso e Configuração - Raspberry Pi Actuator Control

Este documento descreve como configurar, instalar e operar o sistema de controle de atuadores no Raspberry Pi 4.

## 1. Pré-requisitos de Hardware
- **Raspberry Pi 4** (Recomendado 2GB RAM ou superior).
- **Atuadores MightyZAP (3x)**: Conectados via adaptador USB-RS485 ou Hat RS485 (Protocolo Modbus RTU).
- **Profilômetro**: Conectado via Serial/USB.
- **Cartão SD**: Com Raspberry Pi OS (Bullseye ou Bookworm) instalado.

> **Diagrama de Conexão**: Consulte [HARDWARE_DIAGRAM.md](./HARDWARE_DIAGRAM.md) para um diagrama visual detalhado das conexões.

## 2. Preparação do Raspberry Pi

### 2.1. Atualizar o Sistema
Abra o terminal e execute:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git libatlas-base-dev -y
```

### 2.2. Configurar Porta Serial (Se usar GPIO/Hat)
Se estiver usando um Hat RS485 conectado aos pinos GPIO (UART):
1. Execute `sudo raspi-config`.
2. Vá em **Interface Options** -> **Serial Port**.
3. **Login Shell over Serial?** -> **Não**.
4. **Serial Port Hardware enabled?** -> **Sim**.
5. Reinicie o Raspberry Pi: `sudo reboot`.
6. **(Avançado) Controle de Fluxo RTS**: Se estiver usando um módulo MAX485 manual e driver Modbus que exija hardware flow control (ou uso do `rpi-gpio` RTS), edite `/boot/config.txt` e adicione:
   ```ini
   enable_uart=1
   dtoverlay=uart-ctsrts,rts-gpio=18
   ```
   *Isso define o GPIO 18 como pino de controle de direção (RTS) automático pelo driver serial do Kernel.*

### 2.3. Permissões de Acesso
Adicione o usuário atual ao grupo `dialout` para acessar as portas USB/Serial sem `sudo`:
```bash
sudo usermod -a -G dialout $USER
```
*Faça logout e login novamente para aplicar.*

## 3. Instalação da Aplicação

1. **Clonar o Repositório** (ou copiar os arquivos):
   ```bash
   cd /home/pi/work
   # git clone <url-do-repositorio> bocal-dinamico-complex
   cd bocal-dinamico-complex
   ```

2. **Criar Ambiente Virtual**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instalar Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Banco de Dados**:
   ```bash
   python manage.py migrate
   python manage.py init_data
   ```
   *O comando `init_data` cria as configurações padrão e os 3 atuadores.*

## 4. Executando a Aplicação

### 4.1. Modo Desenvolvimento (Teste Manual)
Para testar, inicie o servidor:
```bash
python manage.py runserver 0.0.0.0:8000
```
- Acesse o dashboard em: `http://<IP-DO-RASPBERRY>:8000/`

**Importante**: Em outro terminal, mantenha o loop de controle rodando se quiser que o sistema reaja automaticamente (na versão final, isso pode ser integrado, mas atualmente é um comando separado):
```bash
source .venv/bin/activate
python manage.py run_control
```

### 4.2. Modo Simulação
O sistema possui um modo de simulação para testes sem hardware conectado.
1. No Dashboard, vá até o card **Simulation Control**.
2. Ative a chave **Enable Simulation**.
3. Mova o slider **Simulated Value** para injetar valores de leitura do profilômetro.
4. Observe (no log do terminal `run_control`) que o sistema calcula o erro baseando-se no valor simulado.

## 5. Configuração de Produção (Auto-start)

Para que o sistema inicie automaticamente ao ligar o Raspberry Pi:

1. **Instale o Gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **Crie um serviço Systemd para o Web Server**:
   Crie o arquivo `/etc/systemd/system/bocal-web.service`:
   ```ini
   [Unit]
   Description=Bocal Web Interface
   After=network.target

   [Service]
   User=pi
   Group=pi
   WorkingDirectory=/home/pi/work/bocal-dinamico-complex
   ExecStart=/home/pi/work/bocal-dinamico-complex/.venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 core.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

3. **Crie um serviço para o Loop de Controle**:
   Crie o arquivo `/etc/systemd/system/bocal-control.service`:
   ```ini
   [Unit]
   Description=Bocal Control Loop
   After=network.target

   [Service]
   User=pi
   Group=pi
   WorkingDirectory=/home/pi/work/bocal-dinamico-complex
   ExecStart=/home/pi/work/bocal-dinamico-complex/.venv/bin/python manage.py run_control

   [Install]
   WantedBy=multi-user.target
   ```

4. **Ative os serviços**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bocal-web
   sudo systemctl enable bocal-control
   sudo systemctl start bocal-web
   sudo systemctl start bocal-control
   ```

## 6. Solução de Problemas

- **Erro de Permissão na Serial**: Verifique se o usuário está no grupo `dialout`.
- **Atuadores não respondem**: Verifique os IDs Modbus (padrão 1, 2, 3) e o Baudrate. O driver atual usa `/dev/ttyUSB0` (ajuste em `apps/hardware/services/mighty_zap.py` se necessário).
- **Dashboard não carrega**: Verifique se o serviço web está rodando (`sudo systemctl status bocal-web`).
