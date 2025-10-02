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
        self.details_expander.set_label("📊 Ver detalles avanzados con gráficos")

        # Contenedor de detalles
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        details_box.set_margin_top(12)

        # === Gráficos Circulares (CPU y Memoria) ===
        graphs_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        graphs_row.set_halign(Gtk.Align.CENTER)

        # Gráfico circular de CPU
        self.cpu_circular = CircularProgressWidget(size=140)
        self.cpu_circular.set_value(0, "0%", "CPU")
        graphs_row.append(self.cpu_circular)

        # Gráfico circular de Memoria
        self.memory_circular = CircularProgressWidget(size=140)
        self.memory_circular.set_value(0, "0 GB", "RAM Asignada")
        graphs_row.append(self.memory_circular)

        details_box.append(graphs_row)
        details_box.append(Gtk.Separator())

        # === Mini gráficos de línea (historial) ===
        charts_label = Gtk.Label()
        charts_label.set_markup('<span weight="bold">Historial (últimos 2.5 min)</span>')
        charts_label.set_halign(Gtk.Align.START)
        details_box.append(charts_label)

        # Mini gráfico de CPU
        self.cpu_line_chart = MiniLineChartWidget(width=280, height=70)
        self.cpu_line_chart.set_title("CPU")
        self.cpu_line_chart.set_color(0.26, 0.59, 0.98)  # Azul
        details_box.append(self.cpu_line_chart)

        # Mini gráfico de Memoria
        self.memory_line_chart = MiniLineChartWidget(width=280, height=70)
        self.memory_line_chart.set_title("Memoria")
        self.memory_line_chart.set_color(0.61, 0.15, 0.69)  # Púrpura
        details_box.append(self.memory_line_chart)

        details_box.append(Gtk.Separator())

        # === Información de vCPUs ===
        vcpu_label = Gtk.Label()
        vcpu_label.set_markup('<span weight="bold">CPUs Virtuales</span>')
        vcpu_label.set_halign(Gtk.Align.START)
        self.vcpu_info_label = Gtk.Label()
        self.vcpu_info_label.set_css_classes(['caption'])
        self.vcpu_info_label.set_halign(Gtk.Align.START)

        details_box.append(vcpu_label)
        details_box.append(self.vcpu_info_label)
        details_box.append(Gtk.Separator())

        # === Disco con barra personalizada ===
        disk_label = Gtk.Label()
        disk_label.set_markup('<span weight="bold">Almacenamiento</span>')
        disk_label.set_halign(Gtk.Align.START)
        details_box.append(disk_label)

        self.disk_usage_bar = DiskUsageBarWidget(width=280, height=30)
        self.disk_usage_bar.set_value(0, 0, 0)
        details_box.append(self.disk_usage_bar)

        self.disk_detail_label = Gtk.Label()
        self.disk_iops_label = Gtk.Label()
        self.disk_latency_label = Gtk.Label()
        self.disk_detail_label.set_css_classes(['caption'])
        self.disk_iops_label.set_css_classes(['caption'])
        self.disk_latency_label.set_css_classes(['caption'])
        self.disk_detail_label.set_halign(Gtk.Align.START)
        self.disk_iops_label.set_halign(Gtk.Align.START)
        self.disk_latency_label.set_halign(Gtk.Align.START)
        details_box.append(self.disk_detail_label)
        details_box.append(self.disk_iops_label)
        details_box.append(self.disk_latency_label)

        details_box.append(Gtk.Separator())

        # === Red ===
        net_label = Gtk.Label()
        net_label.set_markup('<span weight="bold">Red (tiempo real)</span>')
        net_label.set_halign(Gtk.Align.START)
        details_box.append(net_label)

        # Mini gráfico de red RX (bajada)
        self.net_rx_chart = MiniLineChartWidget(width=280, height=70)
        self.net_rx_chart.set_title("⬇️ Descarga (MB/s)")
        self.net_rx_chart.set_color(0.26, 0.80, 0.41)  # Verde
        details_box.append(self.net_rx_chart)

        # Mini gráfico de red TX (subida)
        self.net_tx_chart = MiniLineChartWidget(width=280, height=70)
        self.net_tx_chart.set_title("⬆️ Subida (MB/s)")
        self.net_tx_chart.set_color(0.96, 0.61, 0.07)  # Naranja
        details_box.append(self.net_tx_chart)

        # Labels con acumulado total
        self.net_rx_label = Gtk.Label()
        self.net_tx_label = Gtk.Label()
        self.net_rx_label.set_css_classes(['caption'])
        self.net_tx_label.set_css_classes(['caption'])
        self.net_rx_label.set_halign(Gtk.Align.START)
        self.net_tx_label.set_halign(Gtk.Align.START)
        details_box.append(self.net_rx_label)
        details_box.append(self.net_tx_label)

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
        
        button_box.append(self.start_btn)
        button_box.append(self.shutdown_btn)
        button_box.append(self.reboot_btn)
        button_box.append(self.save_btn)
        button_box.append(self.destroy_btn)
        
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

                    # Memoria básica con balloon driver
                    mem_usage_info = self.vm_manager.get_vm_memory_usage(self.vm_name)
                    mem_actual = detailed_stats.get('memory_actual')
                    mem_available = detailed_stats.get('memory_available')

                    if mem_usage_info and 'actual' in mem_usage_info and 'unused' in mem_usage_info:
                        # Usar balloon stats para mostrar uso real dentro del guest
                        actual_kb = mem_usage_info['actual']
                        unused_kb = mem_usage_info['unused']
                        used_kb = actual_kb - unused_kb
                        mem_gb_used = used_kb / (1024 * 1024)
                        mem_percent = (used_kb / actual_kb) * 100
                        self.memory_label.set_text(f"💾 Memoria: {mem_gb_used:.1f} GB ({mem_percent:.0f}%)")
                    elif mem_actual and mem_available:
                        # Fallback: memoria asignada
                        mem_actual_gb = mem_actual / (1024 * 1024)
                        self.memory_label.set_text(f"💾 Memoria: {mem_actual_gb:.1f} GB (Asignada)")
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

        # Memoria: calcular uso real desde balloon driver
        mem_usage_info = self.vm_manager.get_vm_memory_usage(self.vm_name)
        mem_percent = 0
        mem_label = ""

        if mem_usage_info and 'actual' in mem_usage_info and 'unused' in mem_usage_info:
            # Tenemos balloon stats: calcular memoria usada dentro del guest
            actual_kb = mem_usage_info['actual']
            unused_kb = mem_usage_info['unused']
            used_kb = actual_kb - unused_kb

            # Calcular porcentaje sobre la memoria asignada
            mem_percent = (used_kb / actual_kb) * 100
            mem_gb_used = used_kb / (1024 * 1024)
            mem_label = f"{mem_gb_used:.1f} GB"
        elif mem_actual and mem_available:
            # Fallback: mostrar memoria asignada
            mem_gb = mem_actual / (1024 * 1024)
            mem_percent = 50  # Valor fijo visual
            mem_label = f"{mem_gb:.1f} GB"

        # Actualizar gráficos circulares
        self.cpu_circular.set_value(cpu_percent, f"{cpu_percent:.1f}%", "CPU")
        self.memory_circular.set_value(
            mem_percent,
            f"{mem_percent:.1f}%",
            "RAM" if mem_usage_info and 'rss' in mem_usage_info else "RAM Asignada"
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
        else:
            self.disk_usage_bar.set_value(0, 0, 0)
            self.disk_detail_label.set_text("Sin información de disco")
            self.disk_iops_label.set_text("")
            self.disk_latency_label.set_text("")

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

        self.net_rx_label.set_text(f"⬇️ Recibido: {format_bytes(rx_bytes)}")
        self.net_tx_label.set_text(f"⬆️ Enviado: {format_bytes(tx_bytes)}")

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