import sys, json, time
import threading
from network.Network import NetworkNode
from algorithm.Flooding import FloodingNode
from algorithm.linkStateRouting import Node

import sys, json, time
import threading
from network.Network import NetworkNode
from algorithm.Flooding import FloodingNode
from algorithm.linkStateRouting import Node


def send_periodic_lsa(algorithm, interval=10):
    """Función para enviar LSAs periódicamente"""
    while True:
        time.sleep(interval)
        try:
            algorithm.send_own_lsa_package()
        except Exception as e:
            print(f"Error enviando LSA periódico: {e}")

if __name__ == "__main__":
    node_id = sys.argv[1]
    topo_file = sys.argv[2]
    msg_file = sys.argv[3]
    algorithm_type = sys.argv[4]

    with open(topo_file) as f:
        config = json.load(f)["config"]

    node_info = config[node_id]
    port = node_info["port"]
    neighbors = node_info["neighbors"]

    net = NetworkNode(node_id, port)
    
    # Seleccionar algoritmo dinámicamente
    if algorithm_type == "flooding":
        algorithm = FloodingNode(node_id, neighbors, net)
        
    elif algorithm_type == "lsr":
        algorithm = Node(node_id, neighbors, net)
        # Construir tabla inicial basada en vecinos directos
        algorithm.build_routing_table()
        
        # Enviar LSA inicial
        algorithm.send_own_lsa_package()
        
        # Iniciar hilo para LSAs periódicos
        lsa_thread = threading.Thread(target=send_periodic_lsa, args=(algorithm, 15))
        lsa_thread.daemon = True
        lsa_thread.start()
    
    elif algorithm_type == "dijkstra":
        from algorithm.dijkstraRouting import DijkstraNode
        algorithm = DijkstraNode(node_id, neighbors, net)
        
    else:
        print(f"Algoritmo no soportado: {algorithm_type}")
        sys.exit(1)

    net.set_algorithm(algorithm)
    net.start()
    time.sleep(3)  # Dar tiempo a que arranquen los servidores y se intercambien LSAs

    # Leer y procesar el archivo de mensajes
    with open(msg_file) as f:
        packet = json.load(f)
    
    # Enviar mensaje según el algoritmo
    if node_id == packet["from"]:
        if algorithm_type == "flooding":
            algorithm.send_message(packet)
        elif algorithm_type == "lsr":
            # Para LSR, usar send_data_message
            destination = packet["to"]
            payload = packet.get("payload", "")
            print(f"[{node_id}] Iniciando envío de mensaje a {destination}")
            time.sleep(2)  # Esperar un poco más para que se establezcan las rutas
            algorithm.send_data_message(destination, payload)
        elif algorithm_type == "dijkstra":
            destination = packet["to"]
            payload = packet.get("payload", "")
            algorithm.send_data_message(destination, payload)

    try:
        while True:
            # Mostrar estado periódicamente para debug
            if algorithm_type == "lsr":
                time.sleep(20)
                status = algorithm.get_status()
                print(f"\n[{node_id}] === Estado actual ===")
                print(f"Vecinos: {status['neighbors']}")
                print(f"Nodos conocidos: {status['lsdb_nodes']}")
                print(f"Tabla de rutas: {status['routing_table']}")
                print("=" * 30)
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        print("Programa terminado.")
