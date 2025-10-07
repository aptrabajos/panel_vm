import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio
from vm_manager import VMManager
from notifications import NotificationManager, ErrorHandler
from widgets import CircularProgressWidget, MiniLineChartWidget, DiskUsageBarWidget
import threading
import time
import os
from collections import deque

class VMCard(Gtk.Box):
    def __init__(self, vm_name, vm_manager, notification_manager=None, error_handler=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.vm_name = vm_name
        self.vm_manager = vm_manager
        self.notification_manager = notification_manager
        self.error_handler = error_handler
        self.is_updating = False

        # Historial para gráficos
        self.cpu_history = deque(maxlen=30)
        self.memory_history = deque(maxlen=30)
        self.net_rx_history = deque(maxlen=30)
        self.net_tx_history = deque(maxlen=30)

        # Tracking para cálculo de CPU usage
        self.last_cpu_time = None
        self.last_update_time = None

        # Tracking para cálculo de red y disco (deltas)
        self.last_net_rx_bytes = None
        self.last_net_tx_bytes = None
        self.last_block_read_bytes = None
        self.last_block_write_bytes = None
        self.last_block_read_reqs = None
        self.last_block_write_reqs = None
        
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
        
        # Información básica
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.cpu_label = Gtk.Label()
        self.memory_label = Gtk.Label()
        self.ip_label = Gtk.Label()
        self.uptime_label = Gtk.Label()
        self.cpu_label.set_css_classes(['caption'])
        self.memory_label.set_css_classes(['caption'])
        self.ip_label.set_css_classes(['caption'])
        self.uptime_label.set_css_classes(['caption'])
        self.cpu_label.set_halign(Gtk.Align.START)
        self.memory_label.set_halign(Gtk.Align.START)
        self.ip_label.set_halign(Gtk.Align.START)
        self.uptime_label.set_halign(Gtk.Align.START)

        self.info_box.append(self.cpu_label)
        self.info_box.append(self.memory_label)
        self.info_box.append(self.ip_label)
        self.info_box.append(self.uptime_label)

        # Expander para detalles avanzados
        self.details_expander = Gtk.Expander()
        self.details_expander.set_label("📊 Ver detalles avanzados")

        # Contenedor de detalles con TabView
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        details_box.set_margin_top(12)

        # === QUICK STATS EN GRID (mantener en la parte superior) ===
        quick_stats_grid = Gtk.Grid()
        quick_stats_grid.set_row_spacing(12)
        quick_stats_grid.set_column_spacing(12)
        quick_stats_grid.set_column_homogeneous(True)

        # Gráficos circulares compactos
        self.cpu_circular = CircularProgressWidget(size=100)
        self.cpu_circular.set_value(0, "0%", "CPU")
        quick_stats_grid.attach(self.cpu_circular, 0, 0, 1, 1)

        self.memory_circular = CircularProgressWidget(size=100)
        self.memory_circular.set_value(0, "0%", "RAM")
        quick_stats_grid.attach(self.memory_circular, 1, 0, 1, 1)

        # Mini card de disco
        disk_mini_card = Gtk.Frame()
        disk_mini_card.set_css_classes(['card', 'mini-stat'])
        disk_mini_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        disk_mini_box.set_margin_top(8)
        disk_mini_box.set_margin_bottom(8)
        disk_mini_box.set_margin_start(8)
        disk_mini_box.set_margin_end(8)
        disk_mini_title = Gtk.Label()
        disk_mini_title.set_markup('<span size="small" weight="bold">💾 Disco</span>')
        self.disk_mini_value = Gtk.Label()
        self.disk_mini_value.set_markup('<span size="large">N/A</span>')
        disk_mini_box.append(disk_mini_title)
        disk_mini_box.append(self.disk_mini_value)
        disk_mini_card.set_child(disk_mini_box)
        quick_stats_grid.attach(disk_mini_card, 2, 0, 1, 1)

        # Mini card de red
        net_mini_card = Gtk.Frame()
        net_mini_card.set_css_classes(['card', 'mini-stat'])
        net_mini_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        net_mini_box.set_margin_top(8)
        net_mini_box.set_margin_bottom(8)
        net_mini_box.set_margin_start(8)
        net_mini_box.set_margin_end(8)
        net_mini_title = Gtk.Label()
        net_mini_title.set_markup('<span size="small" weight="bold">🌐 Red</span>')
        self.net_mini_value = Gtk.Label()
        self.net_mini_value.set_markup('<span size="large">N/A</span>')
        net_mini_box.append(net_mini_title)
        net_mini_box.append(self.net_mini_value)
        net_mini_card.set_child(net_mini_box)
        quick_stats_grid.attach(net_mini_card, 3, 0, 1, 1)

        details_box.append(quick_stats_grid)
        details_box.append(Gtk.Separator())

        # === TABVIEW para organizar contenido ===
        self.tab_view = Adw.TabView()
        self.tab_view.set_vexpand(True)

        # Tab Bar (pestañas superiores)
        tab_bar = Adw.TabBar()
        tab_bar.set_view(self.tab_view)
        details_box.append(tab_bar)
        details_box.append(self.tab_view)

        # === Crear tabs y agregar al TabView ===
        self._create_performance_tab()
        self._create_storage_tab()
        self._create_network_tab()
        self._create_system_tab()

        self.details_expander.set_child(details_box)
        
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

        self.viewer_btn = Gtk.Button.new_with_label("🖥️ Viewer")
        self.viewer_btn.set_css_classes(['vm-control-button', 'viewer-button'])
        self.viewer_btn.set_tooltip_text("Abrir consola gráfica de la VM")
        self.viewer_btn.connect('clicked', self.on_viewer_clicked)

        button_box.append(self.start_btn)
        button_box.append(self.shutdown_btn)
        button_box.append(self.reboot_btn)
        button_box.append(self.save_btn)
        button_box.append(self.destroy_btn)
        button_box.append(self.viewer_btn)
        
        # Ensamblar la tarjeta
        card_content.append(header_box)
        card_content.append(Gtk.Separator())
        card_content.append(self.info_box)
        card_content.append(self.details_expander)
        card_content.append(button_box)
        
        self.card.set_child(card_content)
        self.append(self.card)
        
        # Actualizar estado inicial
        self.update_vm_status()

    def _create_performance_tab(self):
        """Crea el tab de rendimiento con gráficos de CPU, RAM y Red"""
        perf_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        perf_box.set_margin_start(12)
        perf_box.set_margin_end(12)
        perf_box.set_margin_top(12)
        perf_box.set_margin_bottom(12)

        # Historial de gráficos
        charts_label = Gtk.Label()
        charts_label.set_markup('<span weight="bold" size="large">📈 Historial (últimos 2.5 min)</span>')
        charts_label.set_halign(Gtk.Align.START)
        perf_box.append(charts_label)
        perf_box.append(Gtk.Separator())

        # Gráficos de CPU y Memoria
        self.cpu_line_chart = MiniLineChartWidget(width=280, height=70)
        self.cpu_line_chart.set_title("CPU")
        self.cpu_line_chart.set_color(0.26, 0.59, 0.98)  # Azul
        perf_box.append(self.cpu_line_chart)

        self.memory_line_chart = MiniLineChartWidget(width=280, height=70)
        self.memory_line_chart.set_title("Memoria")
        self.memory_line_chart.set_color(0.61, 0.15, 0.69)  # Púrpura
        perf_box.append(self.memory_line_chart)

        # vCPUs info
        perf_box.append(Gtk.Separator())
        vcpu_label = Gtk.Label()
        vcpu_label.set_markup('<span weight="bold">⚙️ CPUs Virtuales</span>')
        vcpu_label.set_halign(Gtk.Align.START)
        self.vcpu_info_label = Gtk.Label()
        self.vcpu_info_label.set_css_classes(['caption'])
        self.vcpu_info_label.set_halign(Gtk.Align.START)
        perf_box.append(vcpu_label)
        perf_box.append(self.vcpu_info_label)

        # Agregar como tab
        tab_page = self.tab_view.append(perf_box)
        tab_page.set_title("📈 Rendimiento")
        tab_page.set_tooltip("CPU, Memoria y gráficos en tiempo real")

    def _create_storage_tab(self):
        """Crea el tab de almacenamiento con disco, IOPS y latencia"""
        storage_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        storage_box.set_margin_start(12)
        storage_box.set_margin_end(12)
        storage_box.set_margin_top(12)
        storage_box.set_margin_bottom(12)

        # Título
        disk_label = Gtk.Label()
        disk_label.set_markup('<span weight="bold" size="large">💾 Almacenamiento</span>')
        disk_label.set_halign(Gtk.Align.START)
        storage_box.append(disk_label)
        storage_box.append(Gtk.Separator())

        # Barra de uso de disco
        self.disk_usage_bar = DiskUsageBarWidget(width=280, height=30)
        self.disk_usage_bar.set_value(0, 0, 0)
        storage_box.append(self.disk_usage_bar)

        # Detalles de disco
        self.disk_detail_label = Gtk.Label()
        self.disk_iops_label = Gtk.Label()
        self.disk_latency_label = Gtk.Label()
        self.disk_detail_label.set_css_classes(['caption'])
        self.disk_iops_label.set_css_classes(['caption'])
        self.disk_latency_label.set_css_classes(['caption'])
        self.disk_detail_label.set_halign(Gtk.Align.START)
        self.disk_iops_label.set_halign(Gtk.Align.START)
        self.disk_latency_label.set_halign(Gtk.Align.START)
        storage_box.append(self.disk_detail_label)
        storage_box.append(self.disk_iops_label)
        storage_box.append(self.disk_latency_label)

        # Blkio weight
        storage_box.append(Gtk.Separator())
        blkio_title = Gtk.Label()
        blkio_title.set_markup('<span weight="bold">⚖️ Prioridad de I/O</span>')
        blkio_title.set_halign(Gtk.Align.START)
        self.blkio_label = Gtk.Label()
        self.blkio_label.set_css_classes(['caption'])
        self.blkio_label.set_halign(Gtk.Align.START)
        storage_box.append(blkio_title)
        storage_box.append(self.blkio_label)

        # Agregar como tab
        tab_page = self.tab_view.append(storage_box)
        tab_page.set_title("💾 Almacenamiento")
        tab_page.set_tooltip("Disco, IOPS, latencia y prioridad")

    def _create_network_tab(self):
        """Crea el tab de red con interfaces, tráfico y estadísticas"""
        net_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        net_box.set_margin_start(12)
        net_box.set_margin_end(12)
        net_box.set_margin_top(12)
        net_box.set_margin_bottom(12)

        # Título
        net_label = Gtk.Label()
        net_label.set_markup('<span weight="bold" size="large">🌐 Red (tiempo real)</span>')
        net_label.set_halign(Gtk.Align.START)
        net_box.append(net_label)
        net_box.append(Gtk.Separator())

        # Gráficos de red
        self.net_rx_chart = MiniLineChartWidget(width=280, height=70)
        self.net_rx_chart.set_title("⬇️ Descarga (MB/s)")
        self.net_rx_chart.set_color(0.26, 0.80, 0.41)  # Verde
        net_box.append(self.net_rx_chart)

        self.net_tx_chart = MiniLineChartWidget(width=280, height=70)
        self.net_tx_chart.set_title("⬆️ Subida (MB/s)")
        self.net_tx_chart.set_color(0.96, 0.61, 0.07)  # Naranja
        net_box.append(self.net_tx_chart)

        # Labels con totales
        self.net_rx_label = Gtk.Label()
        self.net_tx_label = Gtk.Label()
        self.net_rx_label.set_css_classes(['caption'])
        self.net_tx_label.set_css_classes(['caption'])
        self.net_rx_label.set_halign(Gtk.Align.START)
        self.net_tx_label.set_halign(Gtk.Align.START)
        net_box.append(self.net_rx_label)
        net_box.append(self.net_tx_label)

        # Interfaces de red
        net_box.append(Gtk.Separator())
        interfaces_title = Gtk.Label()
        interfaces_title.set_markup('<span weight="bold">🔌 Interfaces de Red</span>')
        interfaces_title.set_halign(Gtk.Align.START)
        self.net_interfaces_label = Gtk.Label()
        self.net_interfaces_label.set_css_classes(['caption'])
        self.net_interfaces_label.set_halign(Gtk.Align.START)
        self.net_interfaces_label.set_wrap(True)
        net_box.append(interfaces_title)
        net_box.append(self.net_interfaces_label)

        # Agregar como tab
        tab_page = self.tab_view.append(net_box)
        tab_page.set_title("🌐 Red")
        tab_page.set_tooltip("Interfaces, tráfico y estadísticas de red")

    def _create_system_tab(self):
        """Crea el tab de sistema con virtio, CPU features, hugepages, etc."""
        sys_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        sys_box.set_margin_start(12)
        sys_box.set_margin_end(12)
        sys_box.set_margin_top(12)
        sys_box.set_margin_bottom(12)

        # Título
        sys_label = Gtk.Label()
        sys_label.set_markup('<span weight="bold" size="large">⚙️ Configuración del Sistema</span>')
        sys_label.set_halign(Gtk.Align.START)
        sys_box.append(sys_label)
        sys_box.append(Gtk.Separator())

        # Drivers Virtio
        virtio_title = Gtk.Label()
        virtio_title.set_markup('<span weight="bold">⚡ Drivers Virtio</span>')
        virtio_title.set_halign(Gtk.Align.START)
        self.virtio_drivers_label = Gtk.Label()
        self.virtio_drivers_label.set_css_classes(['caption'])
        self.virtio_drivers_label.set_halign(Gtk.Align.START)
        sys_box.append(virtio_title)
        sys_box.append(self.virtio_drivers_label)

        sys_box.append(Gtk.Separator())

        # CPU Features
        cpu_features_title = Gtk.Label()
        cpu_features_title.set_markup('<span weight="bold">🔧 CPU Features</span>')
        cpu_features_title.set_halign(Gtk.Align.START)
        self.cpu_features_label = Gtk.Label()
        self.cpu_features_label.set_css_classes(['caption'])
        self.cpu_features_label.set_halign(Gtk.Align.START)
        self.cpu_features_label.set_wrap(True)
        sys_box.append(cpu_features_title)
        sys_box.append(self.cpu_features_label)

        sys_box.append(Gtk.Separator())

        # Hugepages
        hp_title = Gtk.Label()
        hp_title.set_markup('<span weight="bold">📄 Hugepages</span>')
        hp_title.set_halign(Gtk.Align.START)
        self.hugepages_label = Gtk.Label()
        self.hugepages_label.set_css_classes(['caption'])
        self.hugepages_label.set_halign(Gtk.Align.START)
        sys_box.append(hp_title)
        sys_box.append(self.hugepages_label)

        sys_box.append(Gtk.Separator())

        # Temperatura del host
        temp_title = Gtk.Label()
        temp_title.set_markup('<span weight="bold">🌡️ Temperatura del Host</span>')
        temp_title.set_halign(Gtk.Align.START)
        self.host_temp_label = Gtk.Label()
        self.host_temp_label.set_css_classes(['caption'])
        self.host_temp_label.set_halign(Gtk.Align.START)
        sys_box.append(temp_title)
        sys_box.append(self.host_temp_label)

        sys_box.append(Gtk.Separator())

        # Usuarios conectados
        users_title = Gtk.Label()
        users_title.set_markup('<span weight="bold">👥 Usuarios en el Guest</span>')
        users_title.set_halign(Gtk.Align.START)
        self.guest_users_label = Gtk.Label()
        self.guest_users_label.set_css_classes(['caption'])
        self.guest_users_label.set_halign(Gtk.Align.START)
        sys_box.append(users_title)
        sys_box.append(self.guest_users_label)

        # Agregar como tab
        tab_page = self.tab_view.append(sys_box)
        tab_page.set_title("⚙️ Sistema")
        tab_page.set_tooltip("Virtio, CPU features, hugepages y más")

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
            elif state in ['shut off', 'apagado', 'apagada']:
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
                # Obtener IP
                ip = self.vm_manager.get_vm_ip_address(self.vm_name)
                if ip:
                    self.ip_label.set_markup(f'<span>🌐 IP: <b>{ip}</b></span>')
                else:
                    self.ip_label.set_text("🌐 IP: Obteniendo...")

                # Obtener uptime
                uptime_seconds = self.vm_manager.get_vm_uptime(self.vm_name)
                if uptime_seconds:
                    hours = uptime_seconds // 3600
                    minutes = (uptime_seconds % 3600) // 60
                    if hours > 0:
                        self.uptime_label.set_text(f"⏰ Uptime: {hours}h {minutes}m")
                    else:
                        self.uptime_label.set_text(f"⏰ Uptime: {minutes}m")
                else:
                    self.uptime_label.set_text("⏰ Uptime: N/A")

                # Obtener estadísticas detalladas una sola vez
                detailed_stats = self.vm_manager.get_vm_detailed_stats(self.vm_name)
                if detailed_stats:
                    # CPU básico
                    cpu_time = detailed_stats.get('cpu_time')
                    vcpu_current = detailed_stats.get('vcpu_current', 0)
                    if cpu_time:
                        cpu_seconds = cpu_time / 1_000_000_000
                        cpu_hours = cpu_seconds / 3600
                        if cpu_hours >= 1:
                            self.cpu_label.set_text(f"⚙️ CPU: {vcpu_current} vCPUs | {cpu_hours:.1f}h")
                        else:
                            cpu_minutes = cpu_seconds / 60
                            self.cpu_label.set_text(f"⚙️ CPU: {vcpu_current} vCPUs | {cpu_minutes:.1f}m")
                    else:
                        self.cpu_label.set_text(f"⚙️ CPU: {vcpu_current} vCPUs activas")

                    # Memoria básica - usar datos consistentes de domstats
                    mem_actual = detailed_stats.get('memory_actual')  # Memoria asignada al balloon
                    mem_available = detailed_stats.get('memory_available')  # Memoria máxima configurada
                    mem_unused = detailed_stats.get('memory_unused')  # Memoria no usada dentro del guest
                    mem_rss = detailed_stats.get('memory_rss')  # Memoria RSS del host

                    if mem_actual and mem_unused is not None:
                        # Calcular memoria usada dentro del guest (más preciso)
                        used_kb = mem_actual - mem_unused
                        mem_gb_used = used_kb / (1024 * 1024)
                        mem_gb_total = mem_actual / (1024 * 1024)
                        mem_percent = (used_kb / mem_actual) * 100 if mem_actual > 0 else 0
                        self.memory_label.set_text(f"💾 Memoria: {mem_gb_used:.1f}/{mem_gb_total:.1f} GB ({mem_percent:.0f}%)")
                    elif mem_actual and mem_rss:
                        # Usar RSS como aproximación del uso real
                        mem_gb_actual = mem_actual / (1024 * 1024)
                        mem_gb_rss = mem_rss / (1024 * 1024)
                        mem_percent = (mem_rss / mem_actual) * 100 if mem_actual > 0 else 0
                        self.memory_label.set_text(f"💾 Memoria: {mem_gb_rss:.1f}/{mem_gb_actual:.1f} GB ({mem_percent:.0f}%)")
                    elif mem_actual:
                        # Fallback: solo memoria asignada
                        mem_gb_actual = mem_actual / (1024 * 1024)
                        self.memory_label.set_text(f"💾 Memoria: {mem_gb_actual:.1f} GB (Asignada)")
                    else:
                        self.memory_label.set_text("💾 Memoria: N/A")

                    # Actualizar detalles expandibles
                    self._update_detailed_stats(detailed_stats)
                else:
                    self.cpu_label.set_text("⚙️ CPU: Información no disponible")
                    self.memory_label.set_text("💾 Memoria: Información no disponible")
                    self._clear_detailed_stats()

                self.details_expander.set_visible(True)
            else:
                self.cpu_label.set_text("⚙️ CPU: VM apagada")
                self.memory_label.set_text("💾 Memoria: VM apagada")
                self.ip_label.set_text("🌐 IP: N/A")
                self._clear_detailed_stats()
                self.details_expander.set_visible(False)

    def _update_detailed_stats(self, stats):
        """Actualiza las estadísticas detalladas con gráficos"""
        import time as time_module

        # Calcular porcentajes para gráficos circulares
        mem_actual = stats.get('memory_actual')
        mem_available = stats.get('memory_available')
        vcpu_count = stats.get('vcpu_count', 1)
        vcpu_current = stats.get('vcpu_current', 0)
        cpu_time = stats.get('cpu_time')  # En nanosegundos

        # Calcular % real de uso de CPU basado en tiempo
        cpu_percent = 0
        current_time = time_module.time()

        if cpu_time and self.last_cpu_time is not None and self.last_update_time is not None:
            # Delta de tiempo de CPU en nanosegundos
            cpu_time_delta = cpu_time - self.last_cpu_time
            # Delta de tiempo real en segundos
            real_time_delta = current_time - self.last_update_time

            # Convertir delta de CPU a segundos
            cpu_time_delta_seconds = cpu_time_delta / 1_000_000_000

            # Calcular porcentaje considerando todas las vCPUs
            # % = (tiempo_cpu_usado / (tiempo_real * num_vcpus)) * 100
            if real_time_delta > 0 and vcpu_count > 0:
                cpu_percent = (cpu_time_delta_seconds / (real_time_delta * vcpu_count)) * 100
                cpu_percent = max(0, min(100, cpu_percent))  # Limitar entre 0-100%

        # Guardar valores actuales para próxima iteración
        self.last_cpu_time = cpu_time
        self.last_update_time = current_time

        # Memoria: usar datos consistentes de domstats
        mem_percent = 0
        mem_label = ""
        mem_unused = stats.get('memory_unused')
        mem_rss = stats.get('memory_rss')

        if mem_actual and mem_unused is not None:
            # Calcular memoria usada dentro del guest (más preciso)
            used_kb = mem_actual - mem_unused
            mem_percent = (used_kb / mem_actual) * 100 if mem_actual > 0 else 0
            mem_gb_used = used_kb / (1024 * 1024)
            mem_gb_total = mem_actual / (1024 * 1024)
            mem_label = f"{mem_gb_used:.1f}/{mem_gb_total:.1f} GB"
        elif mem_actual and mem_rss:
            # Usar RSS como aproximación del uso real
            mem_percent = (mem_rss / mem_actual) * 100 if mem_actual > 0 else 0
            mem_gb_rss = mem_rss / (1024 * 1024)
            mem_gb_total = mem_actual / (1024 * 1024)
            mem_label = f"{mem_gb_rss:.1f}/{mem_gb_total:.1f} GB"
        elif mem_actual:
            # Fallback: mostrar memoria asignada
            mem_gb = mem_actual / (1024 * 1024)
            mem_percent = 50  # Valor fijo visual para gráfico
            mem_label = f"{mem_gb:.1f} GB (Asignada)"

        # Actualizar gráficos circulares
        self.cpu_circular.set_value(cpu_percent, f"{cpu_percent:.1f}%", "CPU")
        self.memory_circular.set_value(
            mem_percent,
            f"{mem_percent:.1f}%",
            "RAM Guest" if mem_unused is not None else ("RAM RSS" if mem_rss else "RAM Asignada")
        )

        # Agregar al historial
        self.cpu_line_chart.add_data_point(cpu_percent)
        self.memory_line_chart.add_data_point(mem_percent)

        # vCPUs con tiempo de CPU
        cpu_time = stats.get('cpu_time')
        if cpu_time:
            cpu_seconds = cpu_time / 1_000_000_000
            cpu_hours = cpu_seconds / 3600
            if cpu_hours >= 1:
                self.vcpu_info_label.set_text(f"Activas: {vcpu_current} / {vcpu_count} | Tiempo total: {cpu_hours:.1f}h")
            else:
                cpu_minutes = cpu_seconds / 60
                self.vcpu_info_label.set_text(f"Activas: {vcpu_current} / {vcpu_count} | Tiempo total: {cpu_minutes:.1f}m")
        else:
            self.vcpu_info_label.set_text(f"Activas: {vcpu_current} / {vcpu_count}")

        # === Calcular métricas de red en tiempo real (MB/s) ===
        rx_bytes = stats.get('net_rx_bytes', 0)
        tx_bytes = stats.get('net_tx_bytes', 0)

        net_rx_mbps = 0
        net_tx_mbps = 0

        if self.last_net_rx_bytes is not None and self.last_net_tx_bytes is not None and self.last_update_time is not None:
            time_delta = current_time - self.last_update_time
            if time_delta > 0:
                # Calcular MB/s
                rx_delta = rx_bytes - self.last_net_rx_bytes
                tx_delta = tx_bytes - self.last_net_tx_bytes
                net_rx_mbps = (rx_delta / time_delta) / (1024 * 1024)  # Convertir a MB/s
                net_tx_mbps = (tx_delta / time_delta) / (1024 * 1024)
                net_rx_mbps = max(0, net_rx_mbps)  # Evitar negativos
                net_tx_mbps = max(0, net_tx_mbps)

        self.last_net_rx_bytes = rx_bytes
        self.last_net_tx_bytes = tx_bytes

        # Agregar a historial de red (normalizar a 0-100 para gráficos, asumiendo max 100 MB/s)
        net_rx_percent = min(100, (net_rx_mbps / 100) * 100)
        net_tx_percent = min(100, (net_tx_mbps / 100) * 100)
        self.net_rx_chart.add_data_point(net_rx_percent)
        self.net_tx_chart.add_data_point(net_tx_percent)

        # Actualizar quick stat de red
        if net_rx_mbps > 0 or net_tx_mbps > 0:
            self.net_mini_value.set_markup(f'<span size="large" weight="bold">↓{net_rx_mbps:.1f} ↑{net_tx_mbps:.1f} MB/s</span>')
        else:
            self.net_mini_value.set_markup('<span size="large">0 MB/s</span>')

        # === Disco: calcular IOPS y latencia ===
        block_capacity = stats.get('block_capacity', 0)
        block_allocation = stats.get('block_allocation', 0)
        block_read_reqs = stats.get('block_read_reqs', 0)
        block_write_reqs = stats.get('block_write_reqs', 0)
        block_read_bytes = stats.get('block_read_bytes', 0)
        block_write_bytes = stats.get('block_write_bytes', 0)
        block_rd_times = stats.get('block_rd_total_times', 0)
        block_wr_times = stats.get('block_wr_total_times', 0)

        # Calcular IOPS (operaciones por segundo)
        read_iops = 0
        write_iops = 0
        avg_read_latency_ms = 0
        avg_write_latency_ms = 0

        if self.last_block_read_reqs is not None and self.last_block_write_reqs is not None and self.last_update_time is not None:
            time_delta = current_time - self.last_update_time
            if time_delta > 0:
                read_ops_delta = block_read_reqs - self.last_block_read_reqs
                write_ops_delta = block_write_reqs - self.last_block_write_reqs
                read_iops = max(0, read_ops_delta / time_delta)
                write_iops = max(0, write_ops_delta / time_delta)

        self.last_block_read_reqs = block_read_reqs
        self.last_block_write_reqs = block_write_reqs

        # Calcular latencia promedio (nanosegundos a milisegundos)
        if block_read_reqs > 0:
            avg_read_latency_ms = (block_rd_times / block_read_reqs) / 1_000_000  # ns a ms
        if block_write_reqs > 0:
            avg_write_latency_ms = (block_wr_times / block_write_reqs) / 1_000_000

        if block_capacity > 0:
            capacity_gb = block_capacity / (1024 * 1024 * 1024)
            allocation_gb = block_allocation / (1024 * 1024 * 1024)
            usage_percent = (block_allocation / block_capacity) * 100 if block_capacity > 0 else 0

            self.disk_usage_bar.set_value(usage_percent, allocation_gb, capacity_gb)
            self.disk_detail_label.set_text(f"Dispositivos: {stats.get('block_count', 0)}")
            self.disk_iops_label.set_text(f"📊 IOPS: {read_iops:.1f} lectura/s, {write_iops:.1f} escritura/s")
            self.disk_latency_label.set_text(f"⏱️ Latencia: {avg_read_latency_ms:.2f}ms lectura, {avg_write_latency_ms:.2f}ms escritura")

            # Actualizar quick stat de disco
            self.disk_mini_value.set_markup(f'<span size="large" weight="bold">{allocation_gb:.1f}/{capacity_gb:.1f} GB</span>')
        else:
            self.disk_usage_bar.set_value(0, 0, 0)
            self.disk_detail_label.set_text("Sin información de disco")
            self.disk_iops_label.set_text("")
            self.disk_latency_label.set_text("")
            self.disk_mini_value.set_markup('<span size="large">N/A</span>')

        # Red con formato
        rx_bytes = stats.get('net_rx_bytes', 0)
        tx_bytes = stats.get('net_tx_bytes', 0)

        def format_bytes(bytes_val):
            if bytes_val >= 1024 * 1024 * 1024:
                return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
            elif bytes_val >= 1024 * 1024:
                return f"{bytes_val / (1024 * 1024):.2f} MB"
            elif bytes_val >= 1024:
                return f"{bytes_val / 1024:.2f} KB"
            else:
                return f"{bytes_val} B"

        self.net_rx_label.set_text(f"⬇️ Recibido total: {format_bytes(rx_bytes)}")
        self.net_tx_label.set_text(f"⬆️ Enviado total: {format_bytes(tx_bytes)}")

        # === Información Avanzada ===

        # Interfaces de red con detalles
        net_interfaces = self.vm_manager.get_vm_network_interfaces(self.vm_name)
        if net_interfaces:
            ifaces_text = "🔌 Interfaces: "
            iface_details = []
            for iface in net_interfaces:
                mac = iface.get('mac', 'N/A')
                model = iface.get('model', 'N/A')
                state = iface.get('link_state', 'up')
                state_icon = "🟢" if state == "up" else "🔴"
                source = iface.get('source', 'N/A')
                iface_details.append(f"{state_icon} {mac} ({model}) → {source}")

            # Mostrar drops y errores si están disponibles
            net_rx_drop = stats.get('net_rx_drop', 0)
            net_tx_drop = stats.get('net_tx_drop', 0)
            if net_rx_drop > 0 or net_tx_drop > 0:
                iface_details.append(f"⚠️ Drops: RX {net_rx_drop}, TX {net_tx_drop}")

            self.net_interfaces_label.set_text(ifaces_text + ", ".join(iface_details))
        else:
            self.net_interfaces_label.set_text("🔌 Interfaces: N/A")

        # Drivers virtio
        virtio_info = self.vm_manager.get_vm_virtio_drivers(self.vm_name)
        if virtio_info:
            virtio_enabled = [k for k, v in virtio_info.items() if v]
            if virtio_enabled:
                self.virtio_drivers_label.set_text(f"⚡ Virtio: {', '.join(virtio_enabled)}")
            else:
                self.virtio_drivers_label.set_text("⚡ Virtio: Ninguno activo")
        else:
            self.virtio_drivers_label.set_text("⚡ Virtio: N/A")

        # CPU features (solo mostrar los más importantes)
        cpu_features = self.vm_manager.get_vm_cpu_features(self.vm_name)
        if cpu_features:
            # Filtrar solo features importantes (SSE, AVX, etc.)
            important = [f for f in cpu_features if any(x in f.lower() for x in ['sse', 'avx', 'aes', 'mode:'])]
            if important:
                self.cpu_features_label.set_text(f"🔧 CPU: {', '.join(important[:10])}")
            else:
                self.cpu_features_label.set_text(f"🔧 CPU: {len(cpu_features)} features habilitados")
        else:
            self.cpu_features_label.set_text("🔧 CPU: N/A")

        # Hugepages
        hugepages = self.vm_manager.get_vm_hugepages(self.vm_name)
        if hugepages and hugepages.get('enabled'):
            pages_info = hugepages.get('pages', [])
            if pages_info:
                page_sizes = [f"{p['size']}{p['unit']}" for p in pages_info]
                self.hugepages_label.set_text(f"📄 Hugepages: Habilitadas ({', '.join(page_sizes)})")
            else:
                self.hugepages_label.set_text("📄 Hugepages: Habilitadas")
        else:
            self.hugepages_label.set_text("📄 Hugepages: Deshabilitadas")

        # Blkio weight
        blkio_weight = self.vm_manager.get_vm_blkio_weight(self.vm_name)
        if blkio_weight:
            priority = "Alta" if blkio_weight > 700 else ("Normal" if blkio_weight >= 300 else "Baja")
            self.blkio_label.set_text(f"⚖️ Prioridad I/O: {blkio_weight} ({priority})")
        else:
            self.blkio_label.set_text("⚖️ Prioridad I/O: N/A")

        # Temperatura del host
        host_temp = self.vm_manager.get_vm_host_cpu_temp()
        if host_temp:
            temp_color = "🟢" if host_temp < 60 else ("🟡" if host_temp < 80 else "🔴")
            self.host_temp_label.set_text(f"{temp_color} Temp. Host: {host_temp:.1f}°C")
        else:
            self.host_temp_label.set_text("🌡️ Temp. Host: N/A")

        # Usuarios conectados
        users = self.vm_manager.get_vm_guest_users(self.vm_name)
        if users:
            self.guest_users_label.set_text(f"👥 Usuarios: {', '.join(users)}")
        else:
            self.guest_users_label.set_text("👥 Usuarios: Ninguno")

    def _clear_detailed_stats(self):
        """Limpia las estadísticas detalladas"""
        self.cpu_circular.set_value(0, "0%")
        self.memory_circular.set_value(0, "0 GB", "RAM Asignada")
        self.vcpu_info_label.set_text("VM apagada")
        self.disk_usage_bar.set_value(0, 0, 0)
        self.disk_detail_label.set_text("VM apagada")
        self.disk_iops_label.set_text("")
        self.disk_latency_label.set_text("")
        self.net_rx_label.set_text("⬇️ Recibido: N/A")
        self.net_tx_label.set_text("⬆️ Enviado: N/A")
        self.uptime_label.set_text("⏰ Uptime: N/A")

        # Limpiar información avanzada
        self.net_interfaces_label.set_text("")
        self.virtio_drivers_label.set_text("")
        self.cpu_features_label.set_text("")
        self.hugepages_label.set_text("")
        self.blkio_label.set_text("")
        self.host_temp_label.set_text("")
        self.guest_users_label.set_text("")

        # Limpiar historial
        self.cpu_history.clear()
        self.memory_history.clear()
        self.net_rx_history.clear()
        self.net_tx_history.clear()

        # Resetear tracking
        self.last_cpu_time = None
        self.last_update_time = None
        self.last_net_rx_bytes = None
        self.last_net_tx_bytes = None
        self.last_block_read_reqs = None
        self.last_block_write_reqs = None
    
    def execute_vm_action(self, action_func, success_message, operation_name):
        """Ejecuta una acción de VM en un hilo separado"""
        def run_action():
            GLib.idle_add(self.set_loading, True)

            try:
                # Llamar a la función de VM (ahora retorna tupla)
                result = action_func(self.vm_name)

                # Compatibilidad: algunas funciones pueden retornar solo bool
                if isinstance(result, tuple):
                    success, error_info = result
                else:
                    success = result
                    error_info = None

                time.sleep(0.5)  # Pequeña pausa para que se vea la operación

                GLib.idle_add(self.set_loading, False)
                GLib.idle_add(self.update_vm_status)

                if success:
                    if self.notification_manager:
                        GLib.idle_add(self.notification_manager.show_success,
                                    f"{success_message}")
                else:
                    if self.error_handler and error_info:
                        GLib.idle_add(self.error_handler.handle_vm_operation_error,
                                    self.vm_name, operation_name, error_info)
                    elif self.error_handler:
                        # Fallback para errores sin info detallada
                        GLib.idle_add(self.error_handler.handle_vm_operation_error,
                                    self.vm_name, operation_name, "Operación falló")

            except Exception as e:
                GLib.idle_add(self.set_loading, False)
                if self.error_handler:
                    error_info = {
                        "type": "exception",
                        "message": f"Error inesperado: {str(e)}",
                        "suggestion": "Revisa los logs para más información"
                    }
                    GLib.idle_add(self.error_handler.handle_vm_operation_error,
                                self.vm_name, operation_name, error_info)

        thread = threading.Thread(target=run_action)
        thread.daemon = True
        thread.start()
    
    def on_start_clicked(self, button):
        self.execute_vm_action(self.vm_manager.start_vm, f"VM '{self.vm_name}' iniciada exitosamente", "start")

    def on_shutdown_clicked(self, button):
        self.execute_vm_action(self.vm_manager.shutdown_vm, f"VM '{self.vm_name}' apagándose", "shutdown")

    def on_reboot_clicked(self, button):
        self.execute_vm_action(self.vm_manager.reboot_vm, f"VM '{self.vm_name}' reiniciándose", "reboot")

    def on_save_clicked(self, button):
        self.execute_vm_action(self.vm_manager.save_vm, f"Estado de '{self.vm_name}' guardado", "save")

    def on_destroy_clicked(self, button):
        if self.notification_manager:
            self.notification_manager.show_confirmation_dialog(
                "Confirmar acción destructiva",
                f"¿Estás seguro de que quieres forzar el apagado de '{self.vm_name}'?\n\nEsto puede causar pérdida de datos no guardados.",
                lambda: self.execute_vm_action(self.vm_manager.destroy_vm, f"VM '{self.vm_name}' apagada forzadamente", "destroy")
            )
        else:
            self.execute_vm_action(self.vm_manager.destroy_vm, f"VM '{self.vm_name}' apagada forzadamente", "destroy")

    def on_viewer_clicked(self, button):
        """Maneja el clic del botón Viewer"""
        self.execute_vm_action(self.vm_manager.open_viewer, f"Abriendo viewer para '{self.vm_name}'", "viewer")


class VMPanelWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        print("🎯 Inicializando VMPanelWindow...")
        
        self.vm_manager = VMManager()
        self.vm_cards = {}
        
        # Cargar estilos CSS
        self.load_css()
        
        # Configuración de la ventana
        self.set_title("Panel de Máquinas Virtuales")
        self.set_default_size(800, 600)
        self.set_size_request(600, 400)
        
        print(f"🎯 Ventana configurada: {self.get_title()}")
        
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
        
        # === DASHBOARD DE RESUMEN ===
        summary_frame = Gtk.Frame()
        summary_frame.set_css_classes(['card'])
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        summary_box.set_margin_top(16)
        summary_box.set_margin_bottom(16)
        summary_box.set_margin_start(16)
        summary_box.set_margin_end(16)

        # Título del resumen
        summary_title = Gtk.Label()
        summary_title.set_markup('<span size="large" weight="bold">📊 Resumen General</span>')
        summary_title.set_halign(Gtk.Align.START)
        summary_box.append(summary_title)

        # Grid de quick stats
        stats_grid = Gtk.Grid()
        stats_grid.set_row_spacing(12)
        stats_grid.set_column_spacing(12)
        stats_grid.set_column_homogeneous(True)

        # Card de VMs totales
        self.total_vms_card = self._create_stat_card("💻 Máquinas Virtuales", "0 activas / 0 total", "success")
        stats_grid.attach(self.total_vms_card, 0, 0, 1, 1)

        # Card de CPU total
        self.total_cpu_card = self._create_stat_card("⚙️ CPU Total", "0%", "info")
        stats_grid.attach(self.total_cpu_card, 1, 0, 1, 1)

        # Card de RAM total
        self.total_ram_card = self._create_stat_card("💾 RAM Total", "0 GB", "info")
        stats_grid.attach(self.total_ram_card, 2, 0, 1, 1)

        # Card de temperatura del host
        self.host_temp_card = self._create_stat_card("🌡️ Temperatura Host", "N/A", "warning")
        stats_grid.attach(self.host_temp_card, 3, 0, 1, 1)

        summary_box.append(stats_grid)
        summary_frame.set_child(summary_box)
        main_box.append(summary_frame)

        # Separador
        main_box.append(Gtk.Separator())

        # Título de VMs
        vms_title = Gtk.Label()
        vms_title.set_markup('<span size="large" weight="bold">💻 Máquinas Virtuales</span>')
        vms_title.set_halign(Gtk.Align.START)
        vms_title.set_margin_top(12)
        main_box.append(vms_title)

        # Contenedor para las tarjetas de VMs (Grid en lugar de Box vertical)
        self.vms_box = Gtk.Grid()
        self.vms_box.set_row_spacing(16)
        self.vms_box.set_column_spacing(16)
        self.vms_box.set_column_homogeneous(True)
        
        # Crear tarjetas para cada VM en grid de 2 columnas
        row = 0
        col = 0
        for vm_name in self.vm_manager.vm_names:
            vm_card = VMCard(vm_name, self.vm_manager, self.notification_manager, self.error_handler)
            self.vm_cards[vm_name] = vm_card
            self.vms_box.attach(vm_card, col, row, 1, 1)

            col += 1
            if col >= 2:  # 2 columnas estilo Proxmox
                col = 0
                row += 1
        
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
    
    def _create_stat_card(self, title, value, style_class):
        """Crea una card de estadística rápida"""
        card_frame = Gtk.Frame()
        card_frame.set_css_classes(['card', f'stat-card-{style_class}'])

        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card_box.set_margin_top(12)
        card_box.set_margin_bottom(12)
        card_box.set_margin_start(12)
        card_box.set_margin_end(12)

        # Título
        title_label = Gtk.Label()
        title_label.set_markup(f'<span size="small">{title}</span>')
        title_label.set_halign(Gtk.Align.START)
        title_label.set_css_classes(['dim-label'])
        card_box.append(title_label)

        # Valor
        value_label = Gtk.Label()
        value_label.set_markup(f'<span size="x-large" weight="bold">{value}</span>')
        value_label.set_halign(Gtk.Align.START)
        card_box.append(value_label)

        card_frame.set_child(card_box)

        # Guardar referencia al label de valor para actualizarlo después
        card_frame.value_label = value_label

        return card_frame

    def _update_summary_stats(self):
        """Actualiza las estadísticas del dashboard de resumen"""
        total_vms = len(self.vm_manager.vm_names)
        running_vms = sum(1 for vm in self.vm_manager.list_all_vms() if vm['running'])

        # VMs totales
        self.total_vms_card.value_label.set_markup(
            f'<span size="x-large" weight="bold">{running_vms} activas / {total_vms} total</span>'
        )

        # CPU total (promedio de todas las VMs)
        total_cpu = 0
        cpu_count = 0
        for vm_card in self.vm_cards.values():
            if hasattr(vm_card, 'last_cpu_time') and vm_card.last_cpu_time is not None:
                stats = self.vm_manager.get_vm_detailed_stats(vm_card.vm_name)
                if stats and stats.get('cpu_time'):
                    # Aproximación simplificada
                    cpu_count += 1

        # Mostrar un promedio simple (esto se puede mejorar)
        avg_cpu = total_cpu / max(1, cpu_count) if cpu_count > 0 else 0
        self.total_cpu_card.value_label.set_markup(
            f'<span size="x-large" weight="bold">~{avg_cpu:.1f}%</span>'
        )

        # RAM total (usar datos consistentes de domstats)
        total_ram_gb = 0
        for vm_card in self.vm_cards.values():
            stats = self.vm_manager.get_vm_detailed_stats(vm_card.vm_name)
            if stats:
                mem_actual = stats.get('memory_actual')
                mem_unused = stats.get('memory_unused')
                mem_rss = stats.get('memory_rss')
                if mem_actual and mem_unused is not None:
                    used_kb = mem_actual - mem_unused
                    total_ram_gb += used_kb / (1024 * 1024)
                elif mem_actual and mem_rss:
                    # Usar RSS como aproximación
                    total_ram_gb += mem_rss / (1024 * 1024)
                elif mem_actual:
                    # Fallback: usar memoria asignada
                    total_ram_gb += mem_actual / (1024 * 1024)

        self.total_ram_card.value_label.set_markup(
            f'<span size="x-large" weight="bold">{total_ram_gb:.1f} GB</span>'
        )

        # Temperatura del host
        host_temp = self.vm_manager.get_vm_host_cpu_temp()
        if host_temp:
            temp_icon = "🟢" if host_temp < 60 else ("🟡" if host_temp < 80 else "🔴")
            self.host_temp_card.value_label.set_markup(
                f'<span size="x-large" weight="bold">{temp_icon} {host_temp:.1f}°C</span>'
            )
        else:
            self.host_temp_card.value_label.set_markup(
                f'<span size="x-large" weight="bold">N/A</span>'
            )

    def setup_auto_update(self):
        """Configura la actualización automática cada 5 segundos"""
        self.update_counter = 0
        
        def auto_update():
            self.update_counter += 1
            
            # Actualizar VMs cada 5 segundos
            for vm_card in self.vm_cards.values():
                if not vm_card.is_updating:
                    vm_card.update_vm_status()

            # Actualizar dashboard solo cada 15 segundos (cada 3 ciclos)
            if self.update_counter % 3 == 0:
                self._update_summary_stats()

            return True  # Continuar el timer

        # Primera actualización inmediata
        self._update_summary_stats()

        GLib.timeout_add_seconds(5, auto_update)

    def on_refresh_clicked(self, button):
        """Maneja el clic del botón de actualizar"""
        for vm_card in self.vm_cards.values():
            vm_card.update_vm_status()
        self._update_summary_stats()

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