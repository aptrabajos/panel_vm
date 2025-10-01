#!/bin/bash

# Script simple para configurar solo el grupo libvirt
echo "=== Configuración Simple del Panel de VMs ==="
echo "Este script solo añade tu usuario al grupo libvirt."
echo "El panel usará pkexec para pedir permisos cuando sea necesario."
echo ""

# Verificar que el usuario tenga permisos sudo
if ! sudo -v; then
    echo "Error: No tienes permisos de sudo o la contraseña es incorrecta"
    exit 1
fi

# Verificar que el usuario esté en el grupo libvirt
if ! groups "$USER" | grep -q "libvirt"; then
    echo "Añadiendo usuario al grupo libvirt..."
    sudo usermod -a -G libvirt "$USER"
    echo "✓ Usuario añadido al grupo libvirt"
    echo "⚠ Es necesario cerrar sesión y volver a entrar para aplicar los cambios"
else
    echo "✓ Usuario ya está en el grupo libvirt"
fi

# Verificar que libvirtd esté ejecutándose
if ! systemctl is-active --quiet libvirtd; then
    echo "Iniciando servicio libvirtd..."
    sudo systemctl start libvirtd
    sudo systemctl enable libvirtd
    echo "✓ Servicio libvirtd iniciado y habilitado"
else
    echo "✓ Servicio libvirtd ya está ejecutándose"
fi

echo ""
echo "=== Configuración completada ==="
echo "Modo de funcionamiento:"
echo "- El panel usará pkexec para pedir permisos cuando sea necesario"
echo "- Aparecerá un diálogo para ingresar tu contraseña antes de cada operación"
echo "- Esto es más seguro pero requiere autenticación cada vez"
echo ""
echo "Para ejecutar el panel: python3 main.py"
echo ""
if ! groups "$USER" | grep -q "libvirt"; then
    echo "⚠ IMPORTANTE: Reinicia tu sesión para aplicar los cambios de grupo"
fi