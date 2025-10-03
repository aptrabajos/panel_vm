# ⚡ Inicio Rápido - Panel de VMs Manjaro

## 🚀 Ejecutar AHORA (Sin Instalación)

```bash
./manjaro-vm-panel
```

---

## 📦 Crear Paquete Distribuible

```bash
./build_package.sh
```

Genera: `dist/manjaro-vm-panel-1.0.0.tar.gz`

---

## 🔗 Instalación Rápida (Enlace Simbólico)

```bash
sudo ln -s $(pwd)/manjaro-vm-panel /usr/local/bin/manjaro-vm-panel
```

Ahora ejecuta desde cualquier lugar:
```bash
manjaro-vm-panel
```

---

## 📋 Otras Opciones

| Método | Comando |
|--------|---------|
| **Makefile** | `sudo make install` |
| **pip** | `pip install --user .` |
| **PKGBUILD** | `makepkg -si` |

---

## ⚙️ Configuración Inicial (Una vez)

```bash
# 1. Instalar dependencias
sudo pacman -S python-gobject gtk4 libadwaita libvirt qemu

# 2. Configurar permisos
sudo usermod -a -G libvirt $USER
sudo systemctl enable --now libvirtd

# 3. Reiniciar sesión
```

---

## 📚 Documentación Completa

- **Ejecutables**: `EJECUTABLE.md`
- **Manual completo**: `README.md`
- **Configuración**: `CONFIGURACION_MANUAL.md`
