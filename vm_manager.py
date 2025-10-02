import subprocess
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VMError(Exception):
    """Excepción base para errores de VM"""
    def __init__(self, message: str, error_type: str = "unknown", details: str = ""):
        self.message = message
        self.error_type = error_type
        self.details = details
        super().__init__(self.message)

class VMManager:
    def __init__(self):
        self.connection_uri = "qemu:///system"
        self.vm_names = ["manjaro1", "manjaro2"]
        self.system_ready = False
        self.system_error = None
        self._check_system_requirements()

    def _run_virsh_command(self, args: List[str]) -> Tuple[bool, str, str]:
        """Ejecuta un comando virsh y retorna (éxito, stdout, stderr)"""
        try:
            # Intentar primero sin sudo
            cmd = ["virsh", "-c", self.connection_uri] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Si falla, intentar con pkexec para GUI
            if result.returncode != 0:
                stderr_lower = result.stderr.lower()

                # Si es error de permisos, intentar con pkexec
                if "permission" in stderr_lower or "access denied" in stderr_lower:
                    cmd = ["pkexec", "virsh", "-c", self.connection_uri] + args
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            success = result.returncode == 0
            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            error_msg = f"Comando '{' '.join(args)}' excedió el tiempo de espera"
            logger.error(error_msg)
            return False, "", error_msg
        except FileNotFoundError:
            error_msg = "virsh no está instalado o no se encuentra en el PATH"
            logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Error inesperado ejecutando virsh: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg

    def _parse_virsh_error(self, stderr: str, operation: str) -> Dict[str, str]:
        """Analiza el error de virsh y retorna información estructurada"""
        stderr_lower = stderr.lower()

        error_info = {
            "type": "unknown",
            "message": stderr.strip(),
            "suggestion": ""
        }

        # Errores de conexión
        if "failed to connect" in stderr_lower or "connection refused" in stderr_lower:
            error_info["type"] = "connection"
            error_info["message"] = "No se pudo conectar al servicio de virtualización"
            error_info["suggestion"] = "Ejecuta: sudo systemctl start libvirtd"

        # Errores de permisos
        elif "permission denied" in stderr_lower or "access denied" in stderr_lower:
            error_info["type"] = "permission"
            error_info["message"] = "Permisos insuficientes para la operación"
            error_info["suggestion"] = "Ejecuta: sudo usermod -a -G libvirt $USER y reinicia sesión"

        # VM no encontrada
        elif "domain not found" in stderr_lower or "failed to get domain" in stderr_lower:
            error_info["type"] = "not_found"
            error_info["message"] = "La máquina virtual no existe"
            error_info["suggestion"] = "Verifica el nombre de la VM con: virsh list --all"

        # VM ya está corriendo
        elif "already active" in stderr_lower or "is already active" in stderr_lower:
            error_info["type"] = "already_running"
            error_info["message"] = "La VM ya está en ejecución"
            error_info["suggestion"] = ""

        # VM no está corriendo
        elif "domain is not running" in stderr_lower or "not running" in stderr_lower:
            error_info["type"] = "not_running"
            error_info["message"] = "La VM no está en ejecución"
            error_info["suggestion"] = "Inicia la VM primero"

        # Error de red
        elif "network" in stderr_lower and "error" in stderr_lower:
            error_info["type"] = "network"
            error_info["message"] = "Error de configuración de red"
            error_info["suggestion"] = "Verifica la configuración de red de la VM"

        # Recursos insuficientes
        elif "no space" in stderr_lower or "out of memory" in stderr_lower:
            error_info["type"] = "resources"
            error_info["message"] = "Recursos insuficientes del sistema"
            error_info["suggestion"] = "Libera espacio en disco o memoria RAM"

        return error_info
    
    def list_all_vms(self) -> List[Dict]:
        """Lista todas las VMs con su estado"""
        success, stdout, stderr = self._run_virsh_command(["list", "--all"])
        if not success:
            logger.error(f"Error listando VMs: {stderr}")
            return []

        vms = []
        lines = stdout.strip().split('\n')[2:]  # Saltear headers

        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    vm_id = parts[0] if parts[0] != '-' else None
                    vm_name = parts[1]
                    vm_state = ' '.join(parts[2:])

                    if vm_name in self.vm_names:
                        # Detectar si está ejecutándose (español e inglés)
                        is_running = vm_state in ['running', 'ejecutando']
                        vms.append({
                            'id': vm_id,
                            'name': vm_name,
                            'state': vm_state,
                            'running': is_running
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
    
    def _check_system_requirements(self):
        """Verifica los requisitos del sistema"""
        try:
            # Verificar si virsh está disponible
            result = subprocess.run(["which", "virsh"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("virsh no está instalado o no está en el PATH")
                return
            
            # Verificar si libvirtd está ejecutándose
            result = subprocess.run(["systemctl", "is-active", "libvirtd"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("libvirtd no está ejecutándose")
                return
            
            logger.info("Requisitos del sistema verificados correctamente")
        except Exception as e:
            logger.warning(f"Error verificando requisitos del sistema: {e}")