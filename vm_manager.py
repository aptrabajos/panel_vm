import subprocess
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VMManager:
    def __init__(self):
        self.connection_uri = "qemu:///system"
        self.vm_names = ["manjaro1", "manjaro2"]
    
    def _run_virsh_command(self, args: List[str]) -> tuple[bool, str]:
        """Ejecuta un comando virsh y retorna el resultado"""
        try:
            # Intentar primero sin sudo
            cmd = ["virsh", "-c", self.connection_uri] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Si falla, intentar con sudo usando NOPASSWD o pkexec
            if result.returncode != 0:
                # Intentar con pkexec para GUI
                cmd = ["pkexec", "virsh", "-c", self.connection_uri] + args
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            return success, output
        except subprocess.TimeoutExpired:
            logger.error("Comando virsh expiró")
            return False, "Comando expiró"
        except Exception as e:
            logger.error(f"Error ejecutando comando virsh: {e}")
            return False, str(e)
    
    def list_all_vms(self) -> List[Dict]:
        """Lista todas las VMs con su estado"""
        success, output = self._run_virsh_command(["list", "--all"])
        if not success:
            return []
        
        vms = []
        lines = output.strip().split('\n')[2:]  # Saltear headers
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    vm_id = parts[0] if parts[0] != '-' else None
                    vm_name = parts[1]
                    vm_state = ' '.join(parts[2:])
                    
                    if vm_name in self.vm_names:
                        vms.append({
                            'id': vm_id,
                            'name': vm_name,
                            'state': vm_state,
                            'running': vm_state == 'running'
                        })
        
        return vms
    
    def get_vm_info(self, vm_name: str) -> Optional[Dict]:
        """Obtiene información detallada de una VM"""
        success, output = self._run_virsh_command(["dominfo", vm_name])
        if not success:
            return None
        
        info = {}
        for line in output.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info
    
    def start_vm(self, vm_name: str) -> bool:
        """Inicia una VM"""
        success, output = self._run_virsh_command(["start", vm_name])
        if success:
            logger.info(f"VM {vm_name} iniciada exitosamente")
        else:
            logger.error(f"Error iniciando VM {vm_name}: {output}")
        return success
    
    def shutdown_vm(self, vm_name: str) -> bool:
        """Apaga una VM gracefully"""
        success, output = self._run_virsh_command(["shutdown", vm_name])
        if success:
            logger.info(f"VM {vm_name} siendo apagada")
        else:
            logger.error(f"Error apagando VM {vm_name}: {output}")
        return success
    
    def destroy_vm(self, vm_name: str) -> bool:
        """Fuerza el apagado de una VM"""
        success, output = self._run_virsh_command(["destroy", vm_name])
        if success:
            logger.info(f"VM {vm_name} forzadamente apagada")
        else:
            logger.error(f"Error forzando apagado de VM {vm_name}: {output}")
        return success
    
    def reboot_vm(self, vm_name: str) -> bool:
        """Reinicia una VM"""
        success, output = self._run_virsh_command(["reboot", vm_name])
        if success:
            logger.info(f"VM {vm_name} siendo reiniciada")
        else:
            logger.error(f"Error reiniciando VM {vm_name}: {output}")
        return success
    
    def save_vm(self, vm_name: str) -> bool:
        """Guarda el estado de una VM (managed save)"""
        success, output = self._run_virsh_command(["managedsave", vm_name])
        if success:
            logger.info(f"Estado de VM {vm_name} guardado")
        else:
            logger.error(f"Error guardando estado de VM {vm_name}: {output}")
        return success
    
    def remove_saved_state(self, vm_name: str) -> bool:
        """Elimina el estado guardado de una VM"""
        success, output = self._run_virsh_command(["managedsave-remove", vm_name])
        if success:
            logger.info(f"Estado guardado de VM {vm_name} eliminado")
        else:
            logger.error(f"Error eliminando estado guardado de VM {vm_name}: {output}")
        return success
    
    def get_vm_stats(self, vm_name: str) -> Optional[Dict]:
        """Obtiene estadísticas de CPU y memoria de una VM"""
        try:
            # Obtener estadísticas de CPU
            success, cpu_output = self._run_virsh_command(["cpu-stats", vm_name])
            
            # Obtener información de memoria
            success2, mem_output = self._run_virsh_command(["domstats", "--memory", vm_name])
            
            stats = {
                'cpu_time': None,
                'memory_used': None,
                'memory_total': None
            }
            
            if success and cpu_output:
                for line in cpu_output.split('\n'):
                    if 'cpu_time' in line:
                        stats['cpu_time'] = line.split()[1]
            
            if success2 and mem_output:
                for line in mem_output.split('\n'):
                    if 'balloon.current' in line:
                        stats['memory_used'] = line.split('=')[1]
                    elif 'balloon.maximum' in line:
                        stats['memory_total'] = line.split('=')[1]
            
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de {vm_name}: {e}")
            return None