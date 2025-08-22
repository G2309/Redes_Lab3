import sys, json, time
import threading
from network.Network import NetworkNode
from algorithm.Flooding import FloodingNode

if __name__ == "__main__":
    node_id = sys.argv[1]
    topo_file = sys.argv[2]
    msg_file = sys.argv[3]

    with open(topo_file) as f:
        config = json.load(f)["config"]

    node_info = config[node_id]
    port = node_info["port"]
    neighbors = node_info["neighbors"]

    net = NetworkNode(node_id, port)
    # CHANGE HERE TO SELECT ALGORTIHM DINAMICALLY
    algorithm = FloodingNode(node_id, neighbors, net)
    net.set_algorithm(algorithm)

    net.start()
    time.sleep(2)  # Dar tiempo a que arranquen los servidores

    with open(msg_file) as f:
        packet = json.load(f)
    if node_id == packet["from"]: 
        algorithm.send_message(packet)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Programa terminado.")

