# Panel de Máquinas Virtuales Manjaro

Un panel de control profesional y moderno para administrar máquinas virtuales QEMU/KVM en Manjaro Linux.

## Características

- **Interfaz moderna**: Diseñado con GTK4 y libadwaita para una integración perfecta con el escritorio
- **Control completo**: Iniciar, apagar, reiniciar, pausar y forzar apagado de VMs
- **Monitoreo en tiempo real**: Estado actualizado automáticamente cada 5 segundos
- **Monitoreo avanzado**:
  - 🌐 Dirección IP de cada VM
  - ⚙️ Uso de CPUs virtuales (vCPUs activas/totales)
  - 💾 Memoria RAM con barra de progreso colorizada
  - 📊 Uso de disco (lectura/escritura en MB)
  - 🌐 Tráfico de red (recibido/enviado en MB)
  - 📈 Sección expandible "Ver detalles avanzados" con métricas completas
- **Notificaciones**: Sistema de notificaciones integrado para feedback de operaciones
- **Manejo de errores**: Mensajes de error claros y específicos
- **Integración con escritorio**: Aparece en el menú de aplicaciones

## Máquinas Virtuales Soportadas

El panel está configurado para administrar las siguientes VMs:
- `manjaro1`
- `manjaro2`

## Instalación

### Requisitos previos

- Manjaro Linux con escritorio GNOME/KDE
- QEMU/KVM instalado y configurado
- libvirt instalado y ejecutándose
- Python 3.8 o superior

### Instalación automática

1. Clona o descarga este repositorio
2. Navega al directorio del proyecto
3. Ejecuta uno de los scripts de configuración:

**Opción A - Configuración completa (recomendada):**
```bash
./setup_gui.sh
```

**Opción B - Solo configuración básica:**
```bash
./setup_simple.sh
```

**Opción C - Instalación completa del sistema:**
```bash
./install.sh
```

**Si los scripts no funcionan**, consulta `CONFIGURACION_MANUAL.md`

### Instalación manual

1. Instala las dependencias del sistema:
```bash
sudo pacman -S python-gobject gtk4 libadwaita python-pip
```

2. Instala las dependencias de Python:
```bash
pip install --user -r requirements.txt
```

3. Asegúrate de tener permisos para usar libvirt:
```bash
sudo usermod -a -G libvirt $USER
```

4. Reinicia tu sesión para aplicar los cambios de grupo

## Uso

### Ejecutar la aplicación

Después de la instalación, puedes ejecutar la aplicación de varias formas:

1. **Desde el menú de aplicaciones**: Busca "Panel de VMs Manjaro"
2. **Desde la terminal**: `manjaro-vm-panel`
3. **Directamente**: `python3 main.py` (desde el directorio del proyecto)

### Funcionalidades

#### Controles de VM

- **Iniciar**: Inicia una VM apagada
- **Apagar**: Apaga gracefully una VM en ejecución
- **Reiniciar**: Reinicia una VM en ejecución
- **Pausar**: Guarda el estado actual de la VM y la suspende
- **Forzar**: Fuerza el apagado inmediato de una VM (requiere confirmación)

#### Monitoreo

- **Estado en tiempo real**: El estado de las VMs se actualiza automáticamente
- **Información de recursos**: Muestra tiempo de CPU y uso de memoria para VMs en ejecución
- **Indicadores visuales**: Colores y iconos para identificar rápidamente el estado

#### Notificaciones

- **Notificaciones de éxito**: Confirman cuando las operaciones se completan exitosamente
- **Alertas de error**: Muestran mensajes claros cuando algo sale mal
- **Notificaciones del sistema**: Integración con el sistema de notificaciones de Manjaro

## Estructura del Proyecto

```
panel_vm/
├── main.py                    # Punto de entrada de la aplicación
├── ui.py                      # Interfaz gráfica de usuario
├── vm_manager.py              # Lógica de administración de VMs
├── notifications.py           # Sistema de notificaciones y manejo de errores
├── style.css                  # Estilos personalizados
├── requirements.txt           # Dependencias de Python
├── install.sh                 # Script de instalación
├── manjaro-vm-panel.desktop   # Entrada del menú de aplicaciones
└── README.md                  # Este archivo
```

## Comandos virsh utilizados

La aplicación utiliza los siguientes comandos de `virsh` internamente:

- `virsh list --all` - Listar todas las VMs
- `virsh start <vm>` - Iniciar VM
- `virsh shutdown <vm>` - Apagar VM gracefully
- `virsh destroy <vm>` - Forzar apagado
- `virsh reboot <vm>` - Reiniciar VM
- `virsh managedsave <vm>` - Pausar/guardar estado
- `virsh managedsave-remove <vm>` - Eliminar estado guardado

## Solución de Problemas

### Error de permisos

Si obtienes errores de permisos, asegúrate de:

1. Estar en el grupo `libvirt`:
```bash
groups $USER | grep libvirt
```

2. Si no estás en el grupo, añádete:
```bash
sudo usermod -a -G libvirt $USER
```

3. Reinicia tu sesión

### libvirtd no está ejecutándose

Si no puedes conectarte a libvirt:

```bash
sudo systemctl start libvirtd
sudo systemctl enable libvirtd
```

### Las VMs no aparecen

Verifica que las VMs existen y están definidas:

```bash
sudo virsh list --all
```

Si necesitas modificar qué VMs administrar, edita `vm_manager.py` y cambia la lista `vm_names`.

## Personalización

### Añadir más VMs

Para administrar VMs adicionales, modifica el archivo `vm_manager.py`:

```python
self.vm_names = ["manjaro1", "manjaro2", "nueva_vm"]
```

### Modificar estilos

Los estilos se pueden personalizar editando `style.css`. La aplicación usa el tema Adwaita por defecto.

### Cambiar frecuencia de actualización

Para cambiar la frecuencia de actualización automática (por defecto 5 segundos), modifica `ui.py`:

```python
GLib.timeout_add_seconds(NUEVOS_SEGUNDOS, auto_update)
```

## Contribuir

Si encuentras bugs o tienes sugerencias de mejoras, por favor:

1. Abre un issue describiendo el problema o mejora
2. Si es posible, incluye logs o capturas de pantalla
3. Para contribuciones de código, crea un pull request

## Licencia

Este proyecto está bajo licencia MIT. Ver el archivo LICENSE para más detalles.

## Autor

Desarrollado para administrar máquinas virtuales Manjaro de manera eficiente y profesional.