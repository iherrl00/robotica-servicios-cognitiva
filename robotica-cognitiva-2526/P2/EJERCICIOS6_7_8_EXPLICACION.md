# Ejercicios 6, 7 y 8 - Groot

## Ejercicio 6 - Creación del árbol en Groot

Se cargó el archivo `obstacle_tree.xml` en el Editor de Groot mediante **File → Load Tree**.
El árbol generado visualmente muestra:

- Nodo raíz **Fallback**
  - **Sequence** (obstacle_detected)
    - Condition: `IsObstacleDetected` — ¿Hay obstáculo?
    - Action: `Stop` — Detenerse
    - Action: `Turn` — Girar
  - Action: `MoveForward` — Avanzar

El XML exportado desde Groot es idéntico al creado manualmente en el ejercicio 2.

---

## Ejercicio 7 - Conectar Groot con el BT en ejecución

Se añadió el `PublisherZMQ` al nodo ROS 2:

```cpp
#include <behaviortree_cpp_v3/loggers/bt_zmq_publisher.h>
...
BT::PublisherZMQ publisher(tree);
```

Con el nodo en ejecución, se conectó Groot en modo **Monitor** con:
- Server IP: `localhost`
- Publisher Port: `1666`
- Server Port: `1667`

Groot recibió los mensajes correctamente (Messages received aumentando en tiempo real).

---

## Ejercicio 8 - Análisis del flujo de ejecución

### Nodos que se activan

Durante la ejecución se observaron dos patrones alternos:

**Cuando HAY obstáculo:**
1. `Fallback` (root) — se activa, pasa al primer hijo
2. `Sequence` (obstacle_detected) — se activa
3. `IsObstacleDetected` → **SUCCESS** (verde)
4. `Stop` → **SUCCESS** (verde)
5. `Turn` → **SUCCESS** (verde)
6. `Sequence` → **SUCCESS** → `Fallback` → **SUCCESS**
7. `MoveForward` — no se evalúa (Fallback ya tuvo éxito)

**Cuando NO hay obstáculo:**
1. `Fallback` (root) — se activa, pasa al primer hijo
2. `Sequence` (obstacle_detected) — se activa
3. `IsObstacleDetected` → **FAILURE** (rojo)
4. `Sequence` → **FAILURE** inmediatamente (Stop y Turn no se evalúan)
5. `Fallback` pasa al segundo hijo
6. `MoveForward` → **SUCCESS** (verde)
7. `Fallback` → **SUCCESS**

### Por qué algunos nodos fallan o tienen éxito

- `IsObstacleDetected` falla cuando no hay obstáculo → corta el Sequence por diseño del nodo AND.
- `Stop` y `Turn` solo se ejecutan si la condición previa tuvo éxito → eficiencia del Sequence.
- `MoveForward` solo se ejecuta como último recurso del Fallback → solo cuando no hay obstáculo.

### Flujo observado en Groot

Los nodos cambian de color en tiempo real:
- **Verde** → SUCCESS
- **Rojo** → FAILURE
- **Gris** → no evaluado en este tick
