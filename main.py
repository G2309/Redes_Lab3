import sys, json, asyncio 
from network.Network import NetworkNodePubSub
from algorithm.Flooding import FloodingNode
from algorithm.linkStateRouting import Node


async def send_periodic_lsa(algorithm, interval=10):
    """Función para enviar LSAs periódicamente"""
    while True:
        time.sleep(interval)
        try:
            algorithm.send_own_lsa_package()
        except Exception as e:
            print(f"Error enviando LSA periódico: {e}")

async def user_input_loop(node, algorithm):
    while True:
        msg = await asyncio.to_thread(input, "Message: ")
        dest = await asyncio.to_thread(input, "To: ")

        packet = {
            "proto": "flooding" if isinstance(algorithm, FloodingNode) else "lsr",
            "type": "message",
            "from": node.node_id,
            "to": dest,
            "ttl": 5,
            "headers": [],
            "payload": msg
        }

        await algorithm.send_message(packet) if isinstance(algorithm, FloodingNode) else await algorithm.send_data_message(dest, msg)

async def main():
    node_id = sys.argv[1]
    topo_file = sys.argv[2]
    msg_file = sys.argv[3]
    algorithm_type = sys.argv[4]

    with open(topo_file) as f:
        config = json.load(f)["config"]

    node_info = config[node_id]
    neighbors = node_info["neighbors"]

    channels = [node_id]
    net = NetworkNodePubSub(node_id, channels, neighbors)

    await net.start()
    
    # Seleccionar algoritmo dinámicamente
    if algorithm_type == "flooding":
        algorithm = FloodingNode(node_id, neighbors, net)
        
    elif algorithm_type in ("lsr", "dijkstra"):
        algorithm = Node(node_id, neighbors, net)
        # Construir tabla inicial basada en vecinos directos
        algorithm.build_routing_table()
        
        # Enviar LSA inicial
        algorithm.send_own_lsa_package()
        
        asyncio.create_task(send_periodic_lsa(algorithm, 15))
        
    else:
        print(f"Algoritmo no soportado: {algorithm_type}")
        sys.exit(1)

    net.set_algorithm(algorithm)

    asyncio.create_task(user_input_loop(net, algorithm))

    await net.listen()

if __name__ == "__main__":
    asyncio.run(main())
