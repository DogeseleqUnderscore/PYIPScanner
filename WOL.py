from netHelpers import is_valid_ip
from CLIhelpers import *
import threading
import socket
import time


def send_wol_magic_packet(mac_address: str, broadcast_ip: str = '255.255.255.255', port: int = 9) -> bool:
    try:
        mac = mac_address.replace(':', '').replace('-', '').upper()

        if len(mac) != 12:
            raise ValueError(f"Invalid MAC address length: {mac_address}")

        try:
            int(mac, 16)
        except ValueError:
            raise ValueError(f"Invalid MAC address format: {mac_address}")

        mac_bytes = bytes.fromhex(mac)
        magic_packet = b'\xFF' * 6 + mac_bytes * 16

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, port))
        sock.close()

        return True

    except Exception as e:
        print_error(f"Error sending WOL packet: {e}")
        return False


class WOLButtonServer:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        self.server_thread = None

    def handle_client(self, client_socket, addr):
        try:
            data = client_socket.recv(4096)
            if not data:
                return

            request = data.decode('utf-8', errors='ignore')
            lines = request.split('\r\n')

            if not lines:
                return

            request_line = lines[0]
            parts = request_line.split()

            if len(parts) < 2:
                self.send_response(client_socket, 400, "Bad Request")
                return

            method = parts[0]
            path = parts[1]

            if path == '/' or path == '/index.html':
                self.serve_dashboard(client_socket)
            elif path == '/favicon.ico':
                self.send_response(client_socket, 404, "Not Found")
            elif method == 'GET':
                self.handle_wol_request(client_socket, path)
            else:
                self.send_response(client_socket, 405, "Method Not Allowed")

        except Exception as e:
            print_error(f"Error handling request: {e}")
            try:
                self.send_response(client_socket, 500, "Internal Server Error")
            except:
                pass
        finally:
            try:
                client_socket.close()
            except:
                pass

    def handle_wol_request(self, client_socket, path):
        path = path.lstrip('/')
        parts = path.split('/')

        if len(parts) == 0 or not parts[0]:
            self.send_response(client_socket, 400, "Missing MAC address")
            return

        mac_address = parts[0]
        broadcast_ip = parts[1] if len(parts) > 1 and parts[1] else '255.255.255.255'

        clean_mac = mac_address.replace(':', '').replace('-', '')

        if len(clean_mac) != 12:
            self.send_response(client_socket, 400, f"Invalid MAC address: {mac_address}")
            return

        try:
            int(clean_mac, 16)
        except ValueError:
            self.send_response(client_socket, 400, f"Invalid MAC address format: {mac_address}")
            return

        if broadcast_ip != '255.255.255.255' and not is_valid_ip(broadcast_ip):
            self.send_response(client_socket, 400, f"Invalid broadcast IP: {broadcast_ip}")
            return

        success = send_wol_magic_packet(mac_address, broadcast_ip)

        if success:
            print_success(f"WOL packet sent to {mac_address}!")
            self.send_html_response(
                client_socket,
                100,
                "")
        else:
            print_error(f"Failed to send magic packet to {mac_address}!")
            self.send_response(client_socket, 500, "Failed to send WOL packet")

    def serve_dashboard(self, client_socket):
        html = f""""""

        self.send_html_response(client_socket, 200, html)

    def send_response(self, client_socket, status_code, message):
        response = f"HTTP/1.1 308 Permanent Redirect\r\n"
        response += "Location: https://google.com/\r\n"
        response += f"Content-Length: 0\r\n"

        response += "\r\n"

        try:
            client_socket.send(response.encode())
        except:
            pass

    def send_html_response(self, client_socket, status_code, html):
        status_messages = {200: "OK", 400: "Bad Request", 500: "Internal Server Error"}
        status_text = status_messages.get(status_code, "Unknown")

        html_bytes = html.encode('utf-8')

        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        response += "Content-Type: text/html; charset=utf-8\r\n"
        response += f"Content-Length: {len(html_bytes)}\r\n"
        response += "Connection: close\r\n"
        response += "\r\n"

        try:
            client_socket.send(response.encode('utf-8'))
            client_socket.send(html_bytes)
        except:
            pass

    def _server_loop(self):
        self.server.settimeout(1.0)

        while self.running:
            try:
                client, addr = self.server.accept()

                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, addr),
                    daemon=True
                )
                thread.start()

            except socket.timeout:
                continue
            except OSError:
                if self.running:
                    print_error("Socket error")
                break
            except Exception as e:
                if self.running:
                    print_error(f"Error: {e}")
                break


    def start(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(10)
            self.running = True

            self._server_loop()

        except OSError as e:
            print_error(f"Failed to start server: {e}")
            if "already in use" in str(e).lower() or "only one usage" in str(e).lower():
                print_error(f"Port {self.port} is already in use")
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def start_background(self):
        if self.running:
            return False

        self.server_thread = threading.Thread(target=self.start, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)
        return True

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.server:
            try:
                self.server.close()
            except:
                pass
    def is_running(self):
        return self.running


def make_wol_link(mac: str, broadcast: str = '255.255.255.255',port: int = 2) -> str:
    url = f"http://localhost:{port}/{mac}/"

    return url