# Maintainer: Tu Nombre <tu@email.com>
pkgname=manjaro-vm-panel
pkgver=1.0.0
pkgrel=1
pkgdesc="Panel de control moderno para máquinas virtuales QEMU/KVM"
arch=('any')
url="https://github.com/tu-usuario/manjaro-vm-panel"
license=('MIT')
depends=(
    'python>=3.8'
    'python-gobject'
    'gtk4'
    'libadwaita'
    'python-cairo'
    'libvirt'
    'qemu-base'
)
makedepends=('python-setuptools')
optdepends=(
    'qemu-guest-agent: Para obtener información del guest'
    'notify-send: Para notificaciones del sistema'
)
source=("${pkgname}-${pkgver}.tar.gz")
sha256sums=('SKIP')

build() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python setup.py build
}

package() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    
    # Instalar con setup.py
    python setup.py install --root="${pkgdir}" --optimize=1 --skip-build
    
    # Instalar ejecutable principal
    install -Dm755 manjaro-vm-panel "${pkgdir}/usr/bin/manjaro-vm-panel"
    
    # Instalar archivos de datos
    install -Dm644 style.css "${pkgdir}/usr/share/${pkgname}/style.css"
    install -Dm644 manjaro-vm-panel.desktop "${pkgdir}/usr/share/applications/manjaro-vm-panel.desktop"
    
    # Instalar documentación
    install -Dm644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"
    install -Dm644 CHANGELOG_ERRORES.md "${pkgdir}/usr/share/doc/${pkgname}/CHANGELOG_ERRORES.md"
    install -Dm644 CONFIGURACION_MANUAL.md "${pkgdir}/usr/share/doc/${pkgname}/CONFIGURACION_MANUAL.md"
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}

post_install() {
    echo "================================================"
    echo "Panel de VMs Manjaro instalado correctamente"
    echo "================================================"
    echo ""
    echo "Configuración necesaria:"
    echo "  1. Añade tu usuario al grupo libvirt:"
    echo "     sudo usermod -a -G libvirt \$USER"
    echo ""
    echo "  2. Habilita el servicio libvirtd:"
    echo "     sudo systemctl enable --now libvirtd"
    echo ""
    echo "  3. Cierra sesión y vuelve a entrar"
    echo ""
    echo "Ejecutar: manjaro-vm-panel"
    echo ""
}
