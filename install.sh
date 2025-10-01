#!/bin/bash

# Script de instalación para Panel de VMs Manjaro
echo "=== Instalador del Panel de VMs Manjaro ==="

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo "Error: Ejecuta este script desde el directorio del proyecto"
    exit 1
fi

# Crear directorio de aplicación en /opt
APP_DIR="/opt/manjaro-vm-panel"
echo "Creando directorio de aplicación en $APP_DIR..."
sudo mkdir -p "$APP_DIR"

# Copiar archivos de la aplicación
echo "Copiando archivos de aplicación..."
sudo cp main.py vm_manager.py ui.py style.css requirements.txt "$APP_DIR/"
sudo chmod +x "$APP_DIR/main.py"

# Instalar dependencias de Python
echo "Instalando dependencias de Python..."
sudo pacman -S --needed python-gobject gtk4 libadwaita python-pip
pip install --user -r requirements.txt

# Crear script ejecutable en /usr/local/bin
echo "Creando script ejecutable..."
sudo tee /usr/local/bin/manjaro-vm-panel > /dev/null << 'EOF'
#!/bin/bash
cd /opt/manjaro-vm-panel
python3 main.py "$@"
EOF

sudo chmod +x /usr/local/bin/manjaro-vm-panel

# Instalar archivo .desktop
echo "Instalando entrada del menú de aplicaciones..."
DESKTOP_FILE="manjaro-vm-panel.desktop"
sudo cp "$DESKTOP_FILE" /usr/share/applications/
sudo chmod 644 /usr/share/applications/"$DESKTOP_FILE"

# Actualizar la cache de aplicaciones
echo "Actualizando cache de aplicaciones..."
sudo update-desktop-database /usr/share/applications/

# Crear grupo y permisos para acceso a libvirt (si el usuario no está ya en el grupo)
echo "Configurando permisos de libvirt..."
if ! groups "$USER" | grep -q "libvirt"; then
    sudo usermod -a -G libvirt "$USER"
    echo "Usuario añadido al grupo libvirt. Es posible que necesites cerrar sesión y volver a entrar."
fi

echo ""
echo "=== Instalación completada ==="
echo "Puedes ejecutar la aplicación de estas formas:"
echo "1. Desde el menú de aplicaciones: busca 'Panel de VMs Manjaro'"
echo "2. Desde la terminal: manjaro-vm-panel"
echo "3. Directamente: python3 $APP_DIR/main.py"
echo ""
echo "Nota: Si acabas de ser añadido al grupo libvirt, reinicia la sesión para aplicar los cambios."