# Makefile para Panel de VMs Manjaro

.PHONY: help install uninstall run clean build package test

APP_NAME = manjaro-vm-panel
VERSION = 1.0.0
PREFIX = /usr/local
BINDIR = $(PREFIX)/bin
DATADIR = $(PREFIX)/share
APPDIR = $(DATADIR)/$(APP_NAME)
DESKTOPDIR = $(DATADIR)/applications
DOCDIR = $(DATADIR)/doc/$(APP_NAME)

help:
	@echo "Panel de VMs Manjaro - Makefile"
	@echo "================================"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make install      - Instalar en el sistema (requiere sudo)"
	@echo "  make uninstall    - Desinstalar del sistema (requiere sudo)"
	@echo "  make run          - Ejecutar sin instalar"
	@echo "  make build        - Construir paquete distribuible"
	@echo "  make package      - Crear tarball comprimido"
	@echo "  make clean        - Limpiar archivos generados"
	@echo "  make test         - Verificar dependencias"
	@echo ""

install:
	@echo "📦 Instalando $(APP_NAME)..."
	# Crear directorios
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(APPDIR)
	install -d $(DESTDIR)$(DESKTOPDIR)
	install -d $(DESTDIR)$(DOCDIR)
	
	# Instalar archivos Python
	install -m 644 main.py $(DESTDIR)$(APPDIR)/
	install -m 644 vm_manager.py $(DESTDIR)$(APPDIR)/
	install -m 644 ui.py $(DESTDIR)$(APPDIR)/
	install -m 644 notifications.py $(DESTDIR)$(APPDIR)/
	install -m 644 widgets.py $(DESTDIR)$(APPDIR)/
	install -m 644 style.css $(DESTDIR)$(APPDIR)/
	
	# Instalar ejecutable
	install -m 755 $(APP_NAME) $(DESTDIR)$(BINDIR)/
	
	# Instalar archivo .desktop
	install -m 644 $(APP_NAME).desktop $(DESTDIR)$(DESKTOPDIR)/
	sed -i 's|Exec=.*|Exec=$(BINDIR)/$(APP_NAME)|g' $(DESTDIR)$(DESKTOPDIR)/$(APP_NAME).desktop
	
	# Instalar documentación
	install -m 644 README.md $(DESTDIR)$(DOCDIR)/
	install -m 644 CHANGELOG_ERRORES.md $(DESTDIR)$(DOCDIR)/
	install -m 644 CONFIGURACION_MANUAL.md $(DESTDIR)$(DOCDIR)/
	
	@echo "✅ Instalación completada en $(PREFIX)"
	@echo ""
	@echo "⚠️  Configuración necesaria:"
	@echo "   sudo usermod -a -G libvirt $$USER"
	@echo "   sudo systemctl enable --now libvirtd"
	@echo "   Cierra sesión y vuelve a entrar"

uninstall:
	@echo "🗑️  Desinstalando $(APP_NAME)..."
	rm -f $(DESTDIR)$(BINDIR)/$(APP_NAME)
	rm -rf $(DESTDIR)$(APPDIR)
	rm -f $(DESTDIR)$(DESKTOPDIR)/$(APP_NAME).desktop
	rm -rf $(DESTDIR)$(DOCDIR)
	@echo "✅ Desinstalación completada"

run:
	@echo "🚀 Ejecutando $(APP_NAME)..."
	./$(APP_NAME)

build:
	@echo "🔨 Construyendo paquete..."
	./build_package.sh

package: build
	@echo "📦 Paquete creado en dist/"

clean:
	@echo "🧹 Limpiando archivos generados..."
	rm -rf build dist __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Limpieza completada"

test:
	@echo "🔍 Verificando dependencias..."
	@python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1'); print('✅ GTK4/Adwaita: OK')" || echo "❌ GTK4/Adwaita: FALTA"
	@python3 -c "import cairo; print('✅ Cairo: OK')" || echo "❌ Cairo: FALTA"
	@which virsh > /dev/null && echo "✅ virsh: OK" || echo "❌ virsh: FALTA"
	@systemctl is-active libvirtd > /dev/null && echo "✅ libvirtd: ACTIVO" || echo "⚠️  libvirtd: INACTIVO"
	@groups | grep -q libvirt && echo "✅ Grupo libvirt: OK" || echo "⚠️  Grupo libvirt: FALTA"
