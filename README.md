# PYIP Scanner v2.1

An simple, lightweight and pure¹ python CLI program with ANSI colors that scans your network and shows you what devices you have at what IP, their open ports and more! 

Inspired by **Angry IP Scanner**

¹It has import of one library however the scanner can run without it.
## Features

- **Fast Multi-threaded Scanning** - Scan hundreds of IPs concurrently with configurable worker threads
- **Comprehensive Host Detection** - Identifies alive hosts, open ports, hostnames, and MAC addresses
- **OS Fingerprinting** - Detects operating systems based on TTL values
- **Vendor Identification** - Optional MAC address vendor lookup (requires BeautifulSoup4 library)
- **Wake-on-LAN Support** - Built-in WOL server for remote device wake-up
- **Flexible IP Ranges** - Supports single IPs, ranges, CIDR notation, and file imports
- **CSV Export** - Export scan results for further analysis
- **Colorized Output** - Easy-to-read terminal output with status indicators

## Requirements

- Python 3.7+ (3.13 recommended)
- **Optional**: `beautifulsoup4` (for MAC vendor lookup)

## Installation

1. Clone or download this repository
2. (Optional) Install beautifulsoup4 for vendor lookup:
```bash
pip install beautifulsoup4
```

## Usage

### Basic Scan

Scan the default range (192.168.0.1-255):
```bash
python main.py
```

### Custom IP Range

```bash
# Scan a specific range
python main.py --range 192.168.1.1-192.168.1.100

# Shorthand notation
python main.py --range 192.168.1.1-100

# CIDR notation
python main.py --range 192.168.1.0/24
```

### Specific IPs

```bash
# Comma-separated list
python main.py --ips 192.168.1.1,192.168.1.10,192.168.1.50
```

### IP File Import

```bash
# Load IPs from a file (supports ranges, CIDR, and comments)
python main.py --file ip_list.txt
```

Example `ip_list.txt`:
```
# My network devices
192.168.1.1
192.168.1.10-20
192.168.1.0/28
```

### Port Scanning

```bash
# Custom ports
python main.py --range 192.168.1.0/24 --ports 80,443,8080,3389

# Port ranges
python main.py --range 192.168.1.0/24 --port-range 1-1000,3389,8000-9000

# Skip port scanning
python main.py --range 192.168.1.0/24 --skip-ports
```

### Performance Tuning

```bash
# Adjust concurrent workers (default: 200)
python main.py --range 192.168.1.0/24 --workers 500
```

### Filtering Results

```bash
# Ignore dead hosts
python main.py --range 192.168.1.0/24 --ignore-types dead

# Show only hosts with open ports
python main.py --range 192.168.1.0/24 --ignore-types dead,alive
```

### Export Results

```bash
# Export to CSV
python main.py --range 192.168.1.0/24 --export-csv results.csv
```

### Vendor Lookup

```bash
# Skip vendor lookup (faster)
python main.py --range 192.168.1.0/24 --skip-vendor
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--range` | IP range (e.g., 192.168.1.1-255 or 192.168.1.0/24) |
| `--ips` | Comma-separated IP addresses |
| `--file` | File containing IPs/ranges (one per line) |
| `--ports` | Comma-separated ports to scan |
| `--port-range` | Port ranges (e.g., 1-1000,3389,8000-9000) |
| `--workers` | Max concurrent IP workers (default: 200) |
| `--ignore-types` | Ignore host types: host,alive,dead |
| `--export-csv` | Export results to CSV file |
| `--skip-ports` | Skip port scanning entirely |
| `--skip-vendor` | Skip MAC vendor lookup |

## Output

The scanner displays results with color-coded, square status indicators:

- **Blue** - Alive host (no open ports detected)
- **Green** - Host with open ports
- **Red** - Dead/unreachable host

The scanner also displays following information:
- Status indicator
- IPv4 address
- Hostname
- Open ports (see below)
- Ping (ms)
- MAC address
- Vendor/Manufacturer (network connection required)
- OS (From TTL value, not really accurate)
- WOL link

## Default Ports

When no ports are specified, these common ports are scanned:
```
443, 80, 8080, 9443, 8123, 8008, 8888, 8088, 5000, 3000, 22, 21, 3306, 5432, 6379
```

## Performance Tips

- Use `--skip-vendor` for faster scans (skips web lookups)
- Use `--skip-ports` if you only need host discovery
- Adjust `--workers` based on your system (higher = faster but more resource intensive)
- Use `--ignore-types dead` to reduce output clutter

## License

This project is licensed under the GNU General Public License v3.0 License.

Check the LICENSE file for details.

## Privacy
No data is being collected, stored, shared and or transmitted. All scanning is done locally on your machine and network.
MAC address vendor lookup uses scraping from maclookup.app but no data about you or your scan is sent to them.
The only data sent to it is first 8 characters/first 3 parts of the MAC, also know as OUI, it only allows for vendor lookup and nothing else.
If you don't want to have any data sent you can:
- Use `--skip-vendor` to disable vendor lookup
- Set variable `vendor_disabled` to ``True`` in line 19 in main.py file
