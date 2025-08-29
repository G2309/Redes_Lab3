# algorithm/linkStateRouting.py
import copy
import heapq

class Node:
    def __init__(self, id, neighbors, network, ttl=5):
        self.node_id = id
        # neighbors: lista de IDs de vecinos (coste por defecto = 1)
        self.neighbors = neighbors if isinstance(neighbors, (list, tuple)) else list(neighbors.keys())
        self.network = network
        self.ttl = ttl

        # Grafo plano: {"A": {"B": 1, "C": 2}, ...}
        self.lsdb = {}
        self.routing_table = {}

        print(f"[{self.node_id}] LSR node initialized")

        # Siembra tu adyacencia local
        self.lsdb[self.node_id] = self._adj_from_neighbors()
        self.build_routing_table()

    # ============= Utilidades internas =============

    def _adj_from_neighbors(self):
        """Convierte self.neighbors (lista) a {neighbor: cost} usando costo=1."""
        return {nid: 1 for nid in self.neighbors}

    def _bump_headers_ttl(self, packet):
        """Mantiene últimos 3 hops y reduce TTL."""
        pkt = copy.deepcopy(packet)
        pkt.setdefault("headers", [])
        pkt.setdefault("ttl", self.ttl)

        # conservar últimas 2 y agregarme a mí (máximo 3)
        if len(pkt["headers"]) >= 3:
            pkt["headers"] = pkt["headers"][-2:]
        pkt["headers"].append(self.node_id)

        pkt["ttl"] -= 1
        return pkt

    # ============= Entrada de paquetes =============

    async def handle_message(self, packet):
        ptype = packet.get("type")
        if ptype == "info":
            await self.handle_info_message(packet)
        elif ptype == "message":
            await self.handle_sending_message(packet)
        # HELLO lo maneja NetworkNodePubSub (suscripciones y reply).  # :contentReference[oaicite:4]{index=4}

    async def handle_info_message(self, packet):
        # Evitar loops si ya pasé por aquí
        if self.node_id in packet.get("headers", []):
            return

        origin = packet.get("from")
        payload = packet.get("payload", {})  # esperado: {vecino: costo, ...} del origin

        print(f"[{self.node_id}] INFO from {origin}: updating lsdb")
        prev = self.lsdb.get(origin)

        # Integramos la adyacencia local del emisor (LSR)
        self.lsdb[origin] = dict(payload) if isinstance(payload, dict) else {}

        # Si hubo cambio real, recalculamos rutas
        if prev != self.lsdb[origin]:
            self.build_routing_table()

        # Reenviar (INFO sí se retransmite) si TTL > 0
        if packet.get("ttl", 0) > 0:
            await self.forward(packet)

    async def forward(self, packet):
        pkt = self._bump_headers_ttl(packet)
        if pkt["ttl"] < 0:
            return

        # Enviar a TODOS los vecinos directos
        for neighbor_id in self.neighbors:
            # Para acotar bucles: si ya está en headers, lo podemos saltar
            if neighbor_id in pkt["headers"]:
                continue
            await self.network.publish(neighbor_id, pkt)
        print(f"[{self.node_id}] Forwarded {pkt.get('type')} to neighbors")

    # ============= Mensajería de aplicación =============

    async def handle_sending_message(self, packet):
        """Paquetes 'message' con campos: to, payload."""
        dest = packet.get("to")
        if dest == self.node_id:
            print(f"[{self.node_id}] Message delivered: {packet.get('payload')}")
            return
        await self._route_and_forward(packet, dest)

    async def send_message(self, packet):
        """Para iniciar un 'message' desde este nodo."""
        dest = packet.get("to")
        if dest is None:
            print(f"[{self.node_id}] Error: packet sin 'to'")
            return

        # Si es vecino directo, enviar directo
        if dest in self.neighbors:
            pkt = self._bump_headers_ttl(packet)
            await self.network.publish(dest, pkt)
            print(f"[{self.node_id}] Sent directly to neighbor {dest}")
            return

        # Si no, rutear
        await self._route_and_forward(packet, dest)

    async def _route_and_forward(self, packet, destination):
        # Garantizar tabla
        if destination not in self.routing_table:
            self.build_routing_table()

        route = self.routing_table.get(destination)
        if not route:
            print(f"[{self.node_id}] No route to {destination}")
            return

        next_hop = route["next_hop"]
        if next_hop not in self.neighbors:
            print(f"[{self.node_id}] Route error: next_hop {next_hop} not in neighbors")
            return

        pkt = self._bump_headers_ttl(packet)
        if pkt["ttl"] < 0:
            print(f"[{self.node_id}] TTL exhausted for {destination}")
            return

        await self.network.publish(next_hop, pkt)
        print(f"[{self.node_id}] Routed to {destination} via {next_hop}")

    async def send_own_info(self):
        """Envía tu adyacencia local (LSA) a los vecinos (sin seq)."""
        info_packet = {
            "proto": "lsr",
            "type": "info",
            "from": self.node_id,
            "to": "broadcast",
            "ttl": self.ttl,
            "headers": [self.node_id],
            "payload": self._adj_from_neighbors(),  # adyacencia local
        }
        await self.forward(info_packet)

    # ============= Dijkstra / tabla de rutas =============

    def build_routing_table(self):
        print(f"[{self.node_id}] Recalculando tabla de rutas...")

        # 1) Conjunto de nodos
        nodes = set()
        for n, nbrs in self.lsdb.items():
            nodes.add(n)
            nodes.update(nbrs.keys())
        nodes.add(self.node_id)

        # 2) Dijkstra
        INF = float("inf")
        dist = {n: INF for n in nodes}
        dist[self.node_id] = 0
        previous = {}
        visited = set()
        heap = [(0, self.node_id)]

        while heap:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            for v, cost in self.lsdb.get(u, {}).items():
                if cost is None:
                    cost = 1
                nd = d + cost
                if nd < dist.get(v, INF):
                    dist[v] = nd
                    previous[v] = u
                    heapq.heappush(heap, (nd, v))

        # 3) Construcción routing_table
        old = dict(self.routing_table)
        routing = {}

        for dest in nodes:
            if dest == self.node_id:
                continue
            if dist.get(dest, INF) == INF:
                continue

            # Subir desde dest hasta encontrar el 1er salto desde self.node_id
            hop = dest
            while previous.get(hop) is not None and previous[hop] != self.node_id:
                hop = previous[hop]

            if previous.get(hop) == self.node_id:
                next_hop = hop
            elif previous.get(dest) == self.node_id or dest in self.lsdb.get(self.node_id, {}):
                next_hop = dest
            else:
                continue

            routing[dest] = {"next_hop": next_hop, "cost": dist[dest]}

        self.routing_table = routing

        if self.routing_table != old:
            print(f"[{self.node_id}] 📋 Tabla de rutas actualizada:")
            for dest in sorted(self.routing_table):
                info = self.routing_table[dest]
                print(f"    {dest} -> vía {info['next_hop']} (costo: {info['cost']})")

        return self.routing_table




















