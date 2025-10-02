import subprocess
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

    def _parse_virsh_error(self, stderr: str, _operation: str) -> Dict[str, str]:
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
        success, stdout, stderr = self._run_virsh_command(["dominfo", vm_name])
        if not success:
            logger.error(f"Error obteniendo info de {vm_name}: {stderr}")
            return None

        info = {}
        for line in stdout.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()

        return info

    def _validate_vm_exists(self, vm_name: str) -> bool:
        """Valida que la VM exista"""
        vms = self.list_all_vms()
        return any(vm['name'] == vm_name for vm in vms)

    def _validate_vm_running(self, vm_name: str) -> bool:
        """Valida que la VM esté corriendo"""
        vms = self.list_all_vms()
        vm = next((v for v in vms if v['name'] == vm_name), None)
        return vm is not None and vm['running']

    def start_vm(self, vm_name: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Inicia una VM. Retorna (éxito, info_error)"""
        # Validar que existe
        if not self._validate_vm_exists(vm_name):
            error_info = {
                "type": "not_found",
                "message": f"La VM '{vm_name}' no existe en el sistema",
                "suggestion": "Verifica el nombre de la VM"
            }
            logger.error(f"VM {vm_name} no encontrada")
            return False, error_info

        # Validar que no esté ya corriendo
        if self._validate_vm_running(vm_name):
            error_info = {
                "type": "already_running",
                "message": f"La VM '{vm_name}' ya está en ejecución",
                "suggestion": ""
            }
            logger.warning(f"VM {vm_name} ya está corriendo")
            return False, error_info

        success, _stdout, stderr = self._run_virsh_command(["start", vm_name])
        if success:
            logger.info(f"VM {vm_name} iniciada exitosamente")
            return True, None
        else:
            error_info = self._parse_virsh_error(stderr, "start")
            logger.error(f"Error iniciando VM {vm_name}: {stderr}")
            return False, error_info

    def shutdown_vm(self, vm_name: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Apaga una VM gracefully. Retorna (éxito, info_error)"""
        if not self._validate_vm_running(vm_name):
            error_info = {
                "type": "not_running",
                "message": f"La VM '{vm_name}' no está en ejecución",
                "suggestion": "No se puede apagar una VM que no está corriendo"
            }
            logger.warning(f"VM {vm_name} no está corriendo")
            return False, error_info

        success, _stdout, stderr = self._run_virsh_command(["shutdown", vm_name])
        if success:
            logger.info(f"VM {vm_name} siendo apagada")
            return True, None
        else:
            error_info = self._parse_virsh_error(stderr, "shutdown")
            logger.error(f"Error apagando VM {vm_name}: {stderr}")
            return False, error_info

    def destroy_vm(self, vm_name: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Fuerza el apagado de una VM. Retorna (éxito, info_error)"""
        if not self._validate_vm_running(vm_name):
            error_info = {
                "type": "not_running",
                "message": f"La VM '{vm_name}' no está en ejecución",
                "suggestion": "No se puede forzar el apagado de una VM que no está corriendo"
            }
            logger.warning(f"VM {vm_name} no está corriendo")
            return False, error_info

        success, _stdout, stderr = self._run_virsh_command(["destroy", vm_name])
        if success:
            logger.info(f"VM {vm_name} forzadamente apagada")
            return True, None
        else:
            error_info = self._parse_virsh_error(stderr, "destroy")
            logger.error(f"Error forzando apagado de VM {vm_name}: {stderr}")
            return False, error_info

    def reboot_vm(self, vm_name: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Reinicia una VM. Retorna (éxito, info_error)"""
        if not self._validate_vm_running(vm_name):
            error_info = {
                "type": "not_running",
                "message": f"La VM '{vm_name}' no está en ejecución",
                "suggestion": "No se puede reiniciar una VM que no está corriendo"
            }
            logger.warning(f"VM {vm_name} no está corriendo")
            return False, error_info

        success, _stdout, stderr = self._run_virsh_command(["reboot", vm_name])
        if success:
            logger.info(f"VM {vm_name} siendo reiniciada")
            return True, None
        else:
            error_info = self._parse_virsh_error(stderr, "reboot")
            logger.error(f"Error reiniciando VM {vm_name}: {stderr}")
            return False, error_info

    def save_vm(self, vm_name: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Guarda el estado de una VM (managed save). Retorna (éxito, info_error)"""
        if not self._validate_vm_running(vm_name):
            error_info = {
                "type": "not_running",
                "message": f"La VM '{vm_name}' no está en ejecución",
                "suggestion": "Solo se puede guardar el estado de una VM en ejecución"
            }
            logger.warning(f"VM {vm_name} no está corriendo")
            return False, error_info

        success, _stdout, stderr = self._run_virsh_command(["managedsave", vm_name])
        if success:
            logger.info(f"Estado de VM {vm_name} guardado")
            return True, None
        else:
            error_info = self._parse_virsh_error(stderr, "save")
            logger.error(f"Error guardando estado de VM {vm_name}: {stderr}")
            return False, error_info

    def remove_saved_state(self, vm_name: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """Elimina el estado guardado de una VM. Retorna (éxito, info_error)"""
        success, _stdout, stderr = self._run_virsh_command(["managedsave-remove", vm_name])
        if success:
            logger.info(f"Estado guardado de VM {vm_name} eliminado")
            return True, None
        else:
            error_info = self._parse_virsh_error(stderr, "remove_saved_state")
            logger.error(f"Error eliminando estado guardado de VM {vm_name}: {stderr}")
            return False, error_info
    
    def get_vm_stats(self, vm_name: str) -> Optional[Dict]:
        """Obtiene estadísticas de CPU y memoria de una VM"""
        try:
            # Obtener estadísticas de CPU
            success, cpu_output, cpu_stderr = self._run_virsh_command(["cpu-stats", vm_name])

            # Obtener información de memoria
            success2, mem_output, mem_stderr = self._run_virsh_command(["domstats", "--memory", vm_name])

            stats = {
                'cpu_time': None,
                'memory_used': None,
                'memory_total': None
            }

            if success and cpu_output:
                for line in cpu_output.split('\n'):
                    if 'cpu_time' in line:
                        stats['cpu_time'] = line.split()[1]
            else:
                logger.debug(f"No se pudieron obtener stats de CPU para {vm_name}: {cpu_stderr}")

            if success2 and mem_output:
                for line in mem_output.split('\n'):
                    if 'balloon.current' in line:
                        stats['memory_used'] = line.split('=')[1]
                    elif 'balloon.maximum' in line:
                        stats['memory_total'] = line.split('=')[1]
            else:
                logger.debug(f"No se pudieron obtener stats de memoria para {vm_name}: {mem_stderr}")

            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de {vm_name}: {e}")
            return None

    def get_vm_ip_address(self, vm_name: str) -> Optional[str]:
        """Obtiene la dirección IP de una VM en ejecución"""
        try:
            # Intentar con múltiples fuentes: lease (DHCP), agent (guest agent), arp
            sources = ['lease', 'agent', 'arp']

            for source in sources:
                success, stdout, stderr = self._run_virsh_command(["domifaddr", vm_name, "--source", source])

                if success and stdout:
                    # Parsear la salida para extraer la IP
                    # Formato: Name       MAC address          Protocol     Address
                    #          vnet0      52:54:00:xx:xx:xx    ipv4         192.168.122.x/24
                    lines = stdout.strip().split('\n')
                    for line in lines[2:]:  # Saltar las primeras 2 líneas (headers)
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 4:
                                # Buscar dirección IPv4
                                for part in parts:
                                    if '.' in part and '/' in part:
                                        # Extraer solo la IP sin la máscara
                                        ip = part.split('/')[0]
                                        # Validar que sea una IP válida
                                        octets = ip.split('.')
                                        if len(octets) == 4 and all(o.isdigit() and 0 <= int(o) <= 255 for o in octets):
                                            logger.debug(f"IP obtenida de {vm_name} usando fuente {source}: {ip}")
                                            return ip

            logger.debug(f"No se pudo obtener IP de {vm_name} con ninguna fuente")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo IP de {vm_name}: {e}")
            return None

    def get_vm_detailed_stats(self, vm_name: str) -> Optional[Dict]:
        """Obtiene estadísticas detalladas de CPU, memoria, disco y red"""
        try:
            success, stdout, stderr = self._run_virsh_command([
                "domstats", "--vcpu", "--memory", "--block", "--interface", vm_name
            ])

            if not success:
                logger.debug(f"No se pudieron obtener stats detalladas de {vm_name}: {stderr}")
                return None

            stats = {
                'vcpu_count': None,
                'vcpu_current': None,
                'vcpu_time': None,
                'memory_actual': None,
                'memory_available': None,
                'memory_unused': None,
                'memory_usable': None,
                'memory_rss': None,
                'block_read_bytes': 0,
                'block_write_bytes': 0,
                'block_read_reqs': 0,
                'block_write_reqs': 0,
                'net_rx_bytes': 0,
                'net_tx_bytes': 0,
                'net_rx_pkts': 0,
                'net_tx_pkts': 0,
            }

            # Parsear la salida
            for line in stdout.split('\n'):
                line = line.strip()
                if '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Estadísticas de vCPU
                if key == 'vcpu.current':
                    stats['vcpu_current'] = int(value)
                elif key == 'vcpu.maximum':
                    stats['vcpu_count'] = int(value)
                elif key.startswith('vcpu.') and key.endswith('.time'):
                    # Sumar el tiempo de todas las vCPUs
                    if stats['vcpu_time'] is None:
                        stats['vcpu_time'] = 0
                    stats['vcpu_time'] += int(value)

                # Estadísticas de memoria (en KB)
                elif key == 'balloon.current':
                    stats['memory_actual'] = int(value)
                elif key == 'balloon.maximum':
                    stats['memory_available'] = int(value)
                elif key == 'memory.unused':
                    stats['memory_unused'] = int(value)
                elif key == 'memory.usable':
                    stats['memory_usable'] = int(value)
                elif key == 'memory.rss':
                    stats['memory_rss'] = int(value)

                # Estadísticas de disco
                elif key.startswith('block.') and '.rd.bytes' in key:
                    stats['block_read_bytes'] += int(value)
                elif key.startswith('block.') and '.wr.bytes' in key:
                    stats['block_write_bytes'] += int(value)
                elif key.startswith('block.') and '.rd.reqs' in key:
                    stats['block_read_reqs'] += int(value)
                elif key.startswith('block.') and '.wr.reqs' in key:
                    stats['block_write_reqs'] += int(value)

                # Estadísticas de red
                elif key.startswith('net.') and '.rx.bytes' in key:
                    stats['net_rx_bytes'] += int(value)
                elif key.startswith('net.') and '.tx.bytes' in key:
                    stats['net_tx_bytes'] += int(value)
                elif key.startswith('net.') and '.rx.pkts' in key:
                    stats['net_rx_pkts'] += int(value)
                elif key.startswith('net.') and '.tx.pkts' in key:
                    stats['net_tx_pkts'] += int(value)

            return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas detalladas de {vm_name}: {e}")
            return None

    def get_vm_vcpu_info(self, vm_name: str) -> Optional[List[Dict]]:
        """Obtiene información detallada de las vCPUs"""
        try:
            success, stdout, stderr = self._run_virsh_command(["vcpuinfo", vm_name])

            if not success:
                logger.debug(f"No se pudo obtener info de vCPU de {vm_name}: {stderr}")
                return None

            vcpus = []
            current_vcpu = {}

            for line in stdout.split('\n'):
                line = line.strip()
                if not line:
                    if current_vcpu:
                        vcpus.append(current_vcpu)
                        current_vcpu = {}
                    continue

                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    current_vcpu[key] = value

            if current_vcpu:
                vcpus.append(current_vcpu)

            return vcpus if vcpus else None
        except Exception as e:
            logger.error(f"Error obteniendo info de vCPU de {vm_name}: {e}")
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