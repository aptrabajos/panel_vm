#!/usr/bin/env python3
"""
Script de debug para analizar los datos de memoria de las VMs
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from vm_manager import VMManager
import json

def main():
    vm_manager = VMManager()
    
    print("🔍 Debug de Memoria de VMs")
    print("=" * 50)
    
    for vm_name in vm_manager.vm_names:
        print(f"\n📊 VM: {vm_name}")
        print("-" * 30)
        
        debug_info = vm_manager.debug_vm_memory(vm_name)
        
        # Mostrar dommemstat
        print("📋 dommemstat:")
        if debug_info['dommemstat']:
            if isinstance(debug_info['dommemstat'], dict):
                for key, value in debug_info['dommemstat'].items():
                    if isinstance(value, int):
                        print(f"  {key}: {value:,} KB ({value/1024/1024:.2f} GB)")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  Error: {debug_info['dommemstat']}")
        else:
            print("  No disponible")
        
        # Mostrar domstats (solo memoria)
        print("\n📊 domstats (memoria):")
        if debug_info['domstats']:
            if isinstance(debug_info['domstats'], dict):
                for key, value in debug_info['domstats'].items():
                    if isinstance(value, int):
                        print(f"  {key}: {value:,} KB ({value/1024/1024:.2f} GB)")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  Error: {debug_info['domstats']}")
        else:
            print("  No disponible")
        
        # Mostrar cálculos
        print("\n🧮 Cálculos:")
        if debug_info['calculations']:
            calc = debug_info['calculations']
            method = calc.get('method', 'desconocido')
            print(f"  Método: {method}")
            print(f"  Memoria asignada: {calc['mem_total_gb']:.2f} GB")
            print(f"  Memoria usada: {calc['mem_used_gb']:.2f} GB")
            print(f"  Porcentaje usado: {calc['mem_percent']:.1f}%")
            if method == 'memory.unused':
                print(f"  Detalle: {calc['mem_used_kb']:,} KB usados de {calc['mem_actual_kb']:,} KB asignados")
                print(f"  (calculado como: {calc['mem_actual_kb']:,} - {calc['mem_unused_kb']:,} = {calc['mem_used_kb']:,} KB)")
            elif method == 'RSS':
                print(f"  Detalle: {calc['mem_rss_kb']:,} KB RSS de {calc['mem_actual_kb']:,} KB asignados")
                print(f"  (RSS es la memoria realmente usada en el host)")
        else:
            print("  No se pudieron calcular métricas")
        
        # Mostrar estado de la VM
        vms = vm_manager.list_all_vms()
        vm_info = next((vm for vm in vms if vm['name'] == vm_name), None)
        if vm_info:
            print(f"\n🔄 Estado: {vm_info['state']} ({'Ejecutándose' if vm_info['running'] else 'Detenida'})")
        else:
            print("\n❌ VM no encontrada")

if __name__ == "__main__":
    main()
