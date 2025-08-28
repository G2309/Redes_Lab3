import json
from algorithm.dijkstra import DijkstraRouter

class DijkstraNode:
    def __init__(self, node_id, neighbors, network, full_topo, default_weight=1):
        self.node_id = node_id
        self.neighbors = neighbors  
        self.network = network     
        self.default_weight = default_weight
        self.graph = {}
        self.routing_table = {}
        
        if isinstance(neighbors, list):
            self.neighbors_dict = {n: {} for n in neighbors}
        else:
            self.neighbors_dict = neighbors
            
        self._build_graph_from_full_topo(full_topo)
        self._recompute_routes()
        
        print(f"[{self.node_id}] Dijkstra Node inicializado con vecinos: {list(self.neighbors_dict.keys())}")

    def _build_graph_from_full_topo(self, topo_config):
        """Construye el grafo completo a partir de la topología"""
        g = {}
        for node, info in topo_config.items():
            g.setdefault(node, [])
            neighbors = info["neighbors"]
            
            # Manejar neighbors como lista
            if isinstance(neighbors, list):
                for neigh in neighbors:
                    g.setdefault(neigh, [])
                    # Agregar arista bidireccional
                    g[node].append((neigh, self.default_weight))
                    g[neigh].append((node, self.default_weight))
            else:
                # Manejar neighbors como diccionario
                for neigh in neighbors.keys():
                    g.setdefault(neigh, [])
                    g[node].append((neigh, self.default_weight))
                    g[neigh].append((node, self.default_weight))
        
        # Eliminar duplicados
        for n, lst in g.items():
            seen = set()
            uniq = []
            for v, w in lst:
                if v not in seen:
                    uniq.append((v, w))
                    seen.add(v)
            g[n] = uniq
            
        self.graph = g
        print(f"[{self.node_id}] Grafo construido: {self.graph}")

    def _recompute_routes(self):
        """Recalcula las rutas usando Dijkstra"""
        router = DijkstraRouter(self.graph, self.node_id)
        router.calculate_routes()
        self.routing_table = router.get_routing_table()
        
        print(f"[{self.node_id}] 📋 Tabla de rutas calculada:")
        for dest, info in self.routing_table.items():
            print(f"    {dest} -> vía {info['next_hop']} (costo: {info['cost']})")

    async def handle_message(self, message, from_neighbor=None):
        """Maneja mensajes recibidos"""
        try:
            # Normalizar el mensaje
            if isinstance(message, (bytes, bytearray)):
                message = message.decode("utf-8")
            if isinstance(message, str):
                packet = json.loads(message)
            else:
                packet = message
                
            # Obtener destino
            dst = packet.get("to")
            src = packet.get("from")
            payload = packet.get("payload", "")
            
            print(f"[{self.node_id}] Mensaje recibido de {src} hacia {dst}: {payload}")
            
            # Si somos el destino
            if dst == self.node_id:
                print(f"[{self.node_id}] ✅ Mensaje para mí: {payload}")
                return
            
            # Si no tenemos ruta al destino
            if dst not in self.routing_table:
                print(f"[{self.node_id}] ❌ No hay ruta a {dst}")
                return
            
            # Obtener próximo salto
            next_hop = self.routing_table[dst]["next_hop"]
            
            # Verificar que el próximo salto sea un vecino directo
            if next_hop not in self.neighbors_dict:
                print(f"[{self.node_id}] ❌ {next_hop} no es vecino directo")
                return
            
            # Reenviar el mensaje
            print(f"[{self.node_id}] ➡️ Reenviando hacia {dst} vía {next_hop}")
            await self.network.publish(next_hop, packet)
            
        except Exception as e:
            print(f"[{self.node_id}] Error manejando mensaje: {e}")

    async def send_data_message(self, destination, payload):
        """Envía un mensaje de datos usando la tabla de rutas"""
        packet = {
            "proto": "dijkstra",
            "type": "message",
            "from": self.node_id,
            "to": destination,
            "payload": payload
        }
        
        print(f"[{self.node_id}] 🚀 Enviando mensaje a {destination}: {payload}")
        
        # Si el destino somos nosotros mismos
        if destination == self.node_id:
            print(f"[{self.node_id}] ✅ Mensaje para mí mismo: {payload}")
            return
            
        # Si no tenemos ruta al destino
        if destination not in self.routing_table:
            print(f"[{self.node_id}] ❌ No hay ruta a {destination}")
            print(f"[{self.node_id}] Rutas disponibles: {list(self.routing_table.keys())}")
            return
        
        # Obtener próximo salto
        next_hop = self.routing_table[destination]["next_hop"]
        
        # Verificar que el próximo salto sea un vecino directo
        if next_hop not in self.neighbors_dict:
            print(f"[{self.node_id}] ❌ {next_hop} no es vecino directo")
            return
            
        try:
            await self.network.publish(next_hop, packet)
            print(f"[{self.node_id}] ✅ Mensaje enviado vía {next_hop}")
        except Exception as e:
            print(f"[{self.node_id}] ❌ Error enviando mensaje: {e}")

    async def send_message(self, packet):
        """Compatibilidad con la interfaz de FloodingNode"""
        await self.send_data_message(packet["to"], packet["payload"])

    def get_status(self):
        return {
            "routing_table": self.routing_table,
            "neighbors": list(self.neighbors_dict.keys()),
            "graph": self.graph
        }
