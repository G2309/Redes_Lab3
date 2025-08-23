import json
import threading
import time
import copy

class FloodingNode:
  def __init__(self, node_id, neighbors, network, delay=3.0):
    self.node_id = node_id
    self.neighbors = neighbors
    self.network = network
    self.received_packets = set()
    self.lock = threading.Lock()
    self.delay = delay

  def handle_message(self, message, from_neighbor=None):
    with self.lock:
      packet = json.loads(message)
      packet_id = packet.get("from") + ":" + packet.get("to")

      if packet_id in self.received_packets:
        print(f"Duplicated package received, descarting: {packet_id}")
        return

      self.received_packets.add(packet_id)
      print(f"[{self.node_id}] Package received from {packet.get('from')} with payload: {packet.get('payload')}")

      prev_hop = from_neighbor or packet.get("_prev_hop")

      if packet.get("to") == self.node_id:
        print("Soy el destinatario")
        return

      if packet.get("ttl", 0) > 0:
        self.forward(packet, exclude_neighbor=prev_hop)

  def forward(self, packet, exclude_neighbor=None):
    packet = copy.deepcopy(packet)
    packet["ttl"] -= 1
    packet["_prev_hop"] = self.node_id
    print(f"[{self.node_id}] Resending package to neighbors")

    for neighbor, (host, port) in self.neighbors.items():
      if neighbor == exclude_neighbor:
        continue

      time.sleep(self.delay)

      print(f"[{self.node_id}] --> Sending to {neighbor}")
      self.network.send_message(host, port, packet)

  def send_message(self, packet):
    packet_id = packet.get("from") + ":" + packet.get("to")
    self.received_packets.add(packet_id)
    print(f"[{self.node_id}] 🚀 Enviando mensaje inicial: {packet}")
    self.forward(packet, exclude_neighbor=None)
