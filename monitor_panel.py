#!/usr/bin/env python3
"""
Monitor de recursos del Panel de VMs
Muestra uso de CPU, memoria y estadísticas en tiempo real
"""
import psutil
import time
import os
import sys
from datetime import datetime

def find_panel_process():
    """Encuentra el proceso del panel"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('main.py' in cmd or 'manjaro-vm-panel' in cmd for cmd in cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def format_bytes(bytes_value):
    """Formatea bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def monitor_panel():
    """Monitorea el panel en tiempo real"""
    print("🔍 Buscando proceso del Panel de VMs...")
    
    proc = find_panel_process()
    if not proc:
        print("❌ Panel no encontrado. Asegúrate de que esté corriendo.")
        sys.exit(1)
    
    print(f"✅ Panel encontrado (PID: {proc.pid})")
    print(f"📊 Iniciando monitoreo en tiempo real...\n")
    print("=" * 80)
    
    # Estadísticas acumuladas
    max_cpu = 0
    max_memory = 0
    avg_cpu_samples = []
    start_time = time.time()
    
    try:
        while True:
            try:
                # CPU
                cpu_percent = proc.cpu_percent(interval=1)
                avg_cpu_samples.append(cpu_percent)
                if len(avg_cpu_samples) > 60:
                    avg_cpu_samples.pop(0)
                avg_cpu = sum(avg_cpu_samples) / len(avg_cpu_samples)
                max_cpu = max(max_cpu, cpu_percent)
                
                # Memoria
                mem_info = proc.memory_info()
                mem_rss = mem_info.rss  # Resident Set Size
                mem_vms = mem_info.vms  # Virtual Memory Size
                mem_percent = proc.memory_percent()
                max_memory = max(max_memory, mem_rss)
                
                # Threads
                num_threads = proc.num_threads()
                
                # Tiempo de ejecución
                elapsed = time.time() - start_time
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                
                # Limpiar pantalla y mostrar
                os.system('clear' if os.name != 'nt' else 'cls')
                
                print("=" * 80)
                print(f"🖥️  MONITOR DEL PANEL DE VMs - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 80)
                print(f"\n📍 Proceso: PID {proc.pid} | Tiempo: {elapsed_str}\n")
                
                # CPU
                print("⚡ CPU:")
                print(f"   Actual:   {cpu_percent:6.2f}%")
                print(f"   Promedio: {avg_cpu:6.2f}%")
                print(f"   Máximo:   {max_cpu:6.2f}%")
                
                # Barra de CPU
                cpu_bar_length = int(cpu_percent / 2)
                cpu_bar = "█" * cpu_bar_length + "░" * (50 - cpu_bar_length)
                cpu_color = "🟢" if cpu_percent < 5 else ("🟡" if cpu_percent < 15 else "🔴")
                print(f"   {cpu_color} [{cpu_bar}] {cpu_percent:.1f}%\n")
                
                # Memoria
                print("💾 Memoria:")
                print(f"   RSS:      {format_bytes(mem_rss):>12} ({mem_percent:.2f}%)")
                print(f"   VMS:      {format_bytes(mem_vms):>12}")
                print(f"   Máximo:   {format_bytes(max_memory):>12}")
                
                # Barra de memoria
                mem_bar_length = int(mem_percent * 5)
                mem_bar = "█" * mem_bar_length + "░" * (50 - mem_bar_length)
                mem_color = "🟢" if mem_percent < 1 else ("🟡" if mem_percent < 2 else "🔴")
                print(f"   {mem_color} [{mem_bar}] {mem_percent:.2f}%\n")
                
                # Threads
                print(f"🧵 Threads: {num_threads}\n")
                
                # Estadísticas
                print("📈 Estadísticas:")
                print(f"   Muestras CPU:     {len(avg_cpu_samples)}")
                print(f"   CPU Promedio:     {avg_cpu:.2f}%")
                print(f"   CPU Máximo:       {max_cpu:.2f}%")
                print(f"   Memoria Máxima:   {format_bytes(max_memory)}")
                
                # Evaluación
                print("\n🎯 Evaluación:")
                if avg_cpu < 5 and mem_percent < 1:
                    print("   ✅ Excelente - Uso de recursos muy bajo")
                elif avg_cpu < 10 and mem_percent < 2:
                    print("   ✅ Bueno - Uso de recursos aceptable")
                elif avg_cpu < 20 and mem_percent < 3:
                    print("   ⚠️  Moderado - Considerar optimizaciones")
                else:
                    print("   ❌ Alto - Revisar posibles problemas")
                
                print("\n" + "=" * 80)
                print("Presiona Ctrl+C para detener el monitoreo")
                
            except psutil.NoSuchProcess:
                print("\n❌ El panel se cerró")
                break
                
    except KeyboardInterrupt:
        print("\n\n✅ Monitoreo detenido")
        print("\n📊 Resumen Final:")
        print(f"   Tiempo total:     {elapsed_str}")
        print(f"   CPU Promedio:     {avg_cpu:.2f}%")
        print(f"   CPU Máximo:       {max_cpu:.2f}%")
        print(f"   Memoria Máxima:   {format_bytes(max_memory)}")
        print()

if __name__ == "__main__":
    monitor_panel()
