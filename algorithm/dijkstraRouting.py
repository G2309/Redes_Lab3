import json
import asyncio
from algorithm.dijkstra import DijkstraRouter

class DijkstraNode:
    def __init__(self, node_id, neighbors, network, full_topo, default_weight=1):
        self.node_id = node_id
        self.neighbors = neighbors
        self.network = network
        self.default_weight = default_weight
        self.graph = {}
        self.routing_table = {}
        self.topology_db = {}
        self.sequence_numbers = {}
        
        if isinstance(neighbors, list):
            self.neighbors_dict = {n: {} for n in neighbors}
        else:
            self.neighbors_dict = neighbors
            
        self._build_initial_topology(full_topo)
        self._recompute_routes()
        
        print(f"[{self.node_id}] Dijkstra Node inicializado con vecinos: {list(self.neighbors_dict.keys())}")

    def _build_initial_topology(self, topo_config):
        self.topology_db[self.node_id] = {
            'neighbors': dict.fromkeys(self.neighbors_dict.keys(), self.default_weight),
            'sequence': 1
        }
        
        for node, info in topo_config.items():
            if node != self.node_id:
                neighbors = info.get("neighbors", {})
                if isinstance(neighbors, list):
                    neighbors = dict.fromkeys(neighbors, self.default_weight)
                
                self.topology_db[node] = {
                    'neighbors': neighbors,
                    'sequence': 0
                }

    def _build_graph_from_topology_db(self):
        g = {}
        for node, info in self.topology_db.items():
            g.setdefault(node, [])
            neighbors = info.get('neighbors', {})
            for neighbor, weight in neighbors.items():
                g.setdefault(neighbor, [])
                g[node].append((neighbor, weight))
        for n, lst in g.items():
            seen = set()
            uniq = []
            for v, w in lst:
                if v not in seen:
                    uniq.append((v, w))
                    seen.add(v)
            g[n] = uniq
        self.graph = g
        print(f"[{self.node_id}] Grafo actualizado: {self.graph}")

    def _recompute_routes(self):
        self._build_graph_from_topology_db()
        router = DijkstraRouter(self.graph, self.node_id)
        router.calculate_routes()
        self.routing_table = router.get_routing_table()
        print(f"[{self.node_id}] Tabla de rutas calculada:")
        for dest, info in self.routing_table.items():
            print(f"    {dest} -> vía {info['next_hop']} (costo: {info['cost']})")

    async def send_hello_message(self):
        hello_packet = {
            "proto": "lsr",
            "type": "hello",
            "from": self.node_id,
            "to": "broadcast",
            "ttl": 5,
            "headers": [self.node_id],
            "payload": ""
        }
        print(f"[{self.node_id}] Enviando HELLO a vecinos")
        for neighbor in self.neighbors_dict.keys():
            try:
                await self.network.publish(neighbor, hello_packet)
            except Exception as e:
                print(f"[{self.node_id}] Error enviando HELLO a {neighbor}: {e}")

    async def send_info_message(self, ttl=5, headers=None):
        if headers is None:
            headers = [self.node_id]
        payload = {}
        for dest, info in self.routing_table.items():
            if dest != self.node_id:
                payload[dest] = info['cost']
        self.sequence_numbers[self.node_id] = self.sequence_numbers.get(self.node_id, 0) + 1
        info_packet = {
            "proto": "lsr",
            "type": "info",
            "from": self.node_id,
            "to": "broadcast",
            "ttl": ttl,
            "headers": headers.copy(),
            "payload": payload,
            "sequence": self.sequence_numbers[self.node_id]
        }
        print(f"[{self.node_id}] Enviando INFO (seq: {self.sequence_numbers[self.node_id]})")
        print(f"    Payload: {payload}")
        for neighbor in self.neighbors_dict.keys():
            try:
                await self.network.publish(neighbor, info_packet)
            except Exception as e:
                print(f"[{self.node_id}] Error enviando INFO a {neighbor}: {e}")

    def send_own_lsa_package(self):
        asyncio.create_task(self.send_info_message())

    async def handle_message(self, message, from_neighbor=None):
        try:
            if isinstance(message, (bytes, bytearray)):
                message = message.decode("utf-8")
            if isinstance(message, str):
                packet = json.loads(message)
            else:
                packet = message
            msg_type = packet.get("type")
            proto = packet.get("proto", "")
            if proto != "lsr":
                print(f"[{self.node_id}] Protocolo no soportado: {proto}")
                return
            if msg_type == "hello":
                await self._handle_hello(packet)
            elif msg_type == "info":
                await self._handle_info(packet)
            elif msg_type == "message":
                await self._handle_data_message(packet)
            else:
                print(f"[{self.node_id}] Tipo de mensaje no soportado: {msg_type}")
        except Exception as e:
            print(f"[{self.node_id}] Error manejando mensaje: {e}")

    async def _handle_hello(self, packet):
        src = packet.get("from")
        print(f"[{self.node_id}] HELLO recibido de {src}")
        if src in self.neighbors_dict and src != self.node_id:
            print(f"[{self.node_id}] Vecino {src} confirmado")

    async def _handle_info(self, packet):
        src = packet.get("from")
        ttl = packet.get("ttl", 0)
        headers = packet.get("headers", [])
        payload = packet.get("payload", {})
        sequence = packet.get("sequence", 0)
        print(f"[{self.node_id}] INFO recibido de {src} (TTL: {ttl}, seq: {sequence})")
        if src in self.sequence_numbers:
            if sequence <= self.sequence_numbers[src]:
                return
        if self.node_id in headers:
            return
        self.topology_db[src] = {
            'neighbors': payload.copy(),
            'sequence': sequence
        }
        self.sequence_numbers[src] = sequence
        print(f"[{self.node_id}] Topología actualizada para {src}: {payload}")
        self._recompute_routes()
        if ttl > 1:
            new_headers = headers.copy()
            if len(new_headers) >= 3:
                new_headers.pop(0)
            new_headers.append(self.node_id)
            forward_packet = packet.copy()
            forward_packet["ttl"] = ttl - 1
            forward_packet["headers"] = new_headers
            for neighbor in self.neighbors_dict.keys():
                if neighbor != src:
                    try:
                        await self.network.publish(neighbor, forward_packet)
                    except Exception as e:
                        print(f"[{self.node_id}] Error reenviando INFO a {neighbor}: {e}")

    async def _handle_data_message(self, packet):
        dst = packet.get("to")
        src = packet.get("from")
        payload = packet.get("payload", "")
        ttl = packet.get("ttl", 0)
        headers = packet.get("headers", [])
        if dst == self.node_id:
            return
        if ttl <= 1:
            return
        if self.node_id in headers:
            return
        if dst not in self.routing_table:
            return
        next_hop = self.routing_table[dst]["next_hop"]
        if next_hop not in self.neighbors_dict:
            return
        new_headers = headers.copy()
        if len(new_headers) >= 3:
            new_headers.pop(0)
        new_headers.append(self.node_id)
        forward_packet = packet.copy()
        forward_packet["ttl"] = ttl - 1
        forward_packet["headers"] = new_headers
        try:
            await self.network.publish(next_hop, forward_packet)
        except Exception:
            pass

    async def send_data_message(self, destination, payload):
        packet = {
            "proto": "lsr",
            "type": "message",
            "from": self.node_id,
            "to": destination,
            "ttl": 5,
            "headers": [self.node_id],
            "payload": payload
        }
        if destination == self.node_id:
            return
        if destination not in self.routing_table:
            return
        next_hop = self.routing_table[destination]["next_hop"]
        if next_hop not in self.neighbors_dict:
            return
        try:
            await self.network.publish(next_hop, packet)
        except Exception:
            pass

    async def send_message(self, packet):
        await self.send_data_message(packet["to"], packet["payload"])

    def build_routing_table(self):
        self._recompute_routes()

    def get_status(self):
        return {
            "routing_table": self.routing_table,
            "neighbors": list(self.neighbors_dict.keys()),
            "graph": self.graph,
            "topology_db": self.topology_db
        }

