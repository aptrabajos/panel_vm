#!/bin/bash

# Script para configurar sudo sin contraseña para comandos virsh
echo "=== Configurando sudo para virsh ==="
echo "Este script necesita permisos de administrador para configurar sudo."
echo "Se te pedirá la contraseña de sudo una vez."
echo ""

# Verificar que el usuario tenga permisos sudo
if ! sudo -v; then
    echo "Error: No tienes permisos de sudo o la contraseña es incorrecta"
    exit 1
fi

# Crear archivo sudoers para virsh
SUDOERS_FILE="/etc/sudoers.d/manjaro-vm-panel"

echo "Creando configuración de sudo para virsh..."

# Crear el contenido del archivo sudoers
cat > /tmp/manjaro-vm-panel-sudoers << 'EOF'
# Permitir comandos virsh sin contraseña para el panel de VMs
%libvirt ALL=(ALL) NOPASSWD: /usr/bin/virsh
EOF

# Añadir regla específica para el usuario actual
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/virsh" >> /tmp/manjaro-vm-panel-sudoers

# Mover el archivo a la ubicación correcta
sudo mv /tmp/manjaro-vm-panel-sudoers "$SUDOERS_FILE"
sudo chmod 440 "$SUDOERS_FILE"

# Verificar la sintaxis del archivo
if sudo visudo -c -f "$SUDOERS_FILE"; then
    echo "✓ Configuración de sudo creada correctamente"
    echo "✓ Ahora puedes usar virsh sin contraseña"
else
    echo "✗ Error en la configuración de sudo"
    sudo rm -f "$SUDOERS_FILE"
    exit 1
fi

# Verificar que el usuario esté en el grupo libvirt
if ! groups "$USER" | grep -q "libvirt"; then
    echo "Añadiendo usuario al grupo libvirt..."
    sudo usermod -a -G libvirt "$USER"
    echo "⚠ Es necesario cerrar sesión y volver a entrar para aplicar los cambios de grupo"
else
    echo "✓ Usuario ya está en el grupo libvirt"
fi

echo ""
echo "=== Configuración completada ==="
echo "Nota: Si acabas de ser añadido al grupo libvirt, reinicia la sesión."