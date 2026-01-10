from CLIhelpers import *
import urllib.request
import subprocess
import time

def _get_vendor_from_mac(macaddr: str, debug: bool = False):
    from bs4 import BeautifulSoup

    mac_prefix = macaddr[:8]
    url = f'https://maclookup.app/search/result?mac={mac_prefix}'

    if debug:
        print_info(f"[DEBUG] [MAC lookup] Looking up vendor for MAC: {macaddr}")
        print_info(f"[DEBUG] [MAC lookup] Using MAC prefix: {mac_prefix}")
        print_info(f"[DEBUG] [MAC lookup] URL: {url}")

    time.sleep(0.5)

    try:
        req = urllib.request.Request(url=url)

        with urllib.request.urlopen(req) as f:
            html_doc = f.read()
            if debug:
                print_info(f"[DEBUG] [MAC lookup] Received {len(html_doc)} bytes of HTML")

            soup = BeautifulSoup(html_doc, 'html.parser')
            vendor_elem = soup.find('h1')

            if vendor_elem:
                vendor_text = vendor_elem.text.strip()
                if debug:
                    print_success(f"[DEBUG] [MAC lookup] Found vendor: {vendor_text}")
                return vendor_text
            else:
                if debug:
                    print_warn(f"[DEBUG] [MAC lookup] Failed to find vendor information!")
                return None

    except Exception as e:
        print_error(f"[MAC lookup] Error during lookup: {e}")
        return None

def install_soup():
    process = subprocess.run(['pip', 'install', 'beautifulsoup4'], shell=True, capture_output=True, check=True)
    if process.stderr:
        print_warn(process.stderr.decode())

    try:
        manufacturer = _get_vendor_from_mac("08:00:27:00:00:01")
        if manufacturer:
            print_success("Successfully installed beautifulsoup4!")
    except Exception as e:
        if str(e) == "No module named 'bs4'":
            print_error("Failed to install beautifulsoup4 package!")
            exit(0)

def check_if_there_will_be_lunch_today():
    try:
        manufacturer = _get_vendor_from_mac("08:00:27:00:00:01")
        if manufacturer:
            return True
        else:
            return False
    except Exception as e:
        if str(e) == "No module named 'bs4'":
            print_error(f"You don't have the {CSI}1;3;97mBeautifulSoup{RESET} library installed in your current {CSI}1;93mpython{RESET} interpretter!"
                        f"\nInstall it by using:"
                        f"\n{CSI}1;97mpip install beautifulsoup4{RESET}"
                        f"\n")
            print_info("Do you want to install it now? (Y/N)")
            selection = input(">_")
            selection = selection.lower()

            if len(selection) != 1:
                print_error("Invalid selection!")
                exit()
            elif selection == "n":
                pass
            elif selection == "y":
                print_info("Installing package...")
                install_soup()
            else:
                print_error("Invalid selection!")
                exit()



            return False
        else:
            print_error(f"An wild error was encountered roaming around the code! This is a closer look at it: {e}")
            return False

def get_vendor_from_mac_address_no_this_is_not_made_by_chatgpt_trust_me(macaddr: str, debug: bool = False):
    try:
        manufacturer = _get_vendor_from_mac(macaddr, debug)
        return manufacturer
    except Exception as e:
        if str(e) == "No module named 'bs4'":
            return f"{CSI}2;34m[no lunch :(]"
        else:
            print_error(f"An wild error was encountered roaming around the code! This is a closer look at it: {e}")
            return e













if __name__ == "__main__":
    print(check_if_there_will_be_lunch_today())

    test_macs = [
        "48:9E:BD:B4:EA:25",
        "94:A9:90:6A:46:4C",
        "00:50:56:00:00:01",
        "08:00:27:00:00:01",
    ]

    for mac in test_macs:
        vendor = get_vendor_from_mac_address_no_this_is_not_made_by_chatgpt_trust_me(mac)
        print_info(vendor)
        time.sleep(1)