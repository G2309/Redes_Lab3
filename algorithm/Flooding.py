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

  def handle_message(self, message, from_neighbor=None):
    with self.lock:
      packet = json.loads(message)
      packet_id = packet.get("from") + ":" + packet.get("to")

      if packet_id in self.received_packets:
        print(f"Duplicated package received, descarting: {packet_id}")
        return

      self.received_packets.add(packet_id)
      print(f"[{self.node_id}] Package received from {packet.get('from')} with payload: {packet.get('payload')}")

      if packet.get("to") == self.node_id:
        print("Soy el destinatario")
        return

      if packet.get("ttl", 0) > 0:
        self.forward(packet, from_neighbor)

  def forward(self, packet, exclude_neighbor=None):
    packet["ttl"] -= 1
    print(f"[{self.node_id}] Resending package to neighbors")

    for neighbor, (host, port) in self.neighbors.items():
      if neighbor == exclude_neighbor:
        continue
      self.network.send_message(host, port, packet)

  def send_message(self, packet):
    packet_id = packet.get("from") + ":" + packet.get("to")
    self.received_packets.add(packet_id)
    print(f"[{self.node_id}] 🚀 Enviando mensaje inicial: {packet}")
    self.forward(packet, exclude_neighbor=None)
