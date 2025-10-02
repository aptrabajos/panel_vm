# Mejoras en Manejo de Errores - Panel VM

## Fecha: 2025-10-01

### Cambios Implementados

#### 1. **vm_manager.py** - Sistema de errores estructurado

- ✅ Creada clase `VMError` para excepciones personalizadas
- ✅ Modificado `_run_virsh_command()` para retornar `(success, stdout, stderr)`
- ✅ Agregado `_parse_virsh_error()` que analiza errores y retorna info estructurada:
  - `type`: Tipo de error (connection, permission, not_found, etc.)
  - `message`: Mensaje descriptivo para el usuario
  - `suggestion`: Sugerencia de solución
- ✅ Agregadas validaciones previas en todas las operaciones:
  - `_validate_vm_exists()`: Verifica que la VM exista antes de operar
  - `_validate_vm_running()`: Verifica que la VM esté corriendo
- ✅ Todas las operaciones ahora retornan `Tuple[bool, Optional[Dict]]`:
  - `start_vm()` - Valida existencia y que no esté corriendo
  - `shutdown_vm()` - Valida que esté corriendo
  - `reboot_vm()` - Valida que esté corriendo
  - `destroy_vm()` - Valida que esté corriendo
  - `save_vm()` - Valida que esté corriendo
  - `remove_saved_state()`
- ✅ Logging mejorado con niveles apropiados (error, warning, info, debug)

#### 2. **notifications.py** - Mensajes contextualizados

- ✅ Mejorado `ErrorHandler.handle_vm_operation_error()`:
  - Acepta dict estructurado o string simple (compatibilidad)
  - Genera mensajes específicos según tipo de error
  - Usa advertencias (warning) para errores de estado (not_running, already_running)
  - Usa errores (error) para problemas críticos
  - Incluye sugerencias con emoji 💡
- ✅ Mejorado `NotificationManager.show_error()`:
  - Muestra solo primera línea en toast si hay múltiples líneas
  - Mensaje completo en notificación del sistema
  - Timeout extendido a 7 segundos
  - Prefijo ❌ para errores
- ✅ Mejorado `show_warning()`:
  - Prefijo ⚠️ para advertencias
  - Timeout de 5 segundos
  - Soporte para mensajes multilínea
- ✅ Mejorado `show_success()`:
  - Prefijo ✓ para éxitos

#### 3. **ui.py** - Integración con nuevo sistema

- ✅ Modificado `execute_vm_action()`:
  - Maneja tuplas `(success, error_info)` retornadas por vm_manager
  - Compatibilidad con funciones que retornan solo bool
  - Pasa `error_info` completo al ErrorHandler
  - Captura excepciones y las formatea como error_info
  - Reducido sleep a 0.5s para mejor respuesta
- ✅ Actualizados mensajes de éxito en todos los botones
- ✅ Mejorado diálogo de confirmación de destroy con advertencia de pérdida de datos

### Tipos de Errores Detectados

El sistema ahora detecta y maneja específicamente:

1. **connection** - No se puede conectar a libvirtd
   - Sugerencia: `sudo systemctl start libvirtd`

2. **permission** - Permisos insuficientes
   - Sugerencia: `sudo usermod -a -G libvirt $USER` + reiniciar sesión

3. **not_found** - VM no existe
   - Sugerencia: Verificar con `virsh list --all`

4. **already_running** - VM ya está en ejecución
   - Muestra advertencia, no error

5. **not_running** - VM no está corriendo
   - Muestra advertencia con sugerencia de iniciarla

6. **network** - Error de configuración de red

7. **resources** - Recursos insuficientes (espacio, RAM)

8. **exception** - Excepciones inesperadas de Python
   - Sugerencia: Revisar logs

### Ejemplo de Flujo Mejorado

#### Antes:
```
Usuario: Intenta apagar VM que no está corriendo
Sistema: "Error apagando VM manjaro1: domain is not running"
```

#### Ahora:
```
Usuario: Intenta apagar VM que no está corriendo
Sistema: ⚠️ La VM 'manjaro1' no está en ejecución
        💡 No se puede apagar una VM que no está corriendo
```

### Compatibilidad

- ✅ 100% compatible con código existente
- ✅ Funciones pueden retornar bool o tupla (detección automática)
- ✅ ErrorHandler acepta string o dict

### Testing

- ✅ Compilación sin errores de sintaxis
- ⏳ Pendiente: Pruebas con VMs reales en ejecución

### Próximos Pasos Sugeridos

1. Probar con VMs reales todos los escenarios de error
2. Agregar timeout configurable para operaciones
3. Agregar retry automático para errores transitorios
4. Mejorar manejo de errores de red específicos
5. Agregar telemetría de errores para debugging
