# Se utilizara una cola de prioridad para visitar nodos con menor costo acumulado
import heapq

class DijkstraRouter:
    def __init__(self, graph, start):
        #graph: Diccionario {nodo: [(vecino, peso)]} 
        #start: Nodo de inicio para calcular rutas.
        self.graph = graph
        self.start = start
        self.distances = {}
        self.previous = {}
        self.routing_table = {}

    def calculate_routes(self):
        # inicializar distancias como infinitas
        self.distances = {node: float('inf') for node in self.graph}
        # inicializar nodos anteriores como None
        self.previous = {node: None for node in self.graph}
        self.distances[self.start] = 0

        # cola de prioridad para visitar nodos con menor costo acumulado
        queue = [(0, self.start)]

        while queue:
            # extraer el nodo con menor distancia acumulada
            current_dist, current_node = heapq.heappop(queue)

            if current_dist > self.distances[current_node]:
                continue

            # examinar vecinos del nodo actual
            for neighbor, weight in self.graph[current_node]:
                distance = current_dist + weight  # nueva distancia pasando por nodo actual
                if distance < self.distances[neighbor]:  # Si encontramos un camino más corto
                    self.distances[neighbor] = distance
                    self.previous[neighbor] = current_node  # Guardar predecesor
                    heapq.heappush(queue, (distance, neighbor))

        # tabla de enrutamiento
        self.routing_table = {}
        for node in self.graph:
            if node == self.start:
                continue
            next_hop = node
            # Retroceder hasta encontrar el primer salto desde el nodo de inicio
            while self.previous[next_hop] != self.start and self.previous[next_hop] is not None:
                next_hop = self.previous[next_hop]
            self.routing_table[node] = {
                "cost": self.distances[node],  # Costo total
                "next_hop": next_hop           # Primer salto
            }

    def get_routing_table(self):
        return self.routing_table

