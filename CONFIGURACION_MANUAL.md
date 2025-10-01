# Configuración Manual del Panel de VMs

Si los scripts automáticos no funcionan, puedes configurar todo manualmente.

## Opción 1: Configuración Básica (Recomendada)

### 1. Añadir usuario al grupo libvirt
```bash
sudo usermod -a -G libvirt $USER
```

### 2. Reiniciar sesión
- Cierra sesión y vuelve a entrar, O
- Ejecuta: `newgrp libvirt`

### 3. Verificar que libvirtd esté ejecutándose
```bash
sudo systemctl start libvirtd
sudo systemctl enable libvirtd
```

### 4. Probar acceso
```bash
virsh -c qemu:///system list --all
```

Con esta configuración, el panel usará `pkexec` para pedir permisos cuando sea necesario.

## Opción 2: Sudo sin contraseña (Opcional)

Si quieres evitar que te pida contraseña cada vez:

### 1. Crear archivo de configuración sudo
```bash
sudo visudo -f /etc/sudoers.d/manjaro-vm-panel
```

### 2. Añadir estas líneas:
```
# Permitir comandos virsh sin contraseña para el panel de VMs
%libvirt ALL=(ALL) NOPASSWD: /usr/bin/virsh
tu_usuario ALL=(ALL) NOPASSWD: /usr/bin/virsh
```

Reemplaza `tu_usuario` con tu nombre de usuario real.

### 3. Guardar y salir (Ctrl+O, Enter, Ctrl+X en nano)

## Verificación

Para verificar que todo está configurado:

```bash
# Verificar grupo
groups $USER | grep libvirt

# Verificar libvirtd
systemctl is-active libvirtd

# Probar virsh
virsh -c qemu:///system list --all
```

## Ejecutar el Panel

Una vez configurado:

```bash
cd /ruta/al/panel_vm
python3 main.py
```

## Solución de Problemas

### Error "permission denied"
- Verifica que estés en el grupo libvirt: `groups $USER`
- Reinicia tu sesión si acabas de añadirte al grupo

### Error "failed to connect to libvirtd"
- Inicia el servicio: `sudo systemctl start libvirtd`
- Verifica que esté ejecutándose: `systemctl status libvirtd`

### Error "command not found: virsh"
- Instala libvirt: `sudo pacman -S libvirt`

### Las VMs no aparecen
- Verifica que existan: `sudo virsh list --all`
- Modifica `vm_manager.py` si tienes VMs con otros nombres