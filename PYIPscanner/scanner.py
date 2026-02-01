from MAClookup import get_vendor_from_mac_address_no_this_is_not_made_by_chatgpt_trust_me
from typing import List, Optional, Tuple, Callable
from WOL import make_wol_link, WOLButtonServer
from dataclasses import dataclass
import concurrent.futures
from fileHelpers import *
from netTools import *
import threading
import argparse
import time
import csv



DEFAULT_PORTS = [443, 80, 8080, 9443, 8123, 8008, 8888, 8088, 5000, 3000, 22, 21, 3306, 5432, 6379]

NAME = f"{CSI}1;33mPY{RESET}{CSI}35mIP{RESET} {CSI}1mscanner v2.1{RESET}\n"

vendor_disabled=False


@dataclass
class FieldConfig:
    name: str
    key: str
    width: int
    fetch_func: Optional[Callable]
    format_func: Optional[Callable]
    default_value: str = "[N/D]"
    requires_alive: bool = True
    skip_if_ports_disabled: bool = False

class FieldManager:
    def __init__(self):
        self.fields: List[FieldConfig] = []
        self._setup_fields()

    def _setup_fields(self):
        self.fields.append(FieldConfig(
            name="Hostname",
            key="hostname",
            width=15,
            fetch_func=lambda ip, alive: get_hostname(ip) if alive else None,
            format_func=self._format_hostname,
            requires_alive=True
        ))

        self.fields.append(FieldConfig(
            name="Open ports",
            key="open_ports",
            width=12,
            fetch_func=None,
            format_func=self._format_open_ports,
            requires_alive=False,
            skip_if_ports_disabled=True
        ))

        self.fields.append(FieldConfig(
            name="Ping",
            key="ping_ms",
            width=7,
            fetch_func=lambda ip, alive: get_ping(ip) if alive else None,
            format_func=self._format_ping,
            requires_alive=True
        ))

        self.fields.append(FieldConfig(
            name="MAC",
            key="mac",
            width=17,
            fetch_func=lambda ip, alive: get_mac_address(ip) if alive else None,
            format_func=self._format_mac,
            requires_alive=True
        ))

        self.fields.append(FieldConfig(
            name="Vendor",
            key="vendor",
            width=20,
            fetch_func=None,
            format_func=self._format_vendor,
            requires_alive=True
        ))

        self.fields.append(FieldConfig(
            name="OS",
            key="os",
            width=16,
            fetch_func=None,
            format_func=self._format_os,
            requires_alive=True
        ))

        self.fields.append(FieldConfig(
            name="WOL",
            key="wol",
            width=38,
            fetch_func=None,
            format_func=self._format_link,
            requires_alive=True
        ))

    def _format_hostname(self, value: Optional[str]) -> Tuple[str, str]:
        display = value or self._get_field_by_key("hostname").default_value
        plain = display
        if display == "[N/D]":
            colored = f"{CSI}1;31m{display}{RESET}"
        else:
            colored = f"{CSI}1;34m{display}{RESET}"
        return colored, plain

    def _format_open_ports(self, value: Optional[str]) -> Tuple[str, str]:
        display = value or "[N/D]"
        plain = display
        if display == "[N/D]":
            colored = f"{CSI}1;31m{display}{RESET}"
        else:
            colored = f"{CSI}1;34m{display}{RESET}"
        return colored, plain

    def _format_ping(self, value: Optional[int]) -> Tuple[str, str]:
        if value is None or value == "[N/D]" or value == "[err]":
            display = str(value) if value else "[N/D]"
            colored = f"{CSI}1;31m{display}{RESET}"
            plain = display
        else:
            try:
                ping_val = int(value) if isinstance(value, str) else value
                display = f"{ping_val}ms"
                if ping_val <= 25:
                    colored = f"{CSI}1;32m{display}{RESET}"
                elif ping_val <= 50:
                    colored = f"{CSI}1;94m{display}{RESET}"
                elif ping_val <= 75:
                    colored = f"{CSI}1;93m{display}{RESET}"
                else:
                    colored = f"{CSI}1;91m{display}{RESET}"
                plain = display
            except (ValueError, TypeError):
                display = "[N/D]"
                colored = f"{CSI}1;31m{display}{RESET}"
                plain = display
        return colored, plain

    def _format_mac(self, value: Optional[str]) -> Tuple[str, str]:
        display = value or "[N/D]"
        plain = display
        if display == "[N/D]":
            colored = f"{CSI}1;31m{display}{RESET}"
        else:
            colored = f"{CSI}1;36m{display}{RESET}"
        return colored, plain

    def _format_vendor(self, value: Optional[str]) -> Tuple[str, str]:
        display = value or "[N/D]"
        plain = display
        if display == "[N/D]" or display == "[Disabled]":
            colored = f"{CSI}1;31m{display}{RESET}"
        else:
            colored = f"{CSI}1;93m{display}{RESET}"
        return colored, plain

    def _format_os(self, value: Optional[str]) -> Tuple[str, str]:
        display = value or "[N/D]"
        plain = display
        if display == "[N/D]":
            colored = f"{CSI}1;31m{display}{RESET}"
        else:
            colored = f"{CSI}1;35m{display}{RESET}"
        return colored, plain

    def _format_link(self, value: Optional[str]) -> Tuple[str, str]:
        display = value or "[N/D]"
        plain = display
        if display == "[N/D]":
            colored = f"{CSI}1;31m[N/A]{RESET}"
        else:
            colored = f"{CSI}1;34m{display}{RESET}"
        return colored, plain

    def _get_field_by_key(self, key: str) -> Optional[FieldConfig]:
        for field in self.fields:
            if field.key == key:
                return field
        return None

    def get_active_fields(self, skip_ports: bool = False) -> List[FieldConfig]:
        return [f for f in self.fields
                if not (skip_ports and f.skip_if_ports_disabled)]

    def get_csv_fieldnames(self, skip_ports: bool = False) -> List[str]:
        base = ['ip', 'status']
        active_fields = self.get_active_fields(skip_ports)
        return base + [f.key for f in active_fields]








def scan_ip_return(ip: str,
                   field_manager: FieldManager,
                   ports: Optional[List[int]] = None,
                   ip_width: int = 15,
                   skip_ports: bool = False) -> Tuple[str, str, int, dict]:
    if not is_valid_ip(ip):
        return _handle_invalid_ip(ip, field_manager, ip_width, skip_ports)

    alive = is_alive(ip)

    result_data = {
        'ip': ip,
        'status': 'dead'
    }

    active_fields = field_manager.get_active_fields(skip_ports)

    for field in active_fields:
        if field.key == "vendor":
            continue

        if field.key == "open_ports":
            if not skip_ports and alive:
                open_ports = get_open_ports(ip, ports or DEFAULT_PORTS, timeout=0.6,
                                            max_workers=min(100, (len(ports) if ports else len(DEFAULT_PORTS))))
                result_data[field.key] = ','.join(map(str, open_ports)) if open_ports else field.default_value
            else:
                result_data[field.key] = field.default_value

        elif field.key == "os":
            if alive:
                ttl = get_ttl(ip)
                os_guess = detect_os_from_ttl(ttl) if ttl else None
                result_data[field.key] = os_guess or field.default_value
            else:
                result_data[field.key] = field.default_value

        elif field.fetch_func:
            if not field.requires_alive or alive:
                try:
                    value = field.fetch_func(ip, alive)
                    result_data[field.key] = value if value is not None else field.default_value
                except Exception:
                    result_data[field.key] = field.default_value
            else:
                result_data[field.key] = field.default_value
        else:
            result_data[field.key] = field.default_value

    for field in active_fields:
        if field.key == "vendor":
            if alive:
                mac = result_data.get('mac', field.default_value)

                if len(mac) == 17:
                    wol_link = make_wol_link(mac)
                    result_data['wol'] = wol_link if alive else "[N/D]"
                else:
                    result_data['wol'] = "[N/D]"

                if mac and mac != "[N/D]" and mac != "[err]":
                    try:
                        vendor = get_vendor_from_mac_address_no_this_is_not_made_by_chatgpt_trust_me(mac) if not vendor_disabled else "[Disabled]"
                        if vendor and vendor.strip() and vendor != "Not found":
                            result_data[field.key] = vendor
                        else:
                            result_data[field.key] = field.default_value
                    except Exception as e:
                        result_data[field.key] = field.default_value
                else:
                    result_data[field.key] = field.default_value
            else:
                result_data[field.key] = field.default_value

    has_open_ports = not skip_ports and result_data.get('open_ports', '[N/D]') != '[N/D]'

    if alive and has_open_ports:
        status = status_host()
        status_key = "host"
    elif alive:
        status = status_alive()
        status_key = "alive"
    else:
        status = status_dead()
        status_key = "dead"

    result_data['status'] = status_key

    line, plain_length = _build_output_line(ip, ip_width, status, result_data,
                                            active_fields, field_manager)

    return status_key, line, plain_length, result_data


def _handle_invalid_ip(ip: str, field_manager: FieldManager, ip_width: int, skip_ports: bool) -> Tuple[
    str, str, int, dict]:
    result_data = {
        'ip': ip,
        'status': 'invalid'
    }

    active_fields = field_manager.get_active_fields(skip_ports)
    for field in active_fields:
        result_data[field.key] = '[invalid ip]' if field.key == 'hostname' else '[N/D]'

    line, plain_length = _build_output_line(ip, ip_width, status_dead(),
                                            result_data, active_fields, field_manager)

    return "dead", line, plain_length, result_data


def _build_output_line(ip: str, ip_width: int, status: str, result_data: dict, active_fields: List[FieldConfig],
                       field_manager: FieldManager) -> Tuple[str, int]:
    parts = [f"{status} {ip.ljust(ip_width)}"]
    plain_parts = [f"■  {ip.ljust(ip_width)}"]

    for field in active_fields:
        value = result_data.get(field.key)

        if field.key == "ping_ms" and value and value != "[N/D]" and value != "[err]":
            try:
                value = int(value)
            except (ValueError, TypeError):
                value = None

        colored, plain = field.format_func(value)

        if len(plain) > field.width:
            plain = truncate(plain, field.width)
            colored = truncate(plain, field.width)
            colored, plain = field.format_func(plain if plain != "[N/D]" and plain != "[err]" else None)

        plain_padded = plain.ljust(field.width)
        colored_padded = pad_colored_text(colored, field.width)

        parts.append(f"{field.name}: {colored_padded}")
        plain_parts.append(f"{field.name}: {plain_padded}")

    line = " | ".join(parts)
    plain_line = " | ".join(plain_parts)
    plain_length = len(plain_line)

    return line, plain_length


def export_to_csv(results: List[dict], filepath: str, field_manager: FieldManager,
                  skip_ports: bool = False) -> bool:
    try:
        fieldnames = field_manager.get_csv_fieldnames(skip_ports)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                filtered = {k: v for k, v in result.items() if k in fieldnames}
                writer.writerow(filtered)

        return True
    except Exception as e:
        print_error(f"Failed to export CSV: {e}")
        return False


def main():
    global vendor_disabled

    ap = argparse.ArgumentParser(description=NAME)
    group = ap.add_mutually_exclusive_group(required=False)
    group.add_argument('--range',
                       help='Range: 192.168.0.1-192.168.0.255 or 192.168.0.1-255 (shorthand) or CIDR: 192.168.0.0/24',
                       default=127)
    group.add_argument('--ips', help='Comma separated IPs: 192.168.0.1,192.168.0.3')
    group.add_argument('--file', help='File with IPs/ranges/CIDR (one per line), supports comments (#)')
    ap.add_argument('--ports', help='Comma separated ports (default common ports)', default=None)
    ap.add_argument('--port-range', help='Ports or ranges like 1-1000 or 1-100,200,300-310', default=None)
    ap.add_argument('--workers', help='Max concurrent IP workers', type=int, default=200)
    ap.add_argument('--ignore-types', help='Comma separated types to ignore: host,alive,dead', default=None)
    ap.add_argument('--export-csv', help='Export results to CSV file', default=None)

    ap.add_argument('--skip-ports', action='store_true', help='Skip port scanning')
    ap.add_argument('--skip-vendor', action='store_true', help='Skips vendor from MAC address scraping')

    args = ap.parse_args()

    field_manager = FieldManager()

    ip_list: List[str] = []

    if args.range:
        if args.range == 127:
            print_warn("No --range argument provided, scanning classic range(192.168.0.0/24)")
            ip_list = expand_range("192.168.0.0/24")
        elif args.range == '127.0.0.1':
            print_cat(
                f"Nothing feels like {CSI}1;31m1{CSI}1;32m2{CSI}1;33m7{CSI}1;37m.{CSI}1;34m0{CSI}1;37m.{CSI}1;35m0{CSI}1;37m.{CSI}1;36m1{RESET} doesn't it?")
            ip_list = expand_range("127.0.0.1-127.0.0.1")
        else:
            ip_list = expand_range(args.range)
    elif args.ips:
        ip_list = parse_ip_list(args.ips)
    elif args.file:
        ip_list = load_ips_from_file(args.file)

    ip_list = [ip for ip in ip_list if is_valid_ip(ip)]
    if not ip_list:
        print_error("No valid IPs to scan.")
        return

    ip_list = sorted(set(ip_list), key=ip_to_int)

    ports = None
    if args.port_range:
        ports = parse_port_range(args.port_range)
        if not ports:
            print_warn("No valid ports parsed from --port-range, using default list.")
            ports = None
    elif args.ports:
        try:
            ports = [int(p.strip()) for p in args.ports.split(',') if p.strip()]
        except ValueError:
            print_warn("Invalid port in --ports, using default list.")
            ports = None



    if args.skip_vendor:
        print_info(f"Vendor scraping {CSI}1mdisabled{RESET} (--skip-vendor)", False)
        vendor_disabled = True

    if args.skip_ports:
        print_info(f"Port scanning {CSI}1mdisabled{RESET} (--skip-ports)", False)
        ports = None





    ignore_set = set()
    if args.ignore_types:
        requested = {x.strip().lower() for x in args.ignore_types.split(',') if x.strip()}
        allowed = {'host', 'alive', 'dead'}
        invalid = requested - allowed
        if invalid:
            print_warn(f"Ignoring invalid types in --ignore-types: {', '.join(sorted(invalid))}")
        ignore_set = requested & allowed
        print_info(f"Ignoring types: {', '.join(sorted(ignore_set))}", False)

    total = len(ip_list)
    ip_width = max(len(ip) for ip in ip_list)

    print_info(f"Starting scan of {total} IP(s) with up to {args.workers} workers...\n", True)

    start_time = time.time()
    separator_length = 0
    csv_results = []

    dead = 0
    alive = 0
    host = 0

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = [
                ex.submit(scan_ip_return, ip, field_manager, ports, ip_width, args.skip_ports)
                for ip in ip_list
            ]

            result = []
            print_loading_bar(0, total, "")

            for idx, fut in enumerate(futures, start=1):
                try:
                    status_key, line, plain_length, result_data = fut.result()
                    separator_length = plain_length
                    csv_results.append(result_data)

                    if result_data["status"] == 'dead':
                        dead += 1
                    elif result_data["status"] == 'alive':
                        alive += 1
                    elif result_data["status"] == 'host':
                        host += 1

                except Exception as e:
                    error_data = {
                        'ip': ip_list[idx - 1],
                        'status': 'error'
                    }
                    active_fields = field_manager.get_active_fields(args.skip_ports)
                    for field in active_fields:
                        error_data[field.key] = '[err]'

                    line, plain_length = _build_output_line(
                        ip_list[idx - 1], ip_width, status_dead(),
                        error_data, active_fields, field_manager
                    )
                    line += f" ({e})"
                    separator_length = plain_length
                    csv_results.append(error_data)
                    status_key = "dead"

                if status_key not in ignore_set:
                    result.append(f"{'-' * separator_length}\n{line}")

                print_loading_bar(idx, total, f"({idx}/{total} scanned)")

    except KeyboardInterrupt:
        print_warn("Interrupted by user, shutting down workers.")

    server = WOLButtonServer(port=2)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    #results
    print("\n\n")
    for thing in result:
        print(thing)

    if separator_length > 0:
        print(f"{'-' * separator_length}")

    #summary
    end_time = time.time()
    duration = end_time - start_time

    print("\n")
    print_success(f"Scan of {CSI}1;97m{total}{RESET} completed in {CSI}1;97m{duration:.2f}{RESET} seconds!")
    print_success(f"It is about {CSI}1;97m{math.floor(total / duration)} IPs/sec{RESET} or one {CSI}1;97mIP/{(duration / total):.2f} sec{RESET}.")
    print("\n")
    print_success(f"{CSI}31mDead IP(s):{CSI}1;91m {dead} ({dead}/{total}){RESET}")
    print_success(f"{CSI}34mAlive IP(s):{CSI}1;94m {alive} ({alive}/{total}){RESET}")
    print_success(f"{CSI}32mIP(s) with open port(s):{CSI}1;92m {host} ({host}/{total}){RESET}")
    print("\n")
    print_success(f"{CSI}33mTotal:{CSI}1;93m {host + alive} ({host + alive}/{total}){RESET}")

    if args.export_csv:
        print_info(f"Exporting results to {args.export_csv}...", False)
        if export_to_csv(csv_results, args.export_csv, field_manager, args.skip_ports):
            print_success(f"Successfully exported {len(csv_results)} results to {args.export_csv}")
        else:
            print_error(f"Failed to export results to CSV")

def scan():
    print(NAME)
    main()
    input()

if __name__ == "__main__":
    scan()