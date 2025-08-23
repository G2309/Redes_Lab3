import threading
import time
import copy
import json
import random

HOST = 'localhost'
class Node:

    def __init__(self, id, port, neighbors, network, ttl):
        self.id = id #Identificador único del nodo
        self.port = port #El puerto en el que se encuentra nuestro nodo
        self.lsdb  = {}  #la db con los datos de la topología de la red
        self.neighbors = neighbors #siempre queremos inforación de los vecinos inmediatos
        for neighbor_id, (host, port) in neighbors.items():
            self.neighbors[neighbor_id] = {
                "host": host,
                "port": port, 
                "cost": random.randint(1, 10) 
        }
        self.lsdb[self.id] = {"neigbors": self.neighbors, "seq": 0}
        self.recived_messages = {} #Aquí guardamos lo que hemos recibido de los demás nodos
        self.seq_counter = -1 #Cada vez que enviemos nuestra información aumentaremos la secuencia
        self.received_lsa = {}
        self.network = network
        self.ttl = ttl
        print(f"[{self.node_id}] LSR Node inicializado con vecinos: {list(self.neighbors.keys())}")

    def send_own_lsa_package(self):
        with self.lock:
            self.seq_counter += 1
            
            lsa_packet = {
                "type": "LSA",
                "source": self.node_id,
                "seq": self.seq_counter,
                "neighbors": self.neighbors,
                "ttl": self.initial_ttl
            }
        print(f"[{self.node_id}] Enviando LSA (seq={self.seq_counter}) a vecinos")
            
        for neighbor_id, neighbor_info in self.neighbors.items():
            try:
                self.network.send_message(
                    neighbor_info["host"], 
                    neighbor_info["port"], 
                    lsa_packet
                )
                print(f"[{self.node_id}] --> LSA enviado a {neighbor_id}")
            except Exception as e:
                print(f"[{self.node_id}] Error enviando LSA a {neighbor_id}: {e}")

    def handle_message(self, raw_message, from_neighbor=None):
        with self.lock:
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError as e:
                print(f"[{self.node_id}] Error decodificando mensaje: {e}")
                return

            if message.get("type") == "LSA":
                self.handle_lsa(message)
            elif message.get("type") == "DATA":
                self.handle_data_message(message)

    def handle_lsa(self, lsa):

        source = lsa["source"]
        seq = lsa["seq"]
        ttl = lsa["ttl"]
        
        # Ignorar nuestros propios LSAs
        if source == self.node_id:
            return
        
        # Verificar si es un LSA duplicado o viejo
        if source in self.received_lsa:
            if seq <= self.received_lsa[source]:
                print(f"[{self.node_id}] LSA duplicado/viejo de {source} (seq={seq}), descartando")
                return
        
        # Actualizar la base de datos
        self.received_lsa[source] = seq
        self.lsdb[source] = {
            "neighbors": lsa["neighbors"],
            "seq": seq
        }
        
        print(f"[{self.node_id}] LSA recibido de {source} (seq={seq})")
        
        # Reenviar si TTL > 1
        if ttl > 1:
            self.forward_lsa(lsa)
        
        # Recalcular tabla de rutas
        self.build_routing_table()

    def forward_lsa(self, original_lsa):
        """Reenvía LSA a vecinos (excepto al que lo envió)"""
        forwarded_lsa = copy.deepcopy(original_lsa)
        forwarded_lsa["ttl"] -= 1  # Decrementar TTL al reenviar
        
        print(f"[{self.node_id}] Reenviando LSA de {original_lsa['source']} (TTL={forwarded_lsa['ttl']})")
        
        for neighbor_id, neighbor_info in self.neighbors.items():
            # No reenviar al nodo que originó el LSA
            if neighbor_id != original_lsa["source"]:
                try:
                    self.network.send_message(
                        neighbor_info["host"], 
                        neighbor_info["port"], 
                        forwarded_lsa
                    )
                    print(f"[{self.node_id}] --> LSA reenviado a {neighbor_id}")
                except Exception as e:
                    print(f"[{self.node_id}] Error reenviando LSA a {neighbor_id}: {e}")

    def build_routing_table(self):
        print(f"[{self.node_id}] Recalculando tabla de rutas...")
        
        # Implementación de Dijkstra
        distances = {node: float('inf') for node in self.lsdb.keys()}
        distances[self.node_id] = 0
        previous = {}
        unvisited = set(self.lsdb.keys())
        
        while unvisited:
            # Encontrar nodo no visitado con menor distancia
            current = min(unvisited, key=lambda x: distances[x])
            
            if distances[current] == float('inf'):
                break
                
            unvisited.remove(current)
            
            # Examinar vecinos del nodo actual
            if current in self.lsdb and "neighbors" in self.lsdb[current]:
                for neighbor_id, neighbor_info in self.lsdb[current]["neighbors"].items():
                    if neighbor_id in unvisited:
                        cost = neighbor_info.get("cost", 1)
                        new_distance = distances[current] + cost
                        
                        if new_distance < distances[neighbor_id]:
                            distances[neighbor_id] = new_distance
                            previous[neighbor_id] = current
        
        # Construir tabla de rutas
        old_table = self.routing_table.copy()
        self.routing_table = {}
        
        for destination in distances:
            if destination != self.node_id and distances[destination] != float('inf'):
                # Encontrar próximo salto
                path = []
                current = destination
                while current in previous:
                    path.insert(0, current)
                    current = previous[current]
                
                next_hop = path[0] if path else destination
                self.routing_table[destination] = {
                    "next_hop": next_hop,
                    "cost": distances[destination]
                }
        
        # Mostrar cambios solo si hay diferencias
        if self.routing_table != old_table:
            print(f"[{self.node_id}] 📋 Tabla de rutas actualizada:")
            for dest, info in self.routing_table.items():
                print(f"    {dest} -> vía {info['next_hop']} (costo: {info['cost']})")
        
        return self.routing_table

    def handle_data_message(self, message):
        source = message["source"]
        destination = message["destination"]
        payload = message.get("payload", message.get("data", ""))
        
        if destination == self.node_id:
            print(f"[{self.node_id}] 📨 Mensaje recibido de {source}: {payload}")
            return
        
        # Reenviar usando tabla de rutas
        if destination in self.routing_table:
            next_hop = self.routing_table[destination]["next_hop"]
            if next_hop in self.neighbors:
                neighbor_info = self.neighbors[next_hop]
                print(f"[{self.node_id}] 📤 Reenviando mensaje de {source} a {destination} vía {next_hop}")
                try:
                    self.network.send_message(
                        neighbor_info["host"], 
                        neighbor_info["port"], 
                        message
                    )
                except Exception as e:
                    print(f"[{self.node_id}] Error reenviando mensaje: {e}")
            else:
                print(f"[{self.node_id}] Error: next_hop {next_hop} no está en vecinos")
        else:
            print(f"[{self.node_id}] No hay ruta hacia {destination}")

    def send_data_message(self, destination, payload):
        if destination in self.routing_table:
            next_hop = self.routing_table[destination]["next_hop"]
            if next_hop in self.neighbors:
                neighbor_info = self.neighbors[next_hop]
                
                data_packet = {
                    "type": "DATA",
                    "source": self.node_id,
                    "destination": destination,
                    "payload": payload
                }
                
                print(f"[{self.node_id}] Enviando mensaje a {destination} vía {next_hop}: {payload}")
                try:
                    self.network.send_message(
                        neighbor_info["host"], 
                        neighbor_info["port"], 
                        data_packet
                    )
                except Exception as e:
                    print(f"[{self.node_id}] Error enviando mensaje: {e}")
            else:
                print(f"[{self.node_id}] Error: next_hop {next_hop} no está en vecinos")
        else:
            print(f"[{self.node_id}] No hay ruta hacia {destination}")
            print(f"[{self.node_id}] Tabla actual: {self.routing_table}")

    def get_status(self):
        return {
            "node_id": self.node_id,
            "neighbors": list(self.neighbors.keys()),
            "lsdb_nodes": list(self.lsdb.keys()),
            "routing_table": self.routing_table,
            "seq_counter": self.seq_counter
        }