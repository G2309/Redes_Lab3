import json
from algorithm.dijkstra import DijkstraRouter  # ajusta el import al nombre real de tu archivo/clase

class DijkstraNode:
    def __init__(self, node_id, neighbors, network, full_topo, default_weight=1):
        self.node_id = node_id
        self.neighbors = neighbors
        self.network = network
        self.default_weight = default_weight
        self.graph = {}
        self.routing_table = {}

        # Construye grafo global (no sólo vecinos del nodo)
        self._build_graph_from_full_topo(full_topo)
        self._recompute_routes()

    def _build_graph_from_full_topo(self, topo_config):
        # Grafo no dirigido con peso 1 por defecto
        g = {}
        for node, info in topo_config.items():
            g.setdefault(node, [])
            for neigh in info["neighbors"].keys():
                g.setdefault(neigh, [])
                g[node].append((neigh, self.default_weight))
                g[neigh].append((node, self.default_weight))
        # Deduplicar listas de adyacencia
        for n, lst in g.items():
            seen = set()
            uniq = []
            for v, w in lst:
                if v not in seen:
                    uniq.append((v, w))
                    seen.add(v)
            g[n] = uniq
        self.graph = g

    def _recompute_routes(self):
        router = DijkstraRouter(self.graph, self.node_id)
        router.calculate_routes()
        self.routing_table = router.get_routing_table()

    def handle_message(self, message, from_neighbor=None):
        # Acepta str o dict
        if isinstance(message, (bytes, bytearray)):
            message = message.decode("utf-8")
        if isinstance(message, str):
            packet = json.loads(message)
        else:
            packet = message

        dst = packet.get("to")

        if dst == self.node_id:
            print(f"[{self.node_id}] ✅ Recibido: {packet.get('payload')}")
            return

        if dst not in self.routing_table:
            print(f"[{self.node_id}] ❌ No hay ruta a {dst}")
            return

        next_hop = self.routing_table[dst]["next_hop"]
        if next_hop not in self.neighbors:
            print(f"[{self.node_id}] ❌ {next_hop} no es vecino directo; no puedo reenviar")
            return

        host, port = self.neighbors[next_hop]
        print(f"[{self.node_id}] ➡️ Reenviando hacia {dst} vía {next_hop}")
        self.network.send_message(host, port, packet)

    def send_data_message(self, destination, payload):
        packet = {
            "proto": "dijkstra",
            "type": "message",
            "from": self.node_id,
            "to": destination,
            "payload": payload
        }
        print(f"[{self.node_id}] 🚀 Enviando a {destination}")
        # Entrar por el mismo path que un paquete recibido
        self.handle_message(json.dumps(packet))

    def get_status(self):
        return {
            "routing_table": self.routing_table,
            "neighbors": list(self.neighbors.keys())
        }

