import time
import threading
from network.Network import NetworkNode
from algorithm.Flooding import FloodingNode

if __name__ == "__main__":
    network_config = {
        "A": {"port": 5000, "neighbors": {"B": ("localhost", 5001), "C": ("localhost", 5002)}},
        "B": {"port": 5001, "neighbors": {"A": ("localhost", 5000), "D": ("localhost", 5003)}},
        "C": {"port": 5002, "neighbors": {"A": ("localhost", 5000), "D": ("localhost", 5003)}},
        "D": {"port": 5003, "neighbors": {"B": ("localhost", 5001), "C": ("localhost", 5002)}},
    }

    nodes = {}
    threads = []

    for node_id, config in network_config.items():
        net = NetworkNode(node_id, config["port"])
        flooding = FloodingNode(node_id, config["neighbors"], net)
        net.set_algorithm(flooding)

        nodes[node_id] = flooding
        thread = threading.Thread(target=net.start)
        thread.start()
        threads.append(thread)

    time.sleep(2)  # Dar tiempo a que arranquen los servidores

    # Enviar un mensaje desde A hacia D
    nodes["A"].send_initial_message("D", "¡Hola desde A! ¿Llegas a D?")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Programa terminado.")

