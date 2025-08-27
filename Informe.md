# Laboratorio 3 Informe

Integrantes:
- José Prince
- Pedro Guzmán
- Gustavo Cruz

En este laboratorio se busca comprender cómo funcionan las tablas de enrutamiento e implementar los algoritmos de enrutamiento y probarlos en una red simulada.

## Descripción de los algoritmos

Loa algoritmos de enrutamiento utilizados fueron los siguientes:

### Dijsktra
Este algoritmo se basa en calcular la ruta más corta entre un nodo origen y todos los demás nodos de la red, utilizando la información de costos asociados a cada enlace. El nodo mantiene un grafo de la red y aplica el algoritmo de Dijkstra para determinar cuál es el camino con menor costo acumulado hacia cada destino.

* Ventajas:

  * Siempre encuentra la ruta más corta disponible.
  * Es eficiente en redes con topologías estáticas o poco cambiantes.
  * Permite obtener las mejores rutas de manera determinística.

* Desventajas:

  * Necesita que el nodo conozca la topología completa de la red.
  * Requiere más memoria y procesamiento que otros algoritmos simples.
  * Si la red cambia con frecuencia, el cálculo debe repetirse, aumentando la carga de cómputo.

---

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

Este algoritmo funciona de esta manera:

- Cada nodo es conciente de sus vecinos al inicio
- Un nodo envía un paquete LSA, este paquete contiene información sobre sus vecinos
- Todos los nodos se reenvían los paquetes LSA que reciben para que cada nodo puede formar su propia topología de la red
- Cuando un nodo ya sabe la topología, aplica Dijkstra y calcula las mejores rutas

- Ventajas: 

  - Cada nodo es conciente de la topología de la red entera.
  - Más presición en el enrutamiento.

- Desventajas: 
  - Si es una red muy grande el algoritmo Dijkstra puede crecer en complejidad.
  - Consume mucha memoria pues cada nodo debe almacenar que paquetes ha recibido y toda la topología de la red.

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
[Prueba Dijkstra](https://youtu.be/r7QjurCP-tg)

- Link State Routing:

[Prueba link state Routing](https://youtu.be/lNOLOMpv2GQ)

## Discusión de resultados

Para la prueba de Flooding se hizo con esta red pequeña de cuatro nodos. El algortimo de Flooding es bastante fácil de comprender y esto es apreciable es la simulación realizada. Se pudo observar como se hacia el envio de paquetes inciando desde el nodo A y terminando en el nodo D. En este caso podemos ver como el mensaje llega dos veces al nodo D debido a que el mensaje que se envió por el nodo C llego después que el mensaje del nodo B al nodo D. También podemos notar que tal vez no se envien paquetes al nodo vecino que lo envió pero esto no evita la duplicación de paquetes a lo largo de la red, es por eso que se le añade un ttl para evitar que el mensaje se expanda a lo largo de toda la red cuando no es necesario. Podemos ver que este algortimo marca una forma rápida para el envió de un paquete debido a que no importa hacia donde se envié el paquete este siempre llega por la vía más rápida, en el caso de que D fuera vecino de A se vería como el paquete llega mucho más rápido que al ser enviado mediante B o D.  

La prueba de LSR se hizo con la misma topología de prueba que el algoritmo de Flooding. Se puede observar que los nodos constantemente se envían sus paquetes LSA para actualizar sus respectivas topologías y determinar cuál es el mejor camino. Otro detalle es que B muestra que recibió un mensaje de A para D y lo reenvía, el mensaje paso por B pues es el camino más óptimo para llegar a D desde A. Para esta implementación usamos un ttl de 10 y por eso se reciben más pquetes de lo normal y sale constantemente que se descartaron mensajes pues están duplicados, lo ideal es utlizar un valor que esea igual a la longitud de la red. 

En el caso de Dijkstra, la simulación mostró cómo cada nodo, al recibir la información de topología, aplica el algoritmo para calcular las rutas más cortas hacia los demás. Esto permitió que el mensaje enviado desde A a D encontrara el camino más eficiente sin duplicaciones, a diferencia del Flooding. Sin embargo, se notó que en cada actualización de topología los cálculos deben repetirse, lo que incrementa el costo computacional si la red fuera más grande o muy dinámica.

## Conclusiones

El algortimo de enrutamiento Flooding se presenta como una forma de envío rápido de paquetes pero que se puede volver ineficiente par redes grandes debido a la gran carga que se hace en la red al enviar el paquete por todos los nodos de la red.

El algoritmo LSR es una buen enfoque para enviar mensajes de forma eficiente a través de una red de routers, sin embargo puede consumir mucha memoria y consumir muchois recursos pues constantemente se está actualizando debido al envió de paquetes LSR. 

El algoritmo de Dijkstra garantiza siempre la ruta más corta de manera determinista y sin duplicación de mensajes, lo que lo hace más preciso que Flooding. No obstante, necesita que cada nodo disponga de la topología completa y recalcula rutas ante cualquier cambio, lo que en redes grandes puede volverlo costoso en tiempo y memoria.

## Comentarios

La práctica permitió comparar diferentes enfoques de enrutamiento en redes. Flooding mostró simplicidad y rapidez a costa de eficiencia, LSR ofreció un balance entre conocimiento de la red y precisión en el enrutamiento, y Dijkstra demostró ser el más exacto en la elección de rutas, aunque dependiente de recursos computacionales más altos.

## Referencias

GeeksforGeeks. (2023, 22 abril). Fixed and Flooding Routing algorithms. GeeksforGeeks. https://www.geeksforgeeks.org/computer-networks/fixed-and-flooding-routing-algorithms/
