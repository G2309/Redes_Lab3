import sys, json, asyncio 
import threading
import time
from network.Network import NetworkNodePubSub
from algorithm.Flooding import FloodingNode
from algorithm.linkStateRouting import Node
from algorithm.dijkstraRouting import DijkstraNode

async def send_periodic_lsa(algorithm, interval=10):
    """Función para enviar LSAs periódicamente"""
    while True:
        await asyncio.sleep(interval)  
        try:
            if hasattr(algorithm, 'send_own_info'):
                await algorithm.send_own_info()
        except Exception as e:
            print(f"Error enviando LSA periódico: {e}")

async def send_initial_hello(algorithm):
    """Envía mensaje HELLO inicial después de un pequeño delay"""
    await asyncio.sleep(2)  # Esperar 2 segundos para que todos los nodos estén listos
    if hasattr(algorithm, 'send_hello_message'):
        await algorithm.send_hello_message()

async def user_input_loop(net, algorithm):
    while True:
        try:
            msg = await asyncio.to_thread(input, "Message: ")
            dest = await asyncio.to_thread(input, "To: ")
            
            if isinstance(algorithm, FloodingNode):
                packet = {
                    "proto": "flooding",
                    "type": "message",
                    "from": net.node_id,
                    "to": dest,
                    "ttl": 5,
                    "headers": [],
                    "payload": msg
                }
                await algorithm.send_message(packet)
            else:
                # Para LSR y Dijkstra
                await algorithm.send_message(dest, msg)
                
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
        except Exception as e:
            print(f"Error en user_input_loop: {e}")

async def main():
    if len(sys.argv) < 5:
        print("Uso: python main.py <node_id> <topo_file> <msg_file> <algorithm>")
        sys.exit(1)
        
    node_id = sys.argv[1]
    topo_file = sys.argv[2]
    msg_file = sys.argv[3]
    algorithm_type = sys.argv[4]
    
    with open(topo_file) as f:
        full_config = json.load(f)
        config = full_config["config"]
    
    if node_id not in config:
        print(f"Error: Nodo {node_id} no encontrado en la configuración")
        sys.exit(1)
        
    node_info = config[node_id]
    neighbors = node_info["neighbors"]
    
    channels = [node_id]
    net = NetworkNodePubSub(node_id, channels, neighbors)
    await net.start()
    
    # Seleccionar algoritmo dinámicamente
    if algorithm_type == "flooding":
        algorithm = FloodingNode(node_id, neighbors, net)
        
    elif algorithm_type in ("lsr", "linkstate"):
        algorithm = Node(node_id, neighbors, net)
        # Construir tabla inicial basada en vecinos directos
        algorithm.build_routing_table()
        
        # Enviar LSA inicial
        await algorithm.send_own_info()
        
        # Programar LSAs periódicos
        asyncio.create_task(send_periodic_lsa(algorithm, 15))
        
    elif algorithm_type == "dijkstra":
        algorithm = DijkstraNode(node_id, neighbors, net, config)

        
    else:
        print(f"Algoritmo no soportado: {algorithm_type}")
        print("Algoritmos disponibles: flooding, lsr, dijkstra")
        sys.exit(1)
    
    net.set_algorithm(algorithm)
    
    # Iniciar el bucle de entrada del usuario
    asyncio.create_task(user_input_loop(net, algorithm))
    
    try:
        await net.listen()
    except KeyboardInterrupt:
        print(f"\n[{node_id}] Cerrando nodo...")

if __name__ == "__main__":
    asyncio.run(main())
