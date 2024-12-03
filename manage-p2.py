#!/usr/bin/env python

from lib_vm import VM, NET  # Clases personalizadas para gestionar VMs y redes
import logging, sys, os, json  # Módulos estándar
import subprocess  # Para ejecutar comandos del sistema
from lxml import etree  # Para manipulación de XML

# Configuración inicial del logger
logging.basicConfig(level=logging.DEBUG)  # Nivel de registro en modo DEBUG
logger = logging.getLogger('manage-p2')  # Logger principal del script

# Funciones auxiliares
def init_log():
    """
    Configura un logger adicional para capturar y formatear mensajes de registro.
    """
    logging.basicConfig(level=logging.DEBUG)  # Configura el nivel de depuración
    log = logging.getLogger('auto_p2')
    ch = logging.StreamHandler(sys.stdout)  # Redirige mensajes al estándar de salida
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)  # Define el formato del mensaje
    log.addHandler(ch)
    log.propagate = False  # Evita que los mensajes se dupliquen

def pause():
    """
    Pausa la ejecución del script hasta que el usuario presione Enter.
    """
    programPause = input("-- Press <ENTER> to continue...")

# Leer configuración desde el archivo JSON
with open('manage-p2.json', 'r') as json_file:
    json_data = json.load(json_file)

number_of_servers = json_data['number_of_servers']  # Número de servidores definidos en el JSON
debug = json_data['debug']  # Modo de depuración definido en el JSON

# Validar el rango del número de servidores
if (number_of_servers > 5 or number_of_servers < 1):
    print("El número de servidores debe ser de 1 a 5")
    sys.exit()

# Ajustar el nivel de depuración según el archivo JSON
if debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Función para crear el escenario de VMs y redes
def create(number_of_servers):
    """
    Configura el entorno necesario para las máquinas virtuales.
    """
    try:
        logger.info("Ejecutando prepare-vnx-debian...")
        subprocess.call(["/lab/cnvr/bin/prepare-vnx-debian"])
        logger.info("Entorno preparado correctamente.")
    except Exception as e:
        logger.error(f"Error al preparar el entorno: {e}")
        sys.exit(1)


    """
    Crea el escenario incluyendo las máquinas virtuales y las redes.
    """
    image = "./cdps-vm-base-pc1.qcow2"  # Ruta de la imagen base
    number_of_servers = int(number_of_servers)  # Convertir a entero

    # Configuración del cliente c1
    interfaces_c1 = [{"addr": "10.1.1.2", "mask": "255.255.255.0"}]
    c1 = VM("c1")
    c1.create_vm(image, interfaces_c1)

    # Configuración del balanceador lb
    interfaces_lb = [
        {"addr": "10.1.1.1", "mask": "255.255.255.0"},
        {"addr": "10.1.2.1", "mask": "255.255.255.0"}
    ]
    lb = VM("lb")
    lb.create_vm(image, interfaces_lb)

    # Configuración de servidores s1, s2, ..., sN
    for n in range(0, number_of_servers):
        server_name = f"s{n+1}"  # Genera nombres s1, s2, ...
        interfaces_server = [{"addr": f"10.1.2.1{n+1}", "mask": "255.255.255.0"}]
        server = VM(server_name)
        server.create_vm(image, interfaces_server)

    # Crear las redes LAN1 y LAN2
    LAN1 = NET("LAN1")
    LAN1.create_net()
    LAN2 = NET("LAN2")
    LAN2.create_net()

    # Configurar las redes
    subprocess.call(["sudo", "ifconfig", "LAN1", "10.1.1.3/24"])  # Asignar IP a LAN1
    subprocess.call(["sudo", "ip", "route", "add", "10.1.0.0/16", "via", "10.1.1.1"])  # Ruta para el tráfico

    logger.debug("Red creada correctamente")

# Función para arrancar las VMs
def start(vm):
    """
    Arranca las VMs especificadas o todas si no se pasa un nombre concreto.
    """
    if vm == "all":  # Arranca todas las VMs
        c1 = VM('c1')
        c1.start_vm()
        lb = VM('lb')
        lb.start_vm()

        for n in range(0, number_of_servers):
          VM(f"s{n+1}").start_vm()
        logger.debug("Todas las VMs arrancadas correctamente")
    else:
        VM(vm).start_vm()
        logger.debug(f"VM: {server} arrancada")

# Función para detener las VMs
def stop(vm):
    """
    Detiene las VMs especificadas o todas si no se pasa un nombre concreto.
    """
    if vm == "all":  # Detiene todas las VMs
        c1 = VM('c1')
        c1.stop_vm()
        lb = VM('lb')
        lb.stop_vm()

        for n in range(0, number_of_servers):
            vm = f"s{n+1}"
            VM(vm).stop_vm()
        logger.debug("VMs paradas correctamente")
    else:
        VM(vm).stop_vm()
        logger.debug(f"VM: {vm} parada correctamente")

# Función para destruir el escenario
def destroy():
    """
    Libera las máquinas virtuales y elimina las redes.
    """
    c1 = VM('c1')
    c1.destroy_vm()
    lb = VM('lb')
    lb.destroy_vm()

    for n in range(0, number_of_servers):
        server_name = f"s{n+1}"
        server = VM(server_name)
        server.destroy_vm()

    LAN1 = NET("LAN1")
    LAN1.destroy_net()
    LAN2 = NET("LAN2")
    LAN2.destroy_net()

    logger.debug("Red destruida correctamente...")

# Función para monitorizar el escenario
def monitor():
    """
    Muestra el estado de todas las máquinas virtuales.
    """
    logger.info("Monitoreando el estado del escenario...")
    try:
        subprocess.call(["sudo", "virsh", "list", "--all"])  # Lista todas las VMs
        for vm_name in ["c1", "lb"] + [f"s{i}" for i in range(1, number_of_servers + 1)]:
            logger.info(f"Estado de: {vm_name}")
            subprocess.call(["sudo", "virsh", "dominfo", vm_name])  # Información detallada de cada VM
    except Exception as e:
        logger.error(f"Error monitoreando el escensario: {e}")

# Código principal que gestiona los argumentos de línea de comandos
arguments = sys.argv
if len(arguments) == 2:
    if arguments[1] == "create":
        create(number_of_servers)
    elif arguments[1] == "start":
        start("all")
    elif arguments[1] == "stop":
        stop("all")
    elif arguments[1] == "destroy":
        destroy()
    elif arguments[1] == "monitor":
        monitor()

if len(arguments) == 3:
    if arguments[1] == "create":
        for vm in arguments[2:]:
            create(vm)
    elif arguments[1] == "start":
        for vm in arguments[2:]:
            start(vm)
    elif arguments[1] == "stop":
        for vm in arguments[2:]:
            stop(vm)

