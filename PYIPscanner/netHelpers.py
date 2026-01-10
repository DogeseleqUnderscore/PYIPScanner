from typing import List, Optional, Tuple
from CLIhelpers import *
import re

_IP_PATTERN = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')

def is_valid_ip(ip: str) -> bool:
    match = _IP_PATTERN.match(ip)
    if not match:
        return False
    return all(0 <= int(octet) <= 255 for octet in match.groups())

def parse_ip_list(csv: str) -> List[str]:
    items = [x.strip() for x in csv.split(',') if x.strip()]
    return items

def ip_to_int(ip: str) -> int:
    parts = list(map(int, ip.split('.')))
    return (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]

def int_to_ip(n: int) -> str:
    return f"{(n >> 24) & 255}.{(n >> 16) & 255}.{(n >> 8) & 255}.{n & 255}"

def parse_cidr(cidr: str) -> List[str]:
    if '/' not in cidr:
        return [cidr.strip()]

    try:
        ip_part, prefix_str = cidr.split('/', 1)
        prefix = int(prefix_str)

        if not (0 <= prefix <= 32):
            print_error(f"Invalid CIDR prefix: /{prefix} (must be 0-32)")
            return []

        if not is_valid_ip(ip_part):
            print_error(f"Invalid IP in CIDR: {ip_part}")
            return []

        ip_int = ip_to_int(ip_part)

        mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF

        network = ip_int & mask

        broadcast = network | (~mask & 0xFFFFFFFF)

        num_ips = broadcast - network + 1
        if num_ips > 10000:
            print_warn(f"CIDR range contains {num_ips} IPs. This may take a while...")
            response = input("Continue? (y/n): ")
            if response.lower() != 'y':
                print_error("Scan cancelled by user.")
                return []

        return [int_to_ip(i) for i in range(network, broadcast + 1)]

    except ValueError as e:
        print_error(f"Error parsing CIDR notation: {e}")
        return []

def expand_range(range_str: str) -> List[str]:
    if '/' in range_str:
        return parse_cidr(range_str)

    if '-' not in range_str:
        return [range_str.strip()]

    a, b = [x.strip() for x in range_str.split('-', 1)]
    if '.' not in b:
        base_parts = a.split('.')[:3]
        start_last = int(a.split('.')[-1])
        end_last = int(b)
        start_base = '.'.join(base_parts) + '.'
        return [start_base + str(i) for i in range(start_last, end_last + 1)]
    else:
        start = ip_to_int(a)
        end = ip_to_int(b)
        if start > end:
            start, end = end, start
        return [int_to_ip(i) for i in range(start, end + 1)]

def parse_port_range(range_str: str) -> List[int]:
    out: List[int] = []
    parts = [p.strip() for p in range_str.split(',') if p.strip()]
    for p in parts:
        if '-' in p:
            a_str, b_str = [x.strip() for x in p.split('-', 1)]
            try:
                a = int(a_str)
                b = int(b_str)
            except ValueError:
                print_warn(f"Invalid port range segment: {p}, skipping.")
                continue
            if a > b:
                a, b = b, a
            out.extend(list(range(a, b + 1)))
        else:
            try:
                out.append(int(p))
            except ValueError:
                print_warn(f"Invalid port value: {p}, skipping.")
    return sorted(set(out))