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

    def handle_vm_operation_error(self, vm_name, operation, error_info):
        """Maneja errores específicos de operaciones de VM

        Args:
            vm_name: Nombre de la VM
            operation: Tipo de operación (start, shutdown, etc)
            error_info: Dict con 'type', 'message', 'suggestion' o string simple
        """
        # Compatibilidad con mensajes string simples
        if isinstance(error_info, str):
            error_info = {
                "type": "unknown",
                "message": error_info,
                "suggestion": ""
            }

        error_type = error_info.get("type", "unknown")
        message = error_info.get("message", "Error desconocido")
        suggestion = error_info.get("suggestion", "")

        # Mapeo de operaciones a verbos en español
        operation_names = {
            'start': 'iniciar',
            'shutdown': 'apagar',
            'reboot': 'reiniciar',
            'destroy': 'forzar el apagado de',
            'save': 'guardar el estado de',
            'restore': 'restaurar'
        }

        operation_verb = operation_names.get(operation, operation)

        # Construir mensaje completo según el tipo de error
        if error_type == "not_found":
            full_message = f"{message}"
            if suggestion:
                full_message += f"\n💡 {suggestion}"

        elif error_type == "permission":
            full_message = f"No se pudo {operation_verb} '{vm_name}': {message}"
            if suggestion:
                full_message += f"\n💡 {suggestion}"

        elif error_type == "connection":
            full_message = f"Error de conexión: {message}"
            if suggestion:
                full_message += f"\n💡 {suggestion}"

        elif error_type == "already_running":
            full_message = f"{message}"
            # No mostrar como error, sino como advertencia
            self.notification_manager.show_warning(full_message)
            return

        elif error_type == "not_running":
            full_message = f"{message}"
            if suggestion:
                full_message += f"\n💡 {suggestion}"
            # Mostrar como advertencia en vez de error
            self.notification_manager.show_warning(full_message)
            return

        elif error_type == "network":
            full_message = f"Error de red al {operation_verb} '{vm_name}': {message}"
            if suggestion:
                full_message += f"\n💡 {suggestion}"

        elif error_type == "resources":
            full_message = f"Recursos insuficientes para {operation_verb} '{vm_name}': {message}"
            if suggestion:
                full_message += f"\n💡 {suggestion}"

        else:
            # Error genérico
            full_message = f"No se pudo {operation_verb} '{vm_name}'"
            if message and message != "Error desconocido":
                full_message += f": {message}"
            if suggestion:
                full_message += f"\n💡 {suggestion}"

        # Mostrar error con logging detallado
        logger.error(f"[{error_type.upper()}] {operation} en {vm_name}: {message}")
        self.notification_manager.show_error(full_message)
    
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