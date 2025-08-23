import json
import time
from algorithm.dijkstra import DijkstraRouter  

class DijkstraNode:
    def __init__(self, node_id, neighbors, network):
        self.node_id = node_id
        self.neighbors = neighbors  # vecinos directos
        self.network = network
        self.graph = {}  # se irá llenando dinámicamente
        self.routing_table = {}

        # construir grafo inicial solo con vecinos directos
        self.build_graph()

    def build_graph(self):
        self.graph[self.node_id] = []
        for neigh, (host, port) in self.neighbors.items():
            self.graph.setdefault(self.node_id, []).append((neigh, 1))  # costo = 1 por defecto
            self.graph.setdefault(neigh, []).append((self.node_id, 1))

        # correr Dijkstra
        router = DijkstraRouter(self.graph, self.node_id)
        router.calculate_routes()
        self.routing_table = router.get_routing_table()

    def handle_message(self, message, from_neighbor=None):
        packet = json.loads(message)
        destination = packet.get("to")

        if destination == self.node_id:
            print(f"[{self.node_id}] ✅ Mensaje recibido: {packet['payload']}")
            return

        # buscar siguiente salto en la tabla de enrutamiento
        if destination not in self.routing_table:
            print(f"[{self.node_id}] ❌ No hay ruta a {destination}")
            return

        next_hop = self.routing_table[destination]["next_hop"]
        if next_hop not in self.neighbors:
            print(f"[{self.node_id}] ❌ No conozco físicamente a {next_hop}")
            return

        host, port = self.neighbors[next_hop]
        print(f"[{self.node_id}] ➡️ Reenviando mensaje hacia {destination} vía {next_hop}")
        self.network.send_message(host, port, packet)

    def send_data_message(self, destination, payload):
        packet = {
            "proto": "dijkstra",
            "type": "message",
            "from": self.node_id,
            "to": destination,
            "payload": payload
        }
        print(f"[{self.node_id}] 🚀 Enviando mensaje a {destination}")
        self.handle_message(json.dumps(packet))

