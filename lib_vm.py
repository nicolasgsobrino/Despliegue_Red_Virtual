import logging, os
import subprocess  # Para ejecutar comandos del sistema operativo
from lxml import etree  # Para manipular ficheros XML

# Configuración del logger
log = logging.getLogger('manage-p2')

# Definición de servidores
servidores = ["s1", "s2", "s3", "s4", "s5"]  # Lista de servidores disponibles

# Configuración de los puentes de red
bridges = {
    "c1": ["LAN1"],  # Cliente conectado a LAN1
    "lb": ["LAN1"],  # Balanceador conectado a LAN1 y LAN2
    "s1": ["LAN2"],  # Servidores conectados a LAN2
    "s2": ["LAN2"],
    "s3": ["LAN2"],
    "s4": ["LAN2"],
    "s5": ["LAN2"]
}

# Configuración de interfaces de red para las VMs
interfaces_red = {
    "c1": ["10.1.1.2", "10.1.1.1"],  # Cliente con dirección IP y gateway
    "s1": ["10.1.2.11", "10.1.2.1"],  # Servidores con direcciones IP consecutivas
    "s2": ["10.1.2.12", "10.1.2.1"],
    "s3": ["10.1.2.13", "10.1.2.1"],
    "s4": ["10.1.2.14", "10.1.2.1"],
    "s5": ["10.1.2.15", "10.1.2.1"]
}

# Función para editar el fichero XML de una máquina virtual
def editar_xml(vm):
    """
    Modifica el fichero XML de configuración de una VM, ajustando:
    - Nombre de la máquina virtual.
    - Fuente del archivo de disco.
    - Configuración de interfaces de red.
    """
    cwd = os.getcwd()  # Obtener el directorio actual
    path = cwd + "/" + vm  # Ruta al fichero XML

    tree = etree.parse(path + ".xml")  # Cargar el fichero XML
    root = tree.getroot()  # Obtener el nodo raíz

    # Modificar el nombre de la máquina
    name = root.find("name")
    name.text = vm

    # Configurar el archivo de disco
    root.find("./devices/disk/source").set("file", path + ".qcow2")

    # Configurar la primera interfaz de red
    interface = root.find("./devices/interface")
    interface.set("type", "bridge")
    source = interface.find("source")
    source.set("bridge", bridges[vm][0])

    # Añadir soporte para openvswitch
    virtualport = etree.SubElement(interface, "virtualport")
    virtualport.set("type", "openvswitch")

    # Si la vm es lb añadimos la interfaz de LAN2.
    if vm == "lb":
        interfaz2 = etree.Element("interface", type="bridge")
        source2 = etree.SubElement(interfaz2, "source")
        source2.set("bridge", "LAN2")

        model2 = etree.SubElement(interfaz2, "model")
        model2.set("type", "virtio")

        virtualport2 = etree.SubElement(interfaz2, "virtualport")
        virtualport2.set("type", "openvswitch")
        root.find("./devices").append(interfaz2)  # Añadir la nueva interfaz al XML

    # Guardar los cambios en el fichero XML
    with open(path + ".xml", "wb") as fout:
        fout.write(etree.tostring(tree, pretty_print=True, encoding="utf-8"))

# Clase para gestionar máquinas virtuales
class VM:
    
    def __init__(self, name):
        self.name = name
        log.debug('init VM ' + self.name)

    def create_vm(self, image, interfaces):
        log.debug("create_vm " + self.name + " (image: " + image + ")")
        subprocess.call(["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", image, self.name + ".qcow2"])
        subprocess.call(["cp", "plantilla-vm-pc1.xml", self.name + ".xml"])
        editar_xml(self.name)
        subprocess.call(["sudo", "virsh", "define", self.name + ".xml"])
      
        cwd = os.getcwd()
        path = cwd + "/" + self.name 

        # Configurar el archivo /etc/hostname
        # with open("hostname", 'w') as fout:
        fout = open("hostname", 'w')
        fout.write(self.name + "\n")
        fout.close()
        subprocess.call(["sudo", "virt-copy-in", "-a", self.name + ".qcow2", "hostname", "/etc"])
            # subprocess.call(["sudo virt-edit -a" +self.name + ".qcow2", "hostname", "/etc"])

        # os.remove("hostname")

        # Configurar el archivo /etc/hosts
        subprocess.call("sudo virt-edit -a " + self.name + ".qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1 " + self.name + "/'", shell=True)

        # Configurar el archivo /etc/network/interfaces
        fout = open("interfaces", 'w')
        if self.name == "lb":
            fout.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet static\n  address 10.1.1.1\n  netmask 255.255.255.0\n  gateway 10.1.1.1\nauto eth1\niface eth1 inet static\n  address 10.1.2.1\n  netmask 255.255.255.0\n  gateway 10.1.2.1")
            
        else:
            fout.write("auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\n  address " + interfaces_red[self.name][0] + "\n  netmask 255.255.255.0\n  gateway " + interfaces_red[self.name][1]+ "\n")
            
        fout.close()
        subprocess.call(["sudo", "virt-copy-in", "-a", self.name + ".qcow2", "interfaces", "/etc/network"])
        # os.remove("interfaces")

        # Configurar el balanceador como router
        if self.name == "lb":
            subprocess.call("sudo virt-edit -a lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'", shell=True)

    def start_vm(self):
        log.debug("start_vm " + self.name)
        subprocess.call(["sudo", "virsh", "start", self.name])
        os.system("xterm -e 'sudo virsh console " + self.name + "'&")

    def stop_vm(self):
        log.debug("stop_vm " + self.name)
        subprocess.call(["sudo", "virsh", "shutdown", self.name])

    def destroy_vm(self):
        subprocess.call(["sudo", "virsh", "destroy", self.name])
        subprocess.call(["sudo", "virsh", "undefine", self.name])
        subprocess.call(["rm", "-f", self.name+".qcow2"])
        subprocess.call(["rm", "-f", self.name+".xml"])
       

# Clase para gestionar redes virtuales
class NET:

    def __init__(self, name):
        self.name = name
        log.debug('init net ' + self.name)

    def create_net(self):
        log.debug('create_net ' + self.name)
        subprocess.call(["sudo", "ovs-vsctl", "add-br", self.name])
        subprocess.call(["sudo", "ifconfig", self.name, "up"])

    def destroy_net(self):
        log.debug('destroy_net ' + self.name)
        subprocess.call(["sudo", "ifconfig", self.name, "down"])
        subprocess.call(["sudo", "ovs-vsctl", "del-br",self.name])
