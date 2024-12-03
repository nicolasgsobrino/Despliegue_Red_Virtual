import logging, os
import subprocess 
from lxml import etree

log = logging.getLogger('manage-p2')

servidores = ["s1", "s2", "s3", "s4" ,"s5"]

bridges = {
          "c1":["LAN1"],
          "lb":["LAN1"],
          "s1":["LAN2"],
          "s2":["LAN2"],
          "s3":["LAN2"],
          "s4":["LAN2"],
          "s5":["LAN2"]
          }

network = {
          "c1":["10.1.1.2", "10.1.1.1"],
          "s1":["10.1.2.11", "10.1.2.1"],
          "s2":["10.1.2.12", "10.1.2.1"],
          "s3":["10.1.2.13", "10.1.2.1"],
          "s4":["10.1.2.14", "10.1.2.1"],
          "s5":["10.1.2.15", "10.1.2.1"]
          }


def editXml(vm):
    cwd = os.getcwd()
    path = cwd + "/" + vm

    # Cargar el XML de la máquina virtual
    tree = etree.parse(path + ".xml")
    root = tree.getroot()

    # Modificar el nombre de la máquina
    name = root.find("name")
    name.text = vm

    # Modificar la fuente del archivo de disco
    sourceFile = root.find("./devices/disk/source")
    sourceFile.set("file", path + ".qcow2")

    # Modificar la primera interfaz de red
    interface = root.find("./devices/interface")
    interface.set("type", "bridge")
    source = interface.find("source")
    source.set("bridge", bridges[vm][0])

    # Añadir el campo <virtualport type='openvswitch'/> a la primera interfaz
    virtualport = etree.SubElement(interface, "virtualport")
    virtualport.set("type", "openvswitch")

    # Si la máquina es "lb", añadir una segunda interfaz para LAN2
    if vm == "lb":
        # Crear una nueva interfaz para LAN2
        second_interface = etree.Element("interface", type="bridge")
        source2 = etree.SubElement(second_interface, "source")
        source2.set("bridge", "LAN2")

        # Modelo de la segunda interfaz
        model2 = etree.SubElement(second_interface, "model")
        model2.set("type", "virtio")

        # Añadir el campo <virtualport type='openvswitch'/> a la segunda interfaz
        virtualport2 = etree.SubElement(second_interface, "virtualport")
        virtualport2.set("type", "openvswitch")

        # Insertar la segunda interfaz en el archivo XML
        root.find("./devices").append(second_interface)

    # Guardar los cambios en el XML
    with open(path + ".xml", "wb") as fout:
        fout.write(etree.tostring(tree, pretty_print=True, encoding="utf-8"))

def configurateNet(vm):

  cwd = os.getcwd()
  path = cwd + "/" + vm

  fout = open("hostname", 'w')
  fout.write(vm + "\n")
  fout.close()
  subprocess.call(["sudo", "virt-copy-in", "-a", vm + ".qcow2", "hostname", "/etc"])
  subprocess.call(["rm", "-f", "hostname"])

  subprocess.call("sudo virt-edit -a" + vm + ".qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1" + vm + "/", shell=True)

  fout = open("interfaces", 'w')
  if vm == "lb":
    fout.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet static\n  address 10.1.1.1\n netmask 255.255.255.0\n gateway 10.1.1.1\nauto eth1\niface eth1 inet static\n  address 10.1.2.1\n netmask 255.255.255.0\n gateway 10.1.2.1")
  else:
    fout.write("auto lo \niface lo inet loopback\n auto eth0\n iface eth0 inet static\n address " + network[vm][0] +"\nnetmask 255.255.255.0 \n gateway " + network[vm][1] + "\n")
  fout.close()
  subprocess.call(["sudo", "virt-copy-in", "-a", vm + ".qcow2", "interfaces", "/etc/network"])
  subprocess.call(["rm", "-f", "interfaces"])

  if vm == "lb":
    subprocess.call("sudo virt-edit -a lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'", shell=True)


class VM:
  def _init_(self, name):
    self.name = name
    log.debug('init VM ' + self.name)

  def create_vm (self, image, interfaces):
    # nota: interfaces es un array de diccionarios de python
    #       aÃ±adir los campos que se necesiten
    log.debug("create_vm " + self.name + " (image: " + image + ")")
    subprocess.call(["qemu-img","create", "-f", "qcow2", "-F", "qcow2", "-b", "./cdps-vm-base-pc1.qcow2",  self.name + ".qcow2"])
    subprocess.call(["cp", "plantilla-vm-pc1.xml", self.name + ".xml"])
    vm = self.name
    editXml(vm)
    subprocess.call(["sudo", "virsh", "define", self.name +".xml"])
    configurateNet(vm)
    # for i in interfaces:
    #  log.debug("  if: addr=" + i["addr"] + ", mask=" + i["mask"])

  def start_vm (self):
    log.debug("start_vm " + self.name)
    subprocess.call(["sudo", "virsh", "start", self.name])
    os.system("xterm -e 'sudo virsh console "+ self.name +"'&")

  def show_console_vm (self):
    log.debug("show_console_vm " + self.name)
    os.system("xterm -e 'sudo virsh console "+ self.name +"'&")

  def stop_vm (self):
    log.debug("stop_vm " + self.name)
    subprocess.call(["sudo","virsh", "shutdown", self.name])

  def destroy_vm (self):
    log.debug("destroy_vm " + self.name)
    subprocess.call(["sudo", "virsh", "destroy", self.name])
    subprocess.call(["sudo", "virsh", "undefine", self.name])
    subprocess.call(["rm", "-f", self.name+".qcow2"])
    subprocess.call(["rm", "-f", self.name+".xml"])

class NET:
  def _init_(self, name):
    self.name = name
    log.debug('init net ' + self.name)

  def create_net(self):
      log.debug('create_net ' + self.name)
      subprocess.call(["sudo", "ovs-vsctl", "add-br", self.name])
      subprocess.call(["sudo", "ifconfig", self.name, "up"])

  def destroy_net(self):
      log.debug('destroy_net ' + self.name)
      subprocess.call(["sudo", "ifconfig", self.name, "down"])
      subprocess.call(["sudo", "ovs-vsctl", "del-br", self.name])
