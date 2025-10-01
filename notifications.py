import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
import subprocess
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, window):
        self.window = window
        self.toast_overlay = None
        self.setup_toast_overlay()
    
    def setup_toast_overlay(self):
        """Configura el overlay para las notificaciones toast"""
        # Buscar el ToastOverlay en la ventana
        content = self.window.get_content()
        if isinstance(content, Adw.ToastOverlay):
            self.toast_overlay = content
        else:
            # Crear un nuevo ToastOverlay si no existe
            self.toast_overlay = Adw.ToastOverlay()
            self.toast_overlay.set_child(content)
            self.window.set_content(self.toast_overlay)
    
    def show_success(self, message, timeout=3):
        """Muestra una notificación de éxito"""
        if self.toast_overlay:
            toast = Adw.Toast.new(message)
            toast.set_timeout(timeout)
            self.toast_overlay.add_toast(toast)
        
        # También mostrar en logs
        logger.info(f"Éxito: {message}")
        
        # Intentar mostrar notificación del sistema
        self._send_system_notification("VM Panel - Éxito", message, "dialog-information")
    
    def show_error(self, message, detailed_error=None, timeout=5):
        """Muestra una notificación de error"""
        if self.toast_overlay:
            toast = Adw.Toast.new(f"Error: {message}")
            toast.set_timeout(timeout)
            self.toast_overlay.add_toast(toast)
        
        # Log del error con detalles
        if detailed_error:
            logger.error(f"Error: {message} - Detalles: {detailed_error}")
        else:
            logger.error(f"Error: {message}")
        
        # Intentar mostrar notificación del sistema
        self._send_system_notification("VM Panel - Error", message, "dialog-error")
    
    def show_warning(self, message, timeout=4):
        """Muestra una notificación de advertencia"""
        if self.toast_overlay:
            toast = Adw.Toast.new(f"Advertencia: {message}")
            toast.set_timeout(timeout)
            self.toast_overlay.add_toast(toast)
        
        logger.warning(f"Advertencia: {message}")
        
        # Intentar mostrar notificación del sistema
        self._send_system_notification("VM Panel - Advertencia", message, "dialog-warning")
    
    def show_info(self, message, timeout=3):
        """Muestra una notificación informativa"""
        if self.toast_overlay:
            toast = Adw.Toast.new(message)
            toast.set_timeout(timeout)
            self.toast_overlay.add_toast(toast)
        
        logger.info(f"Info: {message}")
    
    def _send_system_notification(self, title, message, icon="dialog-information"):
        """Envía una notificación del sistema usando notify-send"""
        try:
            subprocess.run([
                'notify-send',
                '--icon', icon,
                '--app-name', 'Panel de VMs Manjaro',
                title,
                message
            ], timeout=5, check=False)
        except Exception as e:
            logger.debug(f"No se pudo enviar notificación del sistema: {e}")
    
    def show_confirmation_dialog(self, title, message, callback):
        """Muestra un diálogo de confirmación"""
        dialog = Adw.MessageDialog.new(self.window, title, message)
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("confirm", "Confirmar")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            if response == "confirm":
                callback()
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()


class ErrorHandler:
    """Manejador centralizado de errores para el panel de VMs"""
    
    def __init__(self, notification_manager):
        self.notification_manager = notification_manager
    
    def handle_vm_operation_error(self, vm_name, operation, error_message):
        """Maneja errores específicos de operaciones de VM"""
        error_messages = {
            'start': f"No se pudo iniciar la VM {vm_name}",
            'shutdown': f"No se pudo apagar la VM {vm_name}",
            'reboot': f"No se pudo reiniciar la VM {vm_name}",
            'destroy': f"No se pudo forzar el apagado de la VM {vm_name}",
            'save': f"No se pudo guardar el estado de la VM {vm_name}",
            'restore': f"No se pudo restaurar la VM {vm_name}"
        }
        
        user_message = error_messages.get(operation, f"Error en operación '{operation}' para {vm_name}")
        
        # Analizar el error para dar mensajes más específicos
        if "not found" in error_message.lower():
            user_message += " - VM no encontrada"
        elif "permission denied" in error_message.lower():
            user_message += " - Permisos insuficientes"
        elif "already running" in error_message.lower():
            user_message += " - La VM ya está en ejecución"
        elif "not running" in error_message.lower():
            user_message += " - La VM no está en ejecución"
        
        self.notification_manager.show_error(user_message, error_message)
    
    def handle_connection_error(self, error_message):
        """Maneja errores de conexión con libvirt"""
        if "permission denied" in error_message.lower():
            self.notification_manager.show_error(
                "Sin permisos para acceder a libvirt",
                "Ejecuta: sudo usermod -a -G libvirt $USER y reinicia la sesión"
            )
        elif "failed to connect" in error_message.lower():
            self.notification_manager.show_error(
                "No se pudo conectar al servicio de virtualización",
                "Verifica que libvirtd esté ejecutándose: sudo systemctl start libvirtd"
            )
        else:
            self.notification_manager.show_error(
                "Error de conexión con el sistema de virtualización",
                error_message
            )
    
    def handle_sudo_error(self, error_message):
        """Maneja errores relacionados con sudo"""
        if "sudo" in error_message.lower():
            self.notification_manager.show_error(
                "Error de permisos administrativos",
                "Se requieren permisos de administrador para esta operación"
            )
        else:
            self.notification_manager.show_error("Error de permisos", error_message)