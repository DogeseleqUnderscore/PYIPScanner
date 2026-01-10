from CLIhelpers import *
from netHelpers import *
import concurrent.futures
import subprocess
import platform
import socket
import re

_IP_PATTERN = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
_TIME_PATTERN = re.compile(r'time[=<](\d+(?:\.\d+)?)', re.IGNORECASE)
_TTL_PATTERN = re.compile(r'ttl[=](\d+)', re.IGNORECASE)

SYSTEM = platform.system().lower()


def _run_ping(ip: str, timeout_sec: int = 1) -> Tuple[bool, Optional[str]]:
    try:
        startupinfo = None
        creation_flags = 0

        if SYSTEM == 'windows':
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                creation_flags = subprocess.CREATE_NO_WINDOW

            cmd = ['ping', '-n', '1', '-w', str(timeout_sec * 1000), ip]
        else:
            cmd = ['ping', '-c', '1', '-W', str(timeout_sec), ip]

        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding='utf-8',
            timeout=timeout_sec + 0.5,
            startupinfo=startupinfo,
            creationflags=creation_flags
        )

        success = 'ttl=' in res.stdout.lower()
        return success, res.stdout if success else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False, None

def is_alive(ip: str, timeout_sec: int = 1) -> bool:
    success, _ = _run_ping(ip, timeout_sec)
    return success

def is_port_open(ip: str, port: int, timeout: float = 0.5) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip, port))
        return result == 0
    except (OSError, socket.error):
        return False
    finally:
        sock.close()

def get_open_ports(ip: str, ports: List[int] = None, timeout: float = 0.5, max_workers: int = 100) -> List[int]:
    if ports is None:
        ports = [443, 80, 8080, 9443, 8123, 8008, 8888, 8088, 5000, 3000, 22, 21, 3306, 5432, 6379]

    if not ports:
        return []

    open_ports = []
    workers = min(max_workers, len(ports), 200)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        future_to_port = {ex.submit(is_port_open, ip, port, timeout): port for port in ports}

        for future in concurrent.futures.as_completed(future_to_port):
            port = future_to_port[future]
            try:
                if future.result():
                    open_ports.append(port)
            except Exception:
                pass

    return sorted(open_ports)

def get_ping(ip: str, timeout_sec: int = 2) -> Optional[float]:
    success, stdout = _run_ping(ip, timeout_sec)

    if not success or not stdout:
        return None

    match = _TIME_PATTERN.search(stdout)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return None

def get_ttl(ip: str, timeout_sec: int = 1) -> Optional[int]:
    success, stdout = _run_ping(ip, timeout_sec)

    if not success or not stdout:
        return None

    match = _TTL_PATTERN.search(stdout)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None

def detect_os_from_ttl(ttl: Optional[int]) -> str:
    if ttl is None:
        return '[N/D]'

    if ttl > 240:
        return f'Other'
    elif ttl > 120:
        return f'Windows'
    elif ttl > 60:
        return f'Linux/Unix/MacOS'
    elif ttl > 30:
        return f'Linux/Unix'
    else:
        return f'Unknown'

def get_mac_address(ip: str) -> Optional[str]:
    try:
        if SYSTEM == 'windows':
            result = subprocess.run(
                ['arp', '-a', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                encoding='utf-8',
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            mac_pattern = re.compile(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})')
            match = mac_pattern.search(result.stdout)
            if match:
                mac = match.group(0).replace('-', ':').upper()
                return mac
        else:
            result = subprocess.run(
                ['arp', '-n', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                encoding='utf-8',
                timeout=2
            )

            mac_pattern = re.compile(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}')
            match = mac_pattern.search(result.stdout)
            if match:
                return match.group(0).upper()

        return None
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return None

def get_hostname(ip: str, timeout: float = 1.0) -> Optional[str]:
    try:
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        finally:
            socket.setdefaulttimeout(old_timeout)
    except (socket.herror, socket.gaierror, socket.timeout):
        return None

def batch_check_alive(ips: List[str], timeout_sec: int = 1, max_workers: int = 50) -> dict:
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_to_ip = {ex.submit(is_alive, ip, timeout_sec): ip for ip in ips}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                results[ip] = future.result()
            except Exception:
                results[ip] = False
    return results

def get_full_host_info(ip: str, ports: List[int] = None, port_timeout: float = 0.5,ping_timeout: int = 2, skip_ports: bool = False) -> Tuple[ bool, Optional[str], Optional[float], List[int], Optional[str], Optional[str]]:
    if not is_valid_ip(ip):
        return False, None, None, [], None, None

    alive = is_alive(ip, timeout_sec=1)

    if not alive:
        return False, None, None, [], None, None

    # Get TTL for OS detection
    ttl = get_ttl(ip, timeout_sec=1)
    os_guess = detect_os_from_ttl(ttl)

    max_workers = 4 if skip_ports else 4

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        hostname_future = ex.submit(get_hostname, ip, 1.0)
        ping_future = ex.submit(get_ping, ip, ping_timeout)
        mac_future = ex.submit(get_mac_address, ip)

        if not skip_ports:
            ports_future = ex.submit(get_open_ports, ip, ports, port_timeout, 100)

        try:
            hostname = hostname_future.result(timeout=2.0)
        except Exception:
            hostname = None

        try:
            ping = ping_future.result(timeout=ping_timeout + 1)
        except Exception:
            ping = None

        try:
            mac = mac_future.result(timeout=3.0)
        except Exception:
            mac = None

        if not skip_ports:
            try:
                open_ports = ports_future.result(timeout=30.0)
            except Exception:
                open_ports = []
        else:
            open_ports = []

    return alive, hostname, ping, open_ports, mac, os_guess


