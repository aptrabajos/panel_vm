#!/bin/bash

# Script de configuración usando pkexec (GUI)
echo "=== Configuración del Panel de VMs (GUI) ==="
echo "Este script usa pkexec para configurar permisos gráficamente."
echo ""

# Función para mostrar notificaciones
notify_user() {
    if command -v notify-send &> /dev/null; then
        notify-send "Panel VM Setup" "$1"
    fi
    echo "$1"
}

# Verificar que pkexec esté disponible
if ! command -v pkexec &> /dev/null; then
    echo "Error: pkexec no está disponible en el sistema"
    echo "Instala polkit: sudo pacman -S polkit"
    exit 1
fi

# Crear script temporal para ejecutar con pkexec
TEMP_SCRIPT="/tmp/vm-panel-setup.sh"
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash

USER_NAME="$1"

# Añadir usuario al grupo libvirt
if ! groups "$USER_NAME" | grep -q "libvirt"; then
    usermod -a -G libvirt "$USER_NAME"
    echo "Usuario $USER_NAME añadido al grupo libvirt"
else
    echo "Usuario $USER_NAME ya está en el grupo libvirt"
fi

# Iniciar y habilitar libvirtd
if ! systemctl is-active --quiet libvirtd; then
    systemctl start libvirtd
    systemctl enable libvirtd
    echo "Servicio libvirtd iniciado y habilitado"
else
    echo "Servicio libvirtd ya está ejecutándose"
fi

# Crear configuración opcional de sudo sin contraseña
SUDOERS_FILE="/etc/sudoers.d/manjaro-vm-panel"
if [ ! -f "$SUDOERS_FILE" ]; then
    cat > "$SUDOERS_FILE" << 'EOSUDO'
# Permitir comandos virsh sin contraseña para el panel de VMs
%libvirt ALL=(ALL) NOPASSWD: /usr/bin/virsh
EOSUDO
    echo "$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/virsh" >> "$SUDOERS_FILE"
    chmod 440 "$SUDOERS_FILE"
    echo "Configuración sudo creada en $SUDOERS_FILE"
fi

echo "Configuración completada exitosamente"
EOF

chmod +x "$TEMP_SCRIPT"

# Ejecutar con pkexec
echo "Se abrirá un diálogo para ingresar tu contraseña..."
if pkexec "$TEMP_SCRIPT" "$USER"; then
    notify_user "✓ Configuración completada exitosamente"
    echo ""
    echo "=== Configuración completada ==="
    echo "✓ Usuario añadido al grupo libvirt"
    echo "✓ Servicio libvirtd configurado"
    echo "✓ Configuración sudo creada (opcional)"
    echo ""
    echo "Para aplicar los cambios de grupo:"
    echo "1. Cierra sesión y vuelve a entrar, O"
    echo "2. Ejecuta: newgrp libvirt"
    echo ""
    echo "Para ejecutar el panel: python3 main.py"
else
    notify_user "✗ Error en la configuración"
    echo "Error: La configuración falló o fue cancelada"
    exit 1
fi

# Limpiar
rm -f "$TEMP_SCRIPT"