╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     PANEL DE VMs MANJARO - GUÍA DE EJECUTABLES                  ║
║                     Versión 1.0.0                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════
  🚀 MÉTODO 1: EJECUTABLE DIRECTO (MÁS RÁPIDO)
═══════════════════════════════════════════════════════════════════

  Usa el archivo ejecutable standalone:

    ./manjaro-vm-panel

  ✅ No requiere instalación
  ✅ Verifica dependencias automáticamente
  ✅ Portable y fácil de actualizar

═══════════════════════════════════════════════════════════════════
  🔗 MÉTODO 2: ENLACE SIMBÓLICO (USO GLOBAL)
═══════════════════════════════════════════════════════════════════

  Crea un enlace para ejecutar desde cualquier lugar:

    sudo ln -s $(pwd)/manjaro-vm-panel /usr/local/bin/manjaro-vm-panel

  Ahora ejecuta:

    manjaro-vm-panel

  ✅ Acceso global desde terminal
  ✅ Aparece en el PATH del sistema

═══════════════════════════════════════════════════════════════════
  📦 MÉTODO 3: PAQUETE DISTRIBUIBLE
═══════════════════════════════════════════════════════════════════

  Crea un archivo .tar.gz para compartir:

    ./build_package.sh

  Genera:
    • dist/manjaro-vm-panel-1.0.0.tar.gz
    • dist/manjaro-vm-panel-1.0.0.tar.gz.sha256

  Para instalar el paquete:

    tar -xzf manjaro-vm-panel-1.0.0.tar.gz
    cd manjaro-vm-panel-1.0.0
    ./INSTALL.sh

  ✅ Perfecto para distribuir a otros usuarios
  ✅ Incluye instalador automático

═══════════════════════════════════════════════════════════════════
  🐍 MÉTODO 4: INSTALACIÓN CON PIP
═══════════════════════════════════════════════════════════════════

  Instala como paquete Python:

    pip install --user .

  Ejecuta:

    manjaro-vm-panel

  Desinstala:

    pip uninstall manjaro-vm-panel

  ✅ Integración con pip
  ✅ Fácil de actualizar y desinstalar

═══════════════════════════════════════════════════════════════════
  📦 MÉTODO 5: PAQUETE ARCH/MANJARO (PKGBUILD)
═══════════════════════════════════════════════════════════════════

  Crea un paquete nativo de Arch:

    ./build_package.sh
    cp dist/manjaro-vm-panel-1.0.0.tar.gz .
    makepkg -si

  Instala:

    sudo pacman -U manjaro-vm-panel-1.0.0-1-any.pkg.tar.zst

  Desinstala:

    sudo pacman -R manjaro-vm-panel

  ✅ Integración completa con pacman
  ✅ Gestión de dependencias automática

═══════════════════════════════════════════════════════════════════
  🔧 MÉTODO 6: MAKEFILE (ESTILO UNIX)
═══════════════════════════════════════════════════════════════════

  Usa comandos make tradicionales:

    make help          # Ver todos los comandos
    make run           # Ejecutar sin instalar
    make test          # Verificar dependencias
    sudo make install  # Instalar en /usr/local
    sudo make uninstall # Desinstalar

  ✅ Comandos estándar Unix
  ✅ Instalación en ubicaciones tradicionales

═══════════════════════════════════════════════════════════════════
  ⚙️ CONFIGURACIÓN INICIAL (REQUERIDA UNA VEZ)
═══════════════════════════════════════════════════════════════════

  1. Instalar dependencias del sistema:

     sudo pacman -S python-gobject gtk4 libadwaita libvirt qemu

  2. Instalar dependencias Python:

     pip install --user -r requirements.txt

  3. Configurar permisos:

     sudo usermod -a -G libvirt $USER
     sudo systemctl enable --now libvirtd

  4. Reiniciar sesión (importante para aplicar permisos)

═══════════════════════════════════════════════════════════════════
  📊 COMPARACIÓN DE MÉTODOS
═══════════════════════════════════════════════════════════════════

  Método              Facilidad  Portabilidad  Desinstalación
  ──────────────────────────────────────────────────────────────
  Ejecutable directo    ★★★★★      ★★★★★         ★★★★★
  Enlace simbólico      ★★★★★      ★★★★          ★★★★★
  Paquete .tar.gz       ★★★★       ★★★★★         ★★★
  pip install           ★★★★       ★★★           ★★★★★
  PKGBUILD              ★★★        ★★★★          ★★★★★
  Makefile              ★★★★       ★★★           ★★★★

═══════════════════════════════════════════════════════════════════
  💡 RECOMENDACIONES
═══════════════════════════════════════════════════════════════════

  Para desarrollo/testing:
    → ./manjaro-vm-panel

  Para uso personal diario:
    → sudo ln -s $(pwd)/manjaro-vm-panel /usr/local/bin/

  Para distribuir a otros:
    → ./build_package.sh

  Para repositorio AUR:
    → makepkg -si

═══════════════════════════════════════════════════════════════════
  📚 DOCUMENTACIÓN ADICIONAL
═══════════════════════════════════════════════════════════════════

  • QUICKSTART.md         - Inicio rápido
  • EJECUTABLE.md         - Guía completa de ejecutables
  • README.md             - Documentación principal
  • CONFIGURACION_MANUAL.md - Configuración detallada
  • CHANGELOG_ERRORES.md  - Historial de cambios

═══════════════════════════════════════════════════════════════════
  🐛 SOLUCIÓN DE PROBLEMAS
═══════════════════════════════════════════════════════════════════

  Error: "No module named 'gi'"
    → sudo pacman -S python-gobject gtk4 libadwaita

  Error: "Permission denied" con virsh
    → sudo usermod -a -G libvirt $USER
    → Cierra sesión y vuelve a entrar

  Error: "Failed to connect to libvirtd"
    → sudo systemctl start libvirtd

  El ejecutable no funciona
    → chmod +x manjaro-vm-panel

═══════════════════════════════════════════════════════════════════
  📞 SOPORTE Y AYUDA
═══════════════════════════════════════════════════════════════════

  Ejecuta con --help para ver opciones:
    ./manjaro-vm-panel --help

  Verifica dependencias:
    make test

  Lee la documentación completa:
    cat README.md

═══════════════════════════════════════════════════════════════════

  Licencia: MIT
  Versión: 1.0.0
  Plataforma: Manjaro Linux / Arch Linux

═══════════════════════════════════════════════════════════════════
