# Práctica Creativa 1 CDPS 2024/25

Este proyecto implementa un script en Python para gestionar un escenario de máquinas virtuales (VMs) y redes virtuales utilizando herramientas como `virsh`, `qemu-img`, y `ovs-vsctl`. Está diseñado para trabajar en un entorno Debian configurado con el script `/lab/cnvr/bin/prepare-vnx-debian`.

---

## **Autores**

Nicolas García Sobrino, Javier de Ponte Hernando y Santiago Rayán Castro.
nicolas.garciasobrino@alumnos.upm.es, j.deponteh@alumnos.upm.es y s.rayan@alumnos.upm.es

---

## **Estructura del Proyecto**

### **Archivos principales**
1. **`manage-p2.py`**  
   Script principal que permite gestionar el escenario virtual mediante las siguientes órdenes:
   - `create`: Crea las máquinas virtuales y configura las redes virtuales.
   - `start`: Inicia todas las máquinas virtuales o una en particular.
   - `stop`: Detiene todas las máquinas virtuales o una específica.
   - `destroy`: Elimina el escenario y las configuraciones creadas.
   - `monitor`: Muestra el estado de las máquinas virtuales y redes del escenario.

2. **`lib_vm.py`**  
   Librería que contiene las clases y funciones necesarias para gestionar máquinas virtuales (`VM`) y redes virtuales (`NET`).

3. **`manage-p2.json`**  
   Archivo de configuración en formato JSON que define:
   - `number_of_servers`: Número de servidores a crear (de 1 a 5).
   - `debug`: Activa/desactiva el modo detallado de depuración.

4. **`plantilla-vm-pc1.xml`**  
   Plantilla XML base para la definición de máquinas virtuales.

### **Estructura del proyecto**
```plaintext
.
├── manage-p2.py
├── lib_vm.py
├── manage-p2.json
├── plantilla-vm-pc1.xml
```

---

## **Requisitos del sistema**

- **Sistema operativo**: Debian o derivado.
- **Dependencias**:
  - Python 3.x
  - Paquetes de Python: `lxml`, `logging`
  - Herramientas de virtualización:
    - `qemu-img`
    - `virsh`
    - `ovs-vsctl`
    - `virt-copy-in`
    - `virt-edit`

---

## **Configuración previa**

1. **Preparar el entorno**  
   Antes de ejecutar el script, ejecute el siguiente comando en su terminal para configurar el entorno del laboratorio:
   ```bash
   /lab/cnvr/bin/prepare-vnx-debian
   ```

2. **Editar el archivo de configuración (`manage-p2.json`)**  
   Ejemplo de configuración:
   ```json
   {
       "number_of_servers": 3,
       "debug": true
   }
   ```
   - `number_of_servers`: Número de servidores web que se crearán (1-5).
   - `debug`: Activa mensajes detallados para depuración si está en `true`.

---

## **Uso del script**

### **Comandos disponibles**
El script `manage-p2.py` acepta los siguientes comandos:

- **Crear el escenario**  
   ```bash
   python3 manage-p2.py create
   ```

- **Iniciar todas las VMs**  
   ```bash
   python3 manage-p2.py start
   ```

- **Iniciar una VM específica**  
   ```bash
   python3 manage-p2.py start <vm_name>
   ```
   Ejemplo:  
   ```bash
   python3 manage-p2.py start s1
   ```

- **Detener todas las VMs**  
   ```bash
   python3 manage-p2.py stop
   ```

- **Detener una VM específica**  
   ```bash
   python3 manage-p2.py stop <vm_name>
   ```
   Ejemplo:  
   ```bash
   python3 manage-p2.py stop s2
   ```

- **Destruir el escenario completo**  
   ```bash
   python3 manage-p2.py destroy
   ```

- **Monitorizar el estado del escenario**  
   ```bash
   python3 manage-p2.py monitor
   ```

---

## **Funcionalidades principales**

1. **Creación de VMs**  
   - Generación de archivos de disco (`qcow2`) a partir de una imagen base.
   - Configuración personalizada de archivos XML para cada VM.
   - Configuración de red específica para cada VM.

2. **Gestión de redes virtuales**  
   - Creación y eliminación de puentes (`LAN1`, `LAN2`) utilizando `ovs-vsctl`.

3. **Arranque y apagado de VMs**  
   - Uso de `virsh` para manejar el ciclo de vida de las VMs.

4. **Monitorización del escenario**  
   - Comando para inspeccionar el estado de todas las VMs y redes.

5. **Soporte para configuraciones dinámicas**  
   - Configuración del número de servidores y nivel de detalle desde un archivo JSON.

---

## **Notas importantes**

1. **Permisos de administrador**  
   Algunas operaciones requieren permisos de superusuario (`sudo`). Asegúrese de ejecutarlas en un entorno con privilegios.

2. **Depuración**  
   Si se habilita el modo `debug` en el archivo JSON, el script generará mensajes detallados para depuración.

3. **Restricciones**  
   - El número de servidores debe estar entre 1 y 5. El script se detendrá si este rango no se cumple.

4. **Archivos temporales**  
   - Durante la ejecución, se generan archivos temporales como `hostname` y `interfaces`. Estos son gestionados automáticamente por el script.

---

