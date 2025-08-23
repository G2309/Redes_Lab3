# Laboratorio 3 Informe

Integrantes:
- José Prince
- Pedro Guzmán
- Gustavo Cruz

En este laboratorio se busca comprender cómo funcionan las tablas de enrutamiento e implementar los algoritmos de enrutamiento y probarlos en una red simulada.

## Descripción de los algoritmos

Loa algoritmos de enrutamiento utilizados fueron los siguientes:

### Dijsktra

### Flooding

Este algoritmo de enrutamiento funciona enviando un paquete desde un nodo a todos sus vecinos, quienes a su vez lo reenvían a los suyos y así sucesivamente, hasta que el mensaje alcanza a todos los nodos de la red. Cada

- Ventajas:
  - Es robusto porque permite enviar mensajes de emergencia o inmediatos.
  - EL flooding siempre elige la ruta más corta.
  - Transmite mensaje a todos los nodos.

- Desventajas:
  - Puede llegar a crear una congestión en la red, debido al envio masivos de mensajes que se hace a lo largo de esta.
  - Este algoritmo utiliza muchos recursos de red, incluyendo ancho de banda y potencia de procesamiento, para entregar paquetes.

### Link State Routing

## Pruebas

En este caso para las pruebas se utilizó la siguiente topología:

{
  "type": "topo",
  "config": {
    "A": {"port": 5000, "neighbors": {"B": ["localhost", 5001], "C": ["localhost", 5002]}},
    "B": {"port": 5001, "neighbors": {"A": ["localhost", 5000], "D": ["localhost", 5003]}},
    "C": {"port": 5002, "neighbors": {"A": ["localhost", 5000], "D": ["localhost", 5003]}},
    "D": {"port": 5003, "neighbors": {"B": ["localhost", 5001], "C": ["localhost", 5002]}}
  }
}

Este fue el mensaje que se envió a través de la red:

{
  "proto": "flooding",
  "type": "message",
  "from": "A",
  "to": "D",
  "ttl": 5,
  "headers": [],
  "payload": "¡Hola desde A! ¿Llegas a D?"
}

- Flooding:

[Prueba Flooding.webm](https://github.com/user-attachments/assets/b7e538ca-dee5-4ba6-8a99-dd87fe21c29b)

- Dijstktra:

- Link State Routing:

## Discusión de resultados

Para la prueba de Flooding se hizo con esta red pequeña de cuatro nodos. El algortimo de Flooding es bastante fácil de comprender y esto es apreciable es la simulación realizada. Se pudo observar como se hacia el envio de paquetes inciando desde el nodo A y terminando en el nodo D. En este caso podemos ver como el mensaje llega dos veces al nodo D debido a que el mensaje que se envió por el nodo C llego después que el mensaje del nodo B al nodo D. También podemos notar que tal vez no se envien paquetes al nodo vecino que lo envió pero esto no evita la duplicación de paquetes a lo largo de la red, es por eso que se le añade un ttl para evitar que el mensaje se expanda a lo largo de toda la red cuando no es necesario. Podemos ver que este algortimo marca una forma rápida para el envió de un paquete debido a que no importa hacia donde se envié el paquete este siempre llega por la vía más rápida, en el caso de que D fuera vecino de A se vería como el paquete llega mucho más rápido que al ser enviado mediante B o D.  


## Conclusiones

El algortimo de enrutamiento Flooding se presenta como una forma de envío rápido de paquetes pero que se puede volver ineficiente par redes grandes debido a la gran carga que se hace en la red al enviar el paquete por todos los nodos de la red.


## Comentarios

## Referencias

GeeksforGeeks. (2023, 22 abril). Fixed and Flooding Routing algorithms. GeeksforGeeks. https://www.geeksforgeeks.org/computer-networks/fixed-and-flooding-routing-algorithms/
