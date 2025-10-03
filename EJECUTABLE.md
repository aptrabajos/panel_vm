# 🚀 Guía de Ejecutables para Panel de VMs Manjaro

Este documento explica todas las formas de crear y usar ejecutables del Panel de VMs.

---

## 📦 Opciones Disponibles

### 1. **Ejecutable Standalone** (Más Simple) ⭐ RECOMENDADO

El archivo `manjaro-vm-panel` es un script Python ejecutable que puedes usar directamente.

**Uso:**
```bash
# Ejecutar desde el directorio del proyecto
./manjaro-vm-panel

# O crear enlace simbólico para uso global
sudo ln -s $(pwd)/manjaro-vm-panel /usr/local/bin/manjaro-vm-panel
manjaro-vm-panel  # Ahora funciona desde cualquier lugar
```

**Ventajas:**
- ✅ No requiere instalación
- ✅ Portable
- ✅ Fácil de actualizar
- ✅ Verifica dependencias automáticamente

---

### 2. **Paquete Distribuible** (Para Compartir)

Crea un archivo `.tar.gz` con todo lo necesario para instalar en otros sistemas.

**Construcción:**
```bash
# Opción A: Usar el script de construcción
./build_package.sh

# Opción B: Usar Makefile
make package
```

**Resultado:**
- `dist/manjaro-vm-panel-1.0.0.tar.gz` - Paquete comprimido
- `dist/manjaro-vm-panel-1.0.0.tar.gz.sha256` - Checksum

**Distribución:**
```bash
# Compartir el archivo tar.gz
# El usuario lo instala así:
tar -xzf manjaro-vm-panel-1.0.0.tar.gz
cd manjaro-vm-panel-1.0.0
./INSTALL.sh
```

---

### 3. **Instalación con pip** (Estilo Python)

Instala como un paquete Python usando `setup.py`.

**Instalación:**
```bash
# Instalar en modo usuario
pip install --user .

# O instalar en el sistema (requiere sudo)
sudo pip install .

# Ejecutar
manjaro-vm-panel
```

**Desinstalación:**
```bash
pip uninstall manjaro-vm-panel
```

---

### 4. **Paquete Arch/Manjaro** (PKGBUILD)

Crea un paquete nativo de Arch Linux usando `makepkg`.

**Construcción:**
```bash
# 1. Primero crea el tarball fuente
./build_package.sh

# 2. Copia el tarball al directorio con PKGBUILD
cp dist/manjaro-vm-panel-1.0.0.tar.gz .

# 3. Construye el paquete
makepkg -si
```

**Instalación:**
```bash
# Instalar el paquete generado
sudo pacman -U manjaro-vm-panel-1.0.0-1-any.pkg.tar.zst
```

**Desinstalación:**
```bash
sudo pacman -R manjaro-vm-panel
```

---

### 5. **Instalación con Makefile** (Estilo Unix)

Usa el Makefile para instalar en el sistema.

**Comandos:**
```bash
# Ver ayuda
make help

# Instalar en /usr/local
sudo make install

# Desinstalar
sudo make uninstall

# Ejecutar sin instalar
make run

# Verificar dependencias
make test

# Limpiar archivos temporales
make clean
```

---

## 🔧 Comparación de Métodos

| Método | Facilidad | Portabilidad | Actualización | Desinstalación |
|--------|-----------|--------------|---------------|----------------|
| **Standalone** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Tarball** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **pip** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **PKGBUILD** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Makefile** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 📝 Recomendaciones por Caso de Uso

### Para Desarrollo y Testing
```bash
./manjaro-vm-panel
```
✅ Rápido, sin instalación, fácil de modificar

### Para Uso Personal
```bash
sudo ln -s $(pwd)/manjaro-vm-panel /usr/local/bin/manjaro-vm-panel
```
✅ Acceso global, fácil de actualizar

### Para Distribuir a Otros
```bash
./build_package.sh
# Comparte: dist/manjaro-vm-panel-1.0.0.tar.gz
```
✅ Incluye instalador automático

### Para Repositorio AUR (Arch User Repository)
```bash
makepkg -si
```
✅ Integración completa con pacman

### Para Instalación Tradicional Unix
```bash
sudo make install
```
✅ Ubicaciones estándar del sistema

---

## 🛠️ Requisitos Previos

Antes de usar cualquier método, asegúrate de tener:

```bash
# Dependencias del sistema
sudo pacman -S python-gobject gtk4 libadwaita python-pip libvirt qemu

# Dependencias Python
pip install --user -r requirements.txt

# Permisos
sudo usermod -a -G libvirt $USER
sudo systemctl enable --now libvirtd

# Reiniciar sesión para aplicar permisos
```

---

## 🐛 Solución de Problemas

### Error: "No module named 'gi'"
```bash
sudo pacman -S python-gobject gtk4 libadwaita
```

### Error: "Permission denied" al ejecutar virsh
```bash
sudo usermod -a -G libvirt $USER
# Cierra sesión y vuelve a entrar
```

### Error: "Failed to connect to libvirtd"
```bash
sudo systemctl start libvirtd
sudo systemctl enable libvirtd
```

### El ejecutable no se encuentra
```bash
# Verifica que sea ejecutable
chmod +x manjaro-vm-panel

# O usa Python directamente
python3 manjaro-vm-panel
```

---

## 📊 Estructura de Archivos Generados

```
dist/
├── manjaro-vm-panel-1.0.0/
│   ├── manjaro-vm-panel          # Ejecutable principal
│   ├── main.py                   # Módulos Python
│   ├── vm_manager.py
│   ├── ui.py
│   ├── notifications.py
│   ├── widgets.py
│   ├── style.css                 # Estilos
│   ├── requirements.txt          # Dependencias
│   ├── INSTALL.sh                # Instalador automático
│   ├── INSTALACION.txt           # Guía de instalación
│   ├── README.md                 # Documentación
│   └── LICENSE                   # Licencia MIT
├── manjaro-vm-panel-1.0.0.tar.gz       # Paquete comprimido
└── manjaro-vm-panel-1.0.0.tar.gz.sha256 # Checksum
```

---

## 🎯 Inicio Rápido

**Para empezar ahora mismo:**

```bash
# 1. Hacer ejecutable
chmod +x manjaro-vm-panel

# 2. Ejecutar
./manjaro-vm-panel
```

**Para instalación permanente:**

```bash
# Opción más simple
sudo ln -s $(pwd)/manjaro-vm-panel /usr/local/bin/manjaro-vm-panel

# Ahora puedes ejecutar desde cualquier lugar
manjaro-vm-panel
```

---

## 📞 Soporte

- **Documentación completa**: `README.md`
- **Configuración manual**: `CONFIGURACION_MANUAL.md`
- **Historial de cambios**: `CHANGELOG_ERRORES.md`
- **Comandos virsh**: `comando.md`

---

## 📄 Licencia

MIT License - Ver archivo `LICENSE` para más detalles.
