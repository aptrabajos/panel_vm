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
        # Aumentar altura para que quepa el título arriba
        self.set_content_width(size)
        self.set_content_height(size + 30)  # +30px para el título
        self.set_draw_func(self._on_draw)

    def set_value(self, percentage: float, label: str = None, title: str = None):
        """Actualiza el valor del gráfico circular"""
        new_percentage = max(0.0, min(100.0, percentage))
        new_label = label if label else f"{new_percentage:.1f}%"
        new_title = title if title else self.title
        
        # Solo redibujar si los valores cambiaron significativamente
        if (abs(new_percentage - self.percentage) > 0.5 or 
            new_label != self.label or 
            new_title != self.title):
            self.percentage = new_percentage
            self.label = new_label
            self.title = new_title
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
        """Dibuja el gráfico circular moderno"""
        # Centro y radio (desplazar círculo hacia abajo para dejar espacio al título)
        center_x = width / 2
        center_y = height - (self.size / 2)  # Posicionar círculo en la parte inferior
        radius = (self.size / 2) - 12
        line_width = 14

        # Sombra del fondo del círculo
        ctx.save()
        ctx.set_line_width(line_width + 2)
        ctx.set_source_rgba(0, 0, 0, 0.15)
        ctx.arc(center_x + 2, center_y + 2, radius, 0, 2 * math.pi)
        ctx.stroke()
        ctx.restore()

        # Fondo del círculo con gradiente
        ctx.save()
        ctx.set_line_width(line_width)
        
        # Crear gradiente radial para el fondo
        pattern = cairo.RadialGradient(center_x, center_y, 0, center_x, center_y, radius)
        pattern.add_color_stop_rgba(0, 0.15, 0.15, 0.15, 0.3)
        pattern.add_color_stop_rgba(1, 0.05, 0.05, 0.05, 0.1)
        ctx.set_source(pattern)
        ctx.arc(center_x, center_y, radius, 0, 2 * math.pi)
        ctx.stroke()
        ctx.restore()

        # Arco de progreso con efectos modernos
        if self.percentage > 0:
            r, g, b = self._get_color()
            
            # Sombra del arco de progreso
            ctx.save()
            ctx.set_line_width(line_width + 1)
            ctx.set_source_rgba(r, g, b, 0.3)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            start_angle = -math.pi / 2
            end_angle = start_angle + (2 * math.pi * self.percentage / 100)
            ctx.arc(center_x + 1, center_y + 1, radius, start_angle, end_angle)
            ctx.stroke()
            ctx.restore()

            # Arco principal con gradiente
            ctx.save()
            ctx.set_line_width(line_width)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            
            # Crear gradiente para el arco
            pattern = cairo.LinearGradient(center_x - radius, center_y, center_x + radius, center_y)
            pattern.add_color_stop_rgba(0, r, g, b, 0.8)
            pattern.add_color_stop_rgba(0.5, r + 0.1, g + 0.1, b + 0.1, 1.0)
            pattern.add_color_stop_rgba(1, r, g, b, 0.8)
            ctx.set_source(pattern)
            
            ctx.arc(center_x, center_y, radius, start_angle, end_angle)
            ctx.stroke()
            ctx.restore()

            # Brillo interior
            ctx.save()
            ctx.set_line_width(line_width - 4)
            ctx.set_source_rgba(1, 1, 1, 0.2)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.arc(center_x, center_y, radius, start_angle, end_angle)
            ctx.stroke()
            ctx.restore()

        # Texto del porcentaje con sombra
        ctx.save()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24)
        
        # Sombra del texto
        ctx.set_source_rgba(0, 0, 0, 0.5)
        text_extents = ctx.text_extents(self.label)
        text_x = center_x - text_extents.width / 2
        text_y = center_y + text_extents.height / 2
        ctx.move_to(text_x + 1, text_y + 1)
        ctx.show_text(self.label)
        
        # Texto principal
        ctx.set_source_rgb(0.95, 0.95, 0.95)
        ctx.move_to(text_x, text_y)
        ctx.show_text(self.label)
        ctx.restore()

        # Título encima con mejor estilo
        if self.title:
            ctx.save()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(13)
            
            # Sombra del título
            ctx.set_source_rgba(0, 0, 0, 0.4)
            title_extents = ctx.text_extents(self.title)
            title_x = center_x - title_extents.width / 2
            title_y = center_y - radius - 18
            ctx.move_to(title_x + 1, title_y + 1)
            ctx.show_text(self.title)
            
            # Título principal
            ctx.set_source_rgb(0.8, 0.8, 0.8)
            ctx.move_to(title_x, title_y)
            ctx.show_text(self.title)
            ctx.restore()


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
        new_value = max(0.0, min(100.0, value))
        
        # Solo redibujar si el valor cambió significativamente o es un nuevo punto
        should_update = (not self.data_points or 
                        abs(new_value - self.data_points[-1]) > 0.5)
        
        self.data_points.append(new_value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        
        if should_update:
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
        """Dibuja el mini gráfico de línea moderno"""
        if not self.data_points:
            return

        # Márgenes
        margin_left = 12
        margin_right = 12
        margin_top = 22
        margin_bottom = 12

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        # Fondo con gradiente
        ctx.save()
        pattern = cairo.LinearGradient(margin_left, margin_top, margin_left, margin_top + chart_height)
        pattern.add_color_stop_rgba(0, 0.08, 0.08, 0.08, 0.4)
        pattern.add_color_stop_rgba(1, 0.04, 0.04, 0.04, 0.2)
        ctx.set_source(pattern)
        ctx.rectangle(margin_left, margin_top, chart_width, chart_height)
        ctx.fill()
        ctx.restore()

        # Borde del área del gráfico
        ctx.save()
        ctx.set_line_width(1)
        ctx.set_source_rgba(0.2, 0.2, 0.2, 0.6)
        ctx.rectangle(margin_left, margin_top, chart_width, chart_height)
        ctx.stroke()
        ctx.restore()

        # Grid horizontal mejorado
        ctx.save()
        ctx.set_line_width(0.5)
        for i in range(5):
            y = margin_top + (chart_height / 4) * i
            if i == 0 or i == 4:  # Líneas superior e inferior más visibles
                ctx.set_source_rgba(0.3, 0.3, 0.3, 0.7)
            else:
                ctx.set_source_rgba(0.2, 0.2, 0.2, 0.4)
            ctx.move_to(margin_left, y)
            ctx.line_to(margin_left + chart_width, y)
            ctx.stroke()
        ctx.restore()

        # Dibujar línea de datos
        if len(self.data_points) > 1:
            r, g, b = self.color
            x_step = chart_width / (self.max_points - 1)

            # Área bajo la curva con gradiente
            ctx.save()
            pattern = cairo.LinearGradient(margin_left, margin_top + chart_height, margin_left, margin_top)
            pattern.add_color_stop_rgba(0, r, g, b, 0.3)
            pattern.add_color_stop_rgba(1, r, g, b, 0.05)
            ctx.set_source(pattern)

            ctx.move_to(margin_left, margin_top + chart_height)
            for i, value in enumerate(self.data_points):
                x = margin_left + i * x_step
                y = margin_top + chart_height - (value / 100 * chart_height)
                ctx.line_to(x, y)
            ctx.line_to(margin_left + len(self.data_points) * x_step, margin_top + chart_height)
            ctx.close_path()
            ctx.fill()
            ctx.restore()

            # Línea principal con gradiente
            ctx.save()
            pattern = cairo.LinearGradient(margin_left, 0, margin_left + chart_width, 0)
            pattern.add_color_stop_rgba(0, r, g, b, 0.8)
            pattern.add_color_stop_rgba(0.5, r + 0.1, g + 0.1, b + 0.1, 1.0)
            pattern.add_color_stop_rgba(1, r, g, b, 0.8)
            ctx.set_source(pattern)
            ctx.set_line_width(2.5)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)

            for i, value in enumerate(self.data_points):
                x = margin_left + i * x_step
                y = margin_top + chart_height - (value / 100 * chart_height)

                if i == 0:
                    ctx.move_to(x, y)
                else:
                    ctx.line_to(x, y)
            ctx.stroke()
            ctx.restore()

            # Puntos en la línea con brillo
            ctx.save()
            for i, value in enumerate(self.data_points):
                x = margin_left + i * x_step
                y = margin_top + chart_height - (value / 100 * chart_height)
                
                # Sombra del punto
                ctx.set_source_rgba(0, 0, 0, 0.3)
                ctx.arc(x + 1, y + 1, 3, 0, 2 * math.pi)
                ctx.fill()
                
                # Punto principal con gradiente
                pattern = cairo.RadialGradient(x, y, 0, x, y, 3)
                pattern.add_color_stop_rgba(0, 1, 1, 1, 0.8)
                pattern.add_color_stop_rgba(0.5, r, g, b, 1.0)
                pattern.add_color_stop_rgba(1, r * 0.7, g * 0.7, b * 0.7, 1.0)
                ctx.set_source(pattern)
                ctx.arc(x, y, 3, 0, 2 * math.pi)
                ctx.fill()
                
                # Brillo central
                ctx.set_source_rgba(1, 1, 1, 0.6)
                ctx.arc(x, y, 1.5, 0, 2 * math.pi)
                ctx.fill()
            ctx.restore()

        # Título con sombra
        if self.title:
            ctx.save()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(11)
            
            # Sombra del título
            ctx.set_source_rgba(0, 0, 0, 0.4)
            ctx.move_to(margin_left + 1, 13)
            ctx.show_text(self.title)
            
            # Título principal
            ctx.set_source_rgb(0.85, 0.85, 0.85)
            ctx.move_to(margin_left, 12)
            ctx.show_text(self.title)
            ctx.restore()

        # Valor actual con mejor estilo
        if self.data_points:
            current = self.data_points[-1]
            text = f"{current:.1f}%"
            ctx.save()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(11)
            
            # Sombra del valor
            text_extents = ctx.text_extents(text)
            ctx.set_source_rgba(0, 0, 0, 0.4)
            ctx.move_to(width - margin_right - text_extents.width + 1, 13)
            ctx.show_text(text)
            
            # Valor principal
            ctx.set_source_rgb(0.95, 0.95, 0.95)
            ctx.move_to(width - margin_right - text_extents.width, 12)
            ctx.show_text(text)
            ctx.restore()


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
        """Dibuja la barra de disco moderna"""
        # Fondo con gradiente
        ctx.save()
        pattern = cairo.LinearGradient(0, 0, 0, height)
        pattern.add_color_stop_rgba(0, 0.15, 0.15, 0.15, 0.4)
        pattern.add_color_stop_rgba(1, 0.08, 0.08, 0.08, 0.2)
        ctx.set_source(pattern)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        ctx.restore()

        # Borde del fondo
        ctx.save()
        ctx.set_line_width(1)
        ctx.set_source_rgba(0.2, 0.2, 0.2, 0.6)
        ctx.rectangle(0, 0, width, height)
        ctx.stroke()
        ctx.restore()

        # Barra de progreso con efectos modernos
        if self.percentage > 0:
            bar_width = width * (self.percentage / 100)

            # Sombra de la barra
            ctx.save()
            ctx.set_source_rgba(0, 0, 0, 0.2)
            ctx.rectangle(2, 2, bar_width, height)
            ctx.fill()
            ctx.restore()

            # Crear gradiente según porcentaje
            ctx.save()
            gradient = cairo.LinearGradient(0, 0, bar_width, 0)

            if self.percentage < 70:
                # Verde moderno
                gradient.add_color_stop_rgb(0, 0.06, 0.73, 0.39)
                gradient.add_color_stop_rgb(0.5, 0.16, 0.85, 0.49)
                gradient.add_color_stop_rgb(1, 0.06, 0.73, 0.39)
            elif self.percentage < 85:
                # Amarillo/Naranja moderno
                gradient.add_color_stop_rgb(0, 0.96, 0.76, 0.07)
                gradient.add_color_stop_rgb(0.5, 0.99, 0.85, 0.15)
                gradient.add_color_stop_rgb(1, 0.96, 0.76, 0.07)
            else:
                # Rojo moderno
                gradient.add_color_stop_rgb(0, 0.88, 0.11, 0.14)
                gradient.add_color_stop_rgb(0.5, 0.95, 0.15, 0.18)
                gradient.add_color_stop_rgb(1, 0.88, 0.11, 0.14)

            ctx.set_source(gradient)
            ctx.rectangle(0, 0, bar_width, height)
            ctx.fill()
            ctx.restore()

            # Brillo superior
            ctx.save()
            ctx.set_source_rgba(1, 1, 1, 0.2)
            ctx.rectangle(0, 0, bar_width, height * 0.3)
            ctx.fill()
            ctx.restore()

            # Borde de la barra
            ctx.save()
            ctx.set_line_width(1)
            ctx.set_source_rgba(1, 1, 1, 0.1)
            ctx.rectangle(0, 0, bar_width, height)
            ctx.stroke()
            ctx.restore()

        # Texto con mejor estilo
        ctx.save()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(13)

        text = f"{self.used_gb:.1f} GB / {self.total_gb:.1f} GB ({self.percentage:.1f}%)"
        text_extents = ctx.text_extents(text)
        text_x = (width - text_extents.width) / 2
        text_y = (height + text_extents.height) / 2 - 2

        # Sombra del texto
        ctx.set_source_rgba(0, 0, 0, 0.6)
        ctx.move_to(text_x + 1, text_y + 1)
        ctx.show_text(text)

        # Texto principal
        ctx.set_source_rgb(0.95, 0.95, 0.95)
        ctx.move_to(text_x, text_y)
        ctx.show_text(text)
        ctx.restore()
