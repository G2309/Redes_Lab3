import json
import threading
import time

class Flooding:
  def __init__(self, node_id, neighbors):
    self.node_id = node_id
    self.neighbors = neighbors
    self.received_packets = set()
    self.lock = threading.Lock()

    def handle_message(self, message):
      with self.lock:
        packet = json.loads(message)
        packet_id = packet.get("from") + ":" + str(packet.get("ttl"))

        if packet_id in self.received_packets:
          print(f"")
          return

        self.received_packets.add(packet_id)
        print(f"")

    def forward(self, packet):
      packet["ttl"] -= 1
