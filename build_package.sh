#!/bin/bash
# Script para construir paquete distribuible del Panel de VMs Manjaro

set -e  # Salir si hay errores

echo "🔨 Construyendo paquete de Panel de VMs Manjaro"
echo "================================================"

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
APP_NAME="manjaro-vm-panel"
VERSION="1.0.0"
BUILD_DIR="build"
DIST_DIR="dist"
PACKAGE_DIR="${DIST_DIR}/${APP_NAME}-${VERSION}"

# Limpiar builds anteriores
echo -e "${BLUE}🧹 Limpiando builds anteriores...${NC}"
rm -rf "${BUILD_DIR}" "${DIST_DIR}"
mkdir -p "${PACKAGE_DIR}"

# Copiar archivos necesarios
echo -e "${BLUE}📦 Copiando archivos del proyecto...${NC}"
cp main.py vm_manager.py ui.py notifications.py widgets.py "${PACKAGE_DIR}/"
cp style.css requirements.txt "${PACKAGE_DIR}/"
cp manjaro-vm-panel "${PACKAGE_DIR}/"
cp manjaro-vm-panel.desktop "${PACKAGE_DIR}/"
cp README.md CHANGELOG_ERRORES.md CONFIGURACION_MANUAL.md comando.md "${PACKAGE_DIR}/"

# Copiar scripts de instalación
echo -e "${BLUE}📋 Copiando scripts de instalación...${NC}"
cp install.sh setup_gui.sh setup_simple.sh setup_sudo.sh "${PACKAGE_DIR}/"
chmod +x "${PACKAGE_DIR}"/*.sh
chmod +x "${PACKAGE_DIR}/${APP_NAME}"

# Crear script de instalación simplificado
echo -e "${BLUE}✍️  Creando instalador simplificado...${NC}"
cat > "${PACKAGE_DIR}/INSTALL.sh" << 'EOF'
#!/bin/bash
# Instalador rápido para Panel de VMs Manjaro

echo "=== Instalador de Panel de VMs Manjaro ==="
echo ""

# Verificar dependencias del sistema
echo "📦 Verificando dependencias del sistema..."
if ! pacman -Qi python-gobject gtk4 libadwaita &> /dev/null; then
    echo "Instalando dependencias del sistema..."
    sudo pacman -S --needed python-gobject gtk4 libadwaita python-pip libvirt qemu
fi

# Instalar dependencias Python
echo "🐍 Instalando dependencias Python..."
pip install --user -r requirements.txt

# Configurar permisos
echo "🔐 Configurando permisos..."
if ! groups "$USER" | grep -q "libvirt"; then
    sudo usermod -a -G libvirt "$USER"
    echo "⚠️  Necesitas cerrar sesión y volver a entrar para aplicar permisos"
fi

# Iniciar libvirtd
echo "🚀 Iniciando servicio libvirtd..."
sudo systemctl enable --now libvirtd

# Crear enlace simbólico en /usr/local/bin
echo "🔗 Creando enlace ejecutable..."
INSTALL_DIR="$(pwd)"
sudo ln -sf "${INSTALL_DIR}/manjaro-vm-panel" /usr/local/bin/manjaro-vm-panel

# Actualizar archivo .desktop con ruta correcta
echo "🖥️  Configurando entrada del menú..."
sed "s|Exec=.*|Exec=${INSTALL_DIR}/manjaro-vm-panel|g" manjaro-vm-panel.desktop > ~/.local/share/applications/manjaro-vm-panel.desktop
chmod +x ~/.local/share/applications/manjaro-vm-panel.desktop

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Puedes ejecutar el panel con:"
echo "  1. Comando: manjaro-vm-panel"
echo "  2. Desde el menú de aplicaciones"
echo "  3. Directamente: ./manjaro-vm-panel"
echo ""
EOF

chmod +x "${PACKAGE_DIR}/INSTALL.sh"

# Crear README de instalación
echo -e "${BLUE}📝 Creando guía de instalación...${NC}"
cat > "${PACKAGE_DIR}/INSTALACION.txt" << 'EOF'
╔════════════════════════════════════════════════════════════╗
║        Panel de Máquinas Virtuales Manjaro v1.0.0         ║
╚════════════════════════════════════════════════════════════╝

INSTALACIÓN RÁPIDA:
===================

1. Extrae el archivo en tu ubicación preferida
2. Abre una terminal en el directorio extraído
3. Ejecuta: ./INSTALL.sh
4. Cierra sesión y vuelve a entrar (para permisos)
5. Ejecuta: manjaro-vm-panel

INSTALACIÓN MANUAL:
===================

1. Instalar dependencias:
   sudo pacman -S python-gobject gtk4 libadwaita libvirt qemu
   pip install --user -r requirements.txt

2. Configurar permisos:
   sudo usermod -a -G libvirt $USER
   sudo systemctl enable --now libvirtd

3. Ejecutar:
   ./manjaro-vm-panel

OPCIONES DE INSTALACIÓN:
========================

- ./INSTALL.sh         → Instalación automática (recomendado)
- ./setup_gui.sh       → Configuración con interfaz gráfica
- ./install.sh         → Instalación completa del sistema
- ./manjaro-vm-panel   → Ejecutar directamente sin instalar

REQUISITOS:
===========

- Manjaro Linux (o Arch Linux)
- Python 3.8+
- GTK4 y libadwaita
- QEMU/KVM y libvirt

SOPORTE:
========

Documentación: README.md
Configuración manual: CONFIGURACION_MANUAL.md
Changelog: CHANGELOG_ERRORES.md

EOF

# Crear archivo de licencia
echo -e "${BLUE}⚖️  Creando archivo de licencia...${NC}"
cat > "${PACKAGE_DIR}/LICENSE" << 'EOF'
MIT License

Copyright (c) 2025 Manjaro VM Panel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Crear tarball comprimido
echo -e "${BLUE}📦 Creando archivo comprimido...${NC}"
cd "${DIST_DIR}"
tar -czf "${APP_NAME}-${VERSION}.tar.gz" "${APP_NAME}-${VERSION}"
cd ..

# Crear checksum
echo -e "${BLUE}🔐 Generando checksum...${NC}"
cd "${DIST_DIR}"
sha256sum "${APP_NAME}-${VERSION}.tar.gz" > "${APP_NAME}-${VERSION}.tar.gz.sha256"
cd ..

# Resumen
echo ""
echo -e "${GREEN}✅ ¡Paquete construido exitosamente!${NC}"
echo ""
echo "📦 Archivos generados:"
echo "   - ${DIST_DIR}/${APP_NAME}-${VERSION}.tar.gz"
echo "   - ${DIST_DIR}/${APP_NAME}-${VERSION}.tar.gz.sha256"
echo ""
echo "📂 Contenido del paquete:"
ls -lh "${PACKAGE_DIR}/"
echo ""
echo -e "${YELLOW}💡 Para distribuir:${NC}"
echo "   Comparte el archivo: ${DIST_DIR}/${APP_NAME}-${VERSION}.tar.gz"
echo ""
echo -e "${YELLOW}💡 Para instalar:${NC}"
echo "   1. Extrae: tar -xzf ${APP_NAME}-${VERSION}.tar.gz"
echo "   2. cd ${APP_NAME}-${VERSION}"
echo "   3. ./INSTALL.sh"
echo ""
