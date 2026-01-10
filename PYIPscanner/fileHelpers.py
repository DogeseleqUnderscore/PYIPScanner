from netTools import *
import os

#Why is only one function here :sob:

def load_ips_from_file(path: str) -> List[str]:
    if not os.path.exists(path):
        print_error(f"File not found: {path}")
        return []
    out: List[str] = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '/' in line:
                out.extend(parse_cidr(line))
            elif '-' in line:
                out.extend(expand_range(line))
            elif ',' in line:
                out.extend(parse_ip_list(line))
            else:
                out.append(line)
    return out