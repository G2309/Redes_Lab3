import socket
import asyncio
import json

class Node:

    def __init__(self, id, port, neighbors):
        self.id = id #Identificador único del nodo
        self.port = port #El puerto en el que se encuentra nuestro nodo
        self.db  = {}  #la db con los datos de la topología de la red
        self.neighbors = neighbors #siempre queremos inforación de los vecinos inmediatos
        self.db.update(neighbors)
        self.recived_messages = {} #Aquí guardamos lo que hemos recibido de los demás nodos
        self.seq_counter = -1 #Cada vez que enviemos nuestra información aumentaremos la secuencia

    def send_own_lsa_package(self):
        self.seq_counter += 1
        for i in self.neighbors.values():

            message = json.dumps({"source": self.id, 
                                  "port": self.port,
                                  "neigbors": self.neighbors,
                                  "ttl": 50,
                                  "seq": self.seq_counter +1,
                                  "mesassage_type": "LSA" })
            
    def send_hello_message(self):
        for i in self.neighbors.values():

            message = json.dumps({"source": self.id, 
                                  "port": self.port,
                                  "cost": self.neighbors[i]["cost"],
                                  "mesassage_type": "Hello" })
            
    def send_to_other_node(self, destination):
        #Destination: el nodo al que vamos a enviar el mensaje
        pass

    def handle_message(self, message):
        #Si recibimos un hello, añadimos al vecino
        if message["mesagge_type"] == "Hello":
            self.add_neighbors[message["source"]] = {"cost": message["cost"], "port": message["port"] }

        else: #si un paquete LSA de otro nodo
            pass



    


