import json
import threading
import time

class FloodingNode:
  def __init__(self, node_id, neighbors, network):
    self.node_id = node_id
    self.neighbors = neighbors
    self.network = network
    self.received_packets = set()
    self.lock = threading.Lock()

  def handle_message(self, message):
    with self.lock:
      packet = json.loads(message)
      packet_id = packet.get("from") + ":" + str(packet.get("ttl"))

      if packet_id in self.received_packets:
        print(f"Duplicated package received, descrting: {packet_id}")
        return

      self.received_packets.add(packet_id)
      print(f"[{self.node_id}] Package received from {packet.get('from')} with payload: {packet.get('payload')}")

      if packet.get("to") == self.node_id:
        print("Soy el destinatario")
        return

      if packet.get("ttl", 0) > 0:
        self.forward(packet)

  def forward(self, packet):
    packet["ttl"] -= 1
    print(f"[{self.node_id}] Resending package to neighbors")

    for neighbor, (host, port) in self.neighbors.items():
      self.network.send_message(host, port, packet)

  def send_message(self, packet):
    print(f"[{self.node_id}] 🚀 Enviando mensaje inicial: {packet}")
    self.forward(packet)
