import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio
from vm_manager import VMManager
from notifications import NotificationManager, ErrorHandler
import threading
import time
import os

class VMCard(Gtk.Box):
    def __init__(self, vm_name, vm_manager, notification_manager=None, error_handler=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.vm_name = vm_name
        self.vm_manager = vm_manager
        self.notification_manager = notification_manager
        self.error_handler = error_handler
        self.is_updating = False
        
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        # Crear el contenedor principal de la tarjeta
        self.card = Gtk.Frame()
        self.card.set_css_classes(['card', 'vm-card'])
        
        # Contenedor interno
        card_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card_content.set_margin_top(16)
        card_content.set_margin_bottom(16)
        card_content.set_margin_start(16)
        card_content.set_margin_end(16)
        
        # Header con nombre y estado
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Nombre de la VM
        self.vm_title = Gtk.Label()
        self.vm_title.set_markup(f"<b>{vm_name}</b>")
        self.vm_title.set_halign(Gtk.Align.START)
        
        # Indicador de estado
        self.status_indicator = Gtk.Box()
        self.status_label = Gtk.Label()
        self.status_label.set_css_classes(['caption'])
        
        # Spinner para cuando esté actualizando
        self.spinner = Gtk.Spinner()
        self.spinner.set_visible(False)
        
        header_box.append(self.vm_title)
        header_box.append(Gtk.Box())  # Espaciador
        header_box.append(self.spinner)
        header_box.append(self.status_label)
        
        # Información adicional
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.cpu_label = Gtk.Label()
        self.memory_label = Gtk.Label()
        self.cpu_label.set_css_classes(['caption'])
        self.memory_label.set_css_classes(['caption'])
        self.cpu_label.set_halign(Gtk.Align.START)
        self.memory_label.set_halign(Gtk.Align.START)
        
        self.info_box.append(self.cpu_label)
        self.info_box.append(self.memory_label)
        
        # Botones de control
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.start_btn = Gtk.Button.new_with_label("Iniciar")
        self.start_btn.set_css_classes(['vm-control-button', 'start-button'])
        self.start_btn.connect('clicked', self.on_start_clicked)
        
        self.shutdown_btn = Gtk.Button.new_with_label("Apagar")
        self.shutdown_btn.set_css_classes(['vm-control-button', 'stop-button'])
        self.shutdown_btn.connect('clicked', self.on_shutdown_clicked)
        
        self.reboot_btn = Gtk.Button.new_with_label("Reiniciar")
        self.reboot_btn.set_css_classes(['vm-control-button', 'restart-button'])
        self.reboot_btn.connect('clicked', self.on_reboot_clicked)
        
        self.save_btn = Gtk.Button.new_with_label("Pausar")
        self.save_btn.set_css_classes(['vm-control-button', 'pause-button'])
        self.save_btn.connect('clicked', self.on_save_clicked)
        
        self.destroy_btn = Gtk.Button.new_with_label("Forzar")
        self.destroy_btn.set_css_classes(['vm-control-button', 'stop-button'])
        self.destroy_btn.connect('clicked', self.on_destroy_clicked)
        
        button_box.append(self.start_btn)
        button_box.append(self.shutdown_btn)
        button_box.append(self.reboot_btn)
        button_box.append(self.save_btn)
        button_box.append(self.destroy_btn)
        
        # Ensamblar la tarjeta
        card_content.append(header_box)
        card_content.append(Gtk.Separator())
        card_content.append(self.info_box)
        card_content.append(button_box)
        
        self.card.set_child(card_content)
        self.append(self.card)
        
        # Actualizar estado inicial
        self.update_vm_status()
    
    def set_loading(self, loading):
        """Muestra/oculta el spinner de carga"""
        self.is_updating = loading
        self.spinner.set_visible(loading)
        if loading:
            self.spinner.start()
        else:
            self.spinner.stop()
        
        # Deshabilitar botones durante operaciones
        self.start_btn.set_sensitive(not loading)
        self.shutdown_btn.set_sensitive(not loading)
        self.reboot_btn.set_sensitive(not loading)
        self.save_btn.set_sensitive(not loading)
        self.destroy_btn.set_sensitive(not loading)
    
    def update_vm_status(self):
        """Actualiza el estado de la VM"""
        vms = self.vm_manager.list_all_vms()
        vm_info = next((vm for vm in vms if vm['name'] == self.vm_name), None)
        
        if vm_info:
            state = vm_info['state']
            running = vm_info['running']
            
            # Actualizar label de estado
            if running:
                self.status_label.set_markup('<span color="#26a269">● En ejecución</span>')
                self.start_btn.set_visible(False)
                self.shutdown_btn.set_visible(True)
                self.reboot_btn.set_visible(True)
                self.save_btn.set_visible(True)
            elif state == 'shut off':
                self.status_label.set_markup('<span color="#c01c28">● Apagada</span>')
                self.start_btn.set_visible(True)
                self.shutdown_btn.set_visible(False)
                self.reboot_btn.set_visible(False)
                self.save_btn.set_visible(False)
            else:
                self.status_label.set_markup(f'<span color="#f57c00">● {state}</span>')
                self.start_btn.set_visible(True)
                self.shutdown_btn.set_visible(False)
                self.reboot_btn.set_visible(False)
                self.save_btn.set_visible(False)
            
            # Obtener estadísticas si está corriendo
            if running:
                stats = self.vm_manager.get_vm_stats(self.vm_name)
                if stats:
                    cpu_time = stats.get('cpu_time', 'N/A')
                    memory_used = stats.get('memory_used', 'N/A')
                    self.cpu_label.set_text(f"CPU Time: {cpu_time}")
                    self.memory_label.set_text(f"Memoria: {memory_used} KB")
                else:
                    self.cpu_label.set_text("CPU: Información no disponible")
                    self.memory_label.set_text("Memoria: Información no disponible")
            else:
                self.cpu_label.set_text("CPU: VM apagada")
                self.memory_label.set_text("Memoria: VM apagada")
    
    def execute_vm_action(self, action_func, success_message, operation_name):
        """Ejecuta una acción de VM en un hilo separado"""
        def run_action():
            GLib.idle_add(self.set_loading, True)
            
            try:
                success = action_func(self.vm_name)
                time.sleep(1)  # Pequeña pausa para que se vea la operación
                
                GLib.idle_add(self.set_loading, False)
                GLib.idle_add(self.update_vm_status)
                
                if success:
                    if self.notification_manager:
                        GLib.idle_add(self.notification_manager.show_success, 
                                    f"{success_message} para {self.vm_name}")
                else:
                    if self.error_handler:
                        GLib.idle_add(self.error_handler.handle_vm_operation_error,
                                    self.vm_name, operation_name, "Operación falló")
            except Exception as e:
                GLib.idle_add(self.set_loading, False)
                if self.error_handler:
                    GLib.idle_add(self.error_handler.handle_vm_operation_error,
                                self.vm_name, operation_name, str(e))
        
        thread = threading.Thread(target=run_action)
        thread.daemon = True
        thread.start()
    
    def on_start_clicked(self, button):
        self.execute_vm_action(self.vm_manager.start_vm, "VM iniciada", "start")
    
    def on_shutdown_clicked(self, button):
        self.execute_vm_action(self.vm_manager.shutdown_vm, "VM apagándose", "shutdown")
    
    def on_reboot_clicked(self, button):
        self.execute_vm_action(self.vm_manager.reboot_vm, "VM reiniciándose", "reboot")
    
    def on_save_clicked(self, button):
        self.execute_vm_action(self.vm_manager.save_vm, "Estado de VM guardado", "save")
    
    def on_destroy_clicked(self, button):
        if self.notification_manager:
            self.notification_manager.show_confirmation_dialog(
                "Confirmar acción destructiva",
                f"¿Estás seguro de que quieres forzar el apagado de {self.vm_name}?",
                lambda: self.execute_vm_action(self.vm_manager.destroy_vm, "VM forzadamente apagada", "destroy")
            )
        else:
            self.execute_vm_action(self.vm_manager.destroy_vm, "VM forzadamente apagada", "destroy")


class VMPanelWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.vm_manager = VMManager()
        self.vm_cards = {}
        
        # Cargar estilos CSS
        self.load_css()
        
        # Configuración de la ventana
        self.set_title("Panel de Máquinas Virtuales")
        self.set_default_size(800, 600)
        self.set_size_request(600, 400)
        
        # Configurar sistema de notificaciones después de crear el contenido
        self.notification_manager = None
        self.error_handler = None
        
        # Header bar con AdwHeaderBar para AdwApplicationWindow
        
        # Crear contenido principal
        self.create_main_content()
        
        # Configurar actualización automática
        self.setup_auto_update()
    
    def create_main_content(self):
        """Crea el contenido principal de la ventana"""
        # Crear ToastOverlay para notificaciones
        toast_overlay = Adw.ToastOverlay()
        
        # Crear ToolbarView que incluye header y contenido
        toolbar_view = Adw.ToolbarView()
        
        # Header bar
        header = Adw.HeaderBar()
        
        # Botón de actualizar en el header
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        refresh_btn.set_tooltip_text("Actualizar estado de VMs")
        refresh_btn.connect('clicked', self.on_refresh_clicked)
        header.pack_end(refresh_btn)
        
        # Añadir header al toolbar view
        toolbar_view.add_top_bar(header)
        
        # Contenedor principal con scroll
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        
        # Título
        title_label = Gtk.Label()
        title_label.set_markup('<span size="x-large" weight="bold">Panel de Control - Máquinas Virtuales</span>')
        title_label.set_halign(Gtk.Align.START)
        main_box.append(title_label)
        
        # Descripción
        desc_label = Gtk.Label()
        desc_label.set_text("Administra el estado de tus máquinas virtuales Manjaro")
        desc_label.set_css_classes(['dim-label'])
        desc_label.set_halign(Gtk.Align.START)
        main_box.append(desc_label)
        
        # Contenedor para las tarjetas de VMs
        self.vms_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Crear tarjetas para cada VM
        for vm_name in self.vm_manager.vm_names:
            vm_card = VMCard(vm_name, self.vm_manager, self.notification_manager, self.error_handler)
            self.vm_cards[vm_name] = vm_card
            self.vms_box.append(vm_card)
        
        main_box.append(self.vms_box)
        
        scroll.set_child(main_box)
        toolbar_view.set_content(scroll)
        toast_overlay.set_child(toolbar_view)
        self.set_content(toast_overlay)
        
        # Configurar sistema de notificaciones ahora que el contenido está creado
        self.notification_manager = NotificationManager(self)
        self.error_handler = ErrorHandler(self.notification_manager)
        
        # Actualizar las VMCards con los managers
        for vm_card in self.vm_cards.values():
            vm_card.notification_manager = self.notification_manager
            vm_card.error_handler = self.error_handler
    
    def setup_auto_update(self):
        """Configura la actualización automática cada 5 segundos"""
        def auto_update():
            for vm_card in self.vm_cards.values():
                if not vm_card.is_updating:
                    vm_card.update_vm_status()
            return True  # Continuar el timer
        
        GLib.timeout_add_seconds(5, auto_update)
    
    def on_refresh_clicked(self, button):
        """Maneja el clic del botón de actualizar"""
        for vm_card in self.vm_cards.values():
            vm_card.update_vm_status()
    
    def load_css(self):
        """Carga los estilos CSS personalizados"""
        css_provider = Gtk.CssProvider()
        css_file = os.path.join(os.path.dirname(__file__), 'style.css')
        
        if os.path.exists(css_file):
            css_provider.load_from_path(css_file)
            Gtk.StyleContext.add_provider_for_display(
                self.get_display(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )