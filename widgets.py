"""
Widgets personalizados con Cairo para visualización de métricas
"""
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import cairo
import math
from typing import List, Tuple


class CircularProgressWidget(Gtk.DrawingArea):
    """Widget circular para mostrar progreso con Cairo"""

    def __init__(self, size=120):
        super().__init__()
        self.size = size
        self.percentage = 0.0
        self.label = "0%"
        self.title = ""
        self.set_content_width(size)
        self.set_content_height(size)
        self.set_draw_func(self._on_draw)

    def set_value(self, percentage: float, label: str = None, title: str = None):
        """Actualiza el valor del gráfico circular"""
        self.percentage = max(0.0, min(100.0, percentage))
        if label:
            self.label = label
        else:
            self.label = f"{self.percentage:.1f}%"
        if title:
            self.title = title
        self.queue_draw()

    def _get_color(self) -> Tuple[float, float, float]:
        """Retorna color según porcentaje"""
        if self.percentage < 70:
            # Verde
            return (0.15, 0.76, 0.41)
        elif self.percentage < 85:
            # Amarillo/Naranja
            return (0.96, 0.76, 0.07)
        else:
            # Rojo
            return (0.88, 0.11, 0.14)

    def _on_draw(self, area, ctx, width, height):
        """Dibuja el gráfico circular"""
        # Centro y radio
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 10
        line_width = 12

        # Fondo del círculo (gris claro)
        ctx.set_line_width(line_width)
        ctx.set_source_rgba(0.2, 0.2, 0.2, 0.2)
        ctx.arc(center_x, center_y, radius, 0, 2 * math.pi)
        ctx.stroke()

        # Arco de progreso
        if self.percentage > 0:
            r, g, b = self._get_color()
            ctx.set_source_rgb(r, g, b)
            ctx.set_line_width(line_width)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)

            # Ángulo inicial en -90° (arriba)
            start_angle = -math.pi / 2
            end_angle = start_angle + (2 * math.pi * self.percentage / 100)

            ctx.arc(center_x, center_y, radius, start_angle, end_angle)
            ctx.stroke()

        # Texto del porcentaje
        ctx.set_source_rgb(0.9, 0.9, 0.9)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(22)

        text_extents = ctx.text_extents(self.label)
        text_x = center_x - text_extents.width / 2
        text_y = center_y + text_extents.height / 2

        ctx.move_to(text_x, text_y)
        ctx.show_text(self.label)

        # Título encima si existe (con más espacio)
        if self.title:
            ctx.set_font_size(12)
            ctx.set_source_rgb(0.7, 0.7, 0.7)
            title_extents = ctx.text_extents(self.title)
            title_x = center_x - title_extents.width / 2
            title_y = center_y - radius - 15  # Aumentado de 5 a 15 para más espacio
            ctx.move_to(title_x, title_y)
            ctx.show_text(self.title)


class MiniLineChartWidget(Gtk.DrawingArea):
    """Mini gráfico de línea para mostrar historial"""

    def __init__(self, width=200, height=60, max_points=30):
        super().__init__()
        self.width = width
        self.height = height
        self.max_points = max_points
        self.data_points: List[float] = []
        self.title = ""
        self.color = (0.2, 0.6, 1.0)  # Azul por defecto

        self.set_content_width(width)
        self.set_content_height(height)
        self.set_draw_func(self._on_draw)

    def add_data_point(self, value: float):
        """Agrega un punto al historial"""
        self.data_points.append(max(0.0, min(100.0, value)))
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.queue_draw()

    def set_title(self, title: str):
        """Establece el título"""
        self.title = title
        self.queue_draw()

    def set_color(self, r: float, g: float, b: float):
        """Establece el color de la línea"""
        self.color = (r, g, b)
        self.queue_draw()

    def _on_draw(self, area, ctx, width, height):
        """Dibuja el mini gráfico de línea"""
        if not self.data_points:
            return

        # Márgenes
        margin_left = 10
        margin_right = 10
        margin_top = 20
        margin_bottom = 10

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        # Fondo
        ctx.set_source_rgba(0.1, 0.1, 0.1, 0.3)
        ctx.rectangle(margin_left, margin_top, chart_width, chart_height)
        ctx.fill()

        # Grid horizontal (líneas de referencia)
        ctx.set_source_rgba(0.3, 0.3, 0.3, 0.5)
        ctx.set_line_width(0.5)
        for i in range(5):
            y = margin_top + (chart_height / 4) * i
            ctx.move_to(margin_left, y)
            ctx.line_to(margin_left + chart_width, y)
            ctx.stroke()

        # Dibujar línea de datos
        if len(self.data_points) > 1:
            r, g, b = self.color

            # Área bajo la curva (gradiente)
            ctx.set_source_rgba(r, g, b, 0.2)
            x_step = chart_width / (self.max_points - 1)

            ctx.move_to(margin_left, margin_top + chart_height)
            for i, value in enumerate(self.data_points):
                x = margin_left + i * x_step
                y = margin_top + chart_height - (value / 100 * chart_height)
                ctx.line_to(x, y)
            ctx.line_to(margin_left + len(self.data_points) * x_step, margin_top + chart_height)
            ctx.close_path()
            ctx.fill()

            # Línea principal
            ctx.set_source_rgb(r, g, b)
            ctx.set_line_width(2)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)

            for i, value in enumerate(self.data_points):
                x = margin_left + i * x_step
                y = margin_top + chart_height - (value / 100 * chart_height)

                if i == 0:
                    ctx.move_to(x, y)
                else:
                    ctx.line_to(x, y)
            ctx.stroke()

            # Puntos en la línea
            ctx.set_source_rgb(r, g, b)
            for i, value in enumerate(self.data_points):
                x = margin_left + i * x_step
                y = margin_top + chart_height - (value / 100 * chart_height)
                ctx.arc(x, y, 2, 0, 2 * math.pi)
                ctx.fill()

        # Título
        if self.title:
            ctx.set_source_rgb(0.8, 0.8, 0.8)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(10)
            ctx.move_to(margin_left, 12)
            ctx.show_text(self.title)

        # Valor actual
        if self.data_points:
            current = self.data_points[-1]
            text = f"{current:.1f}%"
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(10)
            text_extents = ctx.text_extents(text)
            ctx.move_to(width - margin_right - text_extents.width, 12)
            ctx.show_text(text)


class DiskUsageBarWidget(Gtk.DrawingArea):
    """Barra de uso de disco con gradiente"""

    def __init__(self, width=300, height=30):
        super().__init__()
        self.width = width
        self.height = height
        self.percentage = 0.0
        self.used_gb = 0.0
        self.total_gb = 0.0

        self.set_content_width(width)
        self.set_content_height(height)
        self.set_draw_func(self._on_draw)

    def set_value(self, percentage: float, used_gb: float, total_gb: float):
        """Actualiza los valores"""
        self.percentage = max(0.0, min(100.0, percentage))
        self.used_gb = used_gb
        self.total_gb = total_gb
        self.queue_draw()

    def _on_draw(self, area, ctx, width, height):
        """Dibuja la barra de disco"""
        # Fondo
        ctx.set_source_rgba(0.2, 0.2, 0.2, 0.3)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        # Barra de progreso con gradiente
        if self.percentage > 0:
            bar_width = width * (self.percentage / 100)

            # Crear gradiente según porcentaje
            gradient = cairo.LinearGradient(0, 0, bar_width, 0)

            if self.percentage < 70:
                # Verde
                gradient.add_color_stop_rgb(0, 0.15, 0.76, 0.41)
                gradient.add_color_stop_rgb(1, 0.18, 0.85, 0.49)
            elif self.percentage < 85:
                # Amarillo/Naranja
                gradient.add_color_stop_rgb(0, 0.96, 0.76, 0.07)
                gradient.add_color_stop_rgb(1, 0.96, 0.65, 0.07)
            else:
                # Rojo
                gradient.add_color_stop_rgb(0, 0.88, 0.11, 0.14)
                gradient.add_color_stop_rgb(1, 0.75, 0.07, 0.11)

            ctx.set_source(gradient)
            ctx.rectangle(0, 0, bar_width, height)
            ctx.fill()

        # Texto
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(12)

        text = f"{self.used_gb:.1f} GB / {self.total_gb:.1f} GB ({self.percentage:.1f}%)"
        text_extents = ctx.text_extents(text)
        text_x = (width - text_extents.width) / 2
        text_y = (height + text_extents.height) / 2 - 2

        # Sombra del texto
        ctx.set_source_rgba(0, 0, 0, 0.5)
        ctx.move_to(text_x + 1, text_y + 1)
        ctx.show_text(text)

        # Texto principal
        ctx.set_source_rgb(1, 1, 1)
        ctx.move_to(text_x, text_y)
        ctx.show_text(text)
