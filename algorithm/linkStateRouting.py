import threading
import time
import copy
import json
import random

HOST = 'localhost'
class Node:

    def __init__(self, id, neighbors, network, ttl =10):
        self.node_id = id #Identificador único del nodo
        self.lsdb  = {}  #la db con los datos de la topología de la red
        self.neighbors = neighbors #siempre queremos inforación de los vecinos inmediatos
        self.recived_messages = {} #Aquí guardamos lo que hemos recibido de los demás nodos
        self.seq_counter = -1 #Cada vez que enviemos nuestra información aumentaremos la secuencia
        self.received_lsa = {}
        self.network = network
        self.ttl = ttl
        self.routing_table = {}
        print(f"[{self.node_id}] LSR node initialized")



    async def handle_message(self, packet):

        if packet.get('type') == "info":
            await self.handle_info_message(packet)
        await self.handle_sending_message(packet)


    async def handle_info_message(self, packet):
        
        if self.node_id in packet.get('headers'):
            return #Evitar ciclos
    
        print(f"Adding {packet.get('from')} to local db")
        self.lsbd[packet.get('from')] = packet.get("payload") #Agrgear la info a nuestra bd

        #Ahora verificar si debe ser reenviado
        if packet.get('ttl') > 0:
           await self.forward(packet)

    async def send_own_info(self):
        pass

    async def forward(self, packet):
        packet = copy.deepcopy(packet)
        packet["ttl"] -= 1
        if len(packet["headers"]) == 3:
            del packet["headers"][0]
            packet["headers"][2] = self.node_id
        else:
            packet["headers"].append(self.node_id)

        for neighbor in self.neighbors:
            await self.network.publish(neighbor, packet) 
        print(f"Resending packet to neighbots")



    async def handle_sending_message(self, packet):
        if packet.get('to') == self.node_id:
            print(f"I am the destiny and the message is {packet.get('payload')} ")
        else: 
            #Calcular a que nodo enviar
            pass


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