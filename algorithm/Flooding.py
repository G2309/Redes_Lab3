import copy
import asyncio

class FloodingNode:
  def __init__(self, node_id, neighbors, network, delay=2.0):
    self.node_id = node_id
    self.neighbors = neighbors
    self.network = network
    self.received_packets = set()
    self.delay = delay

  async def handle_message(self, packet):
    packet_id = f"{packet.get('from')}:{packet.get('to')}:{packet.get('payload')}"

    if packet_id in self.received_packets:
      print(f"[{self.node_id}] Discarting duplicating package: {packet_id}")
      return

    self.received_packets.add(packet_id)
    print(f"[{self.node_id}] Received from {packet.get('from')} -> {packet}")
    
    if packet.get("to") == self.node_id:
      print(f"[{self.node_id}] I am the destiny")
      return

    if packet.get("ttl", 0) > 0:
      await self.forward(packet)

  async def forward(self, packet, exclude_neighbor=None):
    packet = copy.deepcopy(packet)
    packet["ttl"] -= 1
    packet["_prev_hop"] = self.node_id
    print(f"[{self.node_id}] Resending package to neighbors")

    for neighbor in self.neighbors:
      if neighbor == exclude_neighbor:
        continue

      await asyncio.sleep(self.delay)

      print(f"[{self.node_id}] --> Sending to {neighbor}")
      await self.network.publish(neighbor, packet)

  async def send_message(self, packet):
    packet_id = packet.get("from") + ":" + packet.get("to")
    self.received_packets.add(packet_id)
    print(f"[{self.node_id}] 🚀 Enviando mensaje inicial: {packet}")
    await self.forward(packet, exclude_neighbor=None)
