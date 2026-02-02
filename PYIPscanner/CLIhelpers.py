import math
import re

CSI = "\033["
RESET = "\033[0m"

def print_error(msg):
    print(f"{CSI}1;31m[!!]{RESET} >> {msg}")

def print_warn(msg):
    print(f"{CSI}1;93m[!]{RESET} >> {msg}")

def print_success(msg):
    print(f"{CSI}1;92m[ :D ]{RESET} >> {msg}")

def print_cat(msg):
    print(f"{CSI}1;95m[(◔◡◔)]{RESET} >> {msg}")

def print_info(msg, blinking=False):
    if blinking:
        print(f"{CSI}1;5m[#]{CSI}5m >> {msg}")
    else:
        print(f"{CSI}1m[#]{RESET} >> {msg}")

def status_dead():
    return f"{CSI}1;31m\u25A0{RESET}"

def status_alive():
    return f"{CSI}1;94m\u25A0{RESET}"

def status_host():
    return f"{CSI}1;92m\u25A0{RESET}"




st=False
def pass_st_var():
    global st
    st=True

def print_loading_bar(value, max_value, msg, width=130):
    if st:
        width=30
    if max_value <= 0:
        raise ValueError("max_value must be > 0")

    value = math.floor(value)
    value = max(0, min(value, max_value))

    progress = value / max_value
    filled = int(progress * width)

    bar = f"{CSI}1;107m {RESET}" * filled + f"{CSI}97;1m-{RESET}" * (width - filled)
    percent = progress * 100

    print(f"\r {bar} {percent:6.2f}% {msg}", end="", flush=True)

def truncate(text: str, width: int) -> str:
    if not st:
        if width <= 0:
            return ''
        text = str(text)
        if len(text) <= width:
            return text
        if width <= 3:
            return text[:width]
        return text[: width - 3] + '...'
    else:
        return text




def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def visual_len(text: str) -> int:
    return len(strip_ansi(text))


def pad_colored_text(colored_text: str, target_width: int) -> str:
    current_visual_len = visual_len(colored_text)
    if current_visual_len >= target_width:
        return colored_text
    padding_needed = target_width - current_visual_len
    return colored_text + (' ' * padding_needed)