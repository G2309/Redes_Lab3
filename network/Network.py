import os
import sys
import socket
import threading
import json
import time

class NetworkNode:
    def __init__(self, node_id, port):
        self.node_id = node_id
        self.port = port
        self.is_running = True
        self.algorithm_logic = None

    def set_algorithm(self, logic):
        self.algorithm_logic = logic

    def start(self):
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("localhost", self.port))
        server_socket.listen()

        while self.is_running:
            try:
                conn, addr = server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client_connection, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
            except:
                break

    def handle_client_connection(self, conn, addr):
        try:
            while self.is_running:
                data = conn.recv(4096)
                if not data:
                    break
                message = data.decode("utf-8")
                
                if self.algorithm_logic:
                    self.algorithm_logic.handle_message(message)
        except (socket.error, ConnectionResetError):
            pass
        finally:
            conn.close()

    def send_message(self, host, port, packet):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.sendall(json.dumps(packet).encode("utf-8"))
            sock.close()
        except socket.error:
            pass

