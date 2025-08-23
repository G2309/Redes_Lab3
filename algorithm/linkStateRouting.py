import socket
import asyncio
import json

HOST = 'localhost'
class Node:

    def __init__(self, id, port, neighbors, network, ttl):
        self.id = id #Identificador único del nodo
        self.port = port #El puerto en el que se encuentra nuestro nodo
        self.lsdb  = {}  #la db con los datos de la topología de la red
        self.neighbors = neighbors #siempre queremos inforación de los vecinos inmediatos
        self.lsdb[self.id] = {"neigbors": self.neighbors, "seq": 0}
        self.recived_messages = {} #Aquí guardamos lo que hemos recibido de los demás nodos
        self.seq_counter = -1 #Cada vez que enviemos nuestra información aumentaremos la secuencia
        self.received_lsa = {}
        self.network = network
        self.ttl = ttl

    def send_own_lsa_package(self):
        self.seq_counter += 1
        self.ttl -= 1
        print(f"Nodo: {self.id} enviando información a sus vecinos")
        for i in self.neighbors.values():

            message = json.dumps({"source": self.id, 
                                  "neighbors": self.neighbors,
                                  "ttl": self.ttl,
                                  "seq": self.seq_counter,
                                  "type": "LSA" })
            
            self.network.send_message(HOST, self.neighbors[i]["port"], message)

    def handle_message(self, raw_message):

        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            return

        if message["type"] == "LSA":
            self.handle_lsa(message)

    def handle_lsa(self, lsa):
        """Procesa paquetes LSA"""
        source = lsa["source"]
        seq = lsa["seq"]
        ttl = lsa["ttl"]
        
        # Verificar si es un LSA duplicado o viejo
        if source in self.received_lsa:
            if seq <= self.received_lsa[source]:
                return  # LSA duplicado o viejo, descartar
        
        # Actualizar la base de datos
        self.received_lsa[source] = seq
        self.lsdb[source] = {
            "neighbors": lsa["neighbors"],
            "seq": seq
        }
        
        print(f"Nodo {self.id}: Recibido LSA de {source}, seq={seq}")
        
        # Reenviar si TTL > 1
        if ttl > 1:
            self.forward_lsa(lsa)
        
        # Recalcular tabla de rutas
        self.build_routing_table()

    def forward_lsa(self, original_lsa):

        forwarded_lsa = original_lsa.copy()
        forwarded_lsa["ttl"] -= 1  # Decrementar TTL al reenviar
        
        message = json.dumps(forwarded_lsa)
        
        for i in self.neighbors:
            if self.neighbors[i] != original_lsa["source"]:  # No reenviar al origen
                self.network.send_message(HOST, self.neighbors[i]["port"], message)
            
    def send_message (self, destination, message):
        
        message = json.dumps({"source": self.id, 
                            "neighbors": self.neighbors,
                            "ttl": len(self.db.values()) -1,
                            "seq": self.seq_counter,
                            "port": self.port,
                            "type": "LSA" })
            
        self.network.send_message(HOST, destination, message)

    def build_routing_table(self):        # Implementación básica de Dijkstra
        distances = {node: float('inf') for node in self.lsdb.keys()}
        distances[self.id] = 0
        previous = {}
        unvisited = set(self.lsdb.keys())
        
        while unvisited:
            # Encontrar nodo no visitado con menor distancia
            current = min(unvisited, key=lambda x: distances[x])
            
            if distances[current] == float('inf'):
                break
                
            unvisited.remove(current)
            
            # Examinar vecinos
            if current in self.lsdb:
                for neighbor, info in self.lsdb[current]["neighbors"].items():
                    if neighbor in unvisited:
                        cost = info["cost"]
                        new_distance = distances[current] + cost
                        
                        if new_distance < distances[neighbor]:
                            distances[neighbor] = new_distance
                            previous[neighbor] = current
        
        # Construir tabla de rutas
        self.routing_table = {}
        for destination in distances:
            if destination != self.id and distances[destination] != float('inf'):
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
        
        print(f"Nodo {self.id}: Tabla de rutas actualizada: {self.routing_table}")

    def handle_lsa(self, lsa):
        source = lsa["source"]
        seq = lsa["seq"]
        ttl = lsa["ttl"]
        
        # Verificar si es un LSA duplicado o viejo
        if source in self.received_lsa:
            if seq <= self.received_lsa[source]:
                return  # LSA duplicado o viejo, descartar
        
        # Actualizar la base de datos
        self.received_lsa[source] = seq
        self.lsdb[source] = {
            "neighbors": lsa["neighbors"],
            "seq": seq
        }
        
        print(f"Nodo {self.id}: Recibido LSA de {source}, seq={seq}")
        
        # Reenviar si TTL > 1
        if ttl > 1:
            self.forward_lsa(lsa)



    


