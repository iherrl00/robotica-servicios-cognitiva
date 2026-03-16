# Ejercicios 2 y 3 - Primer Behavior Tree en ROS 2

## Ejercicio 2 - Diseño del árbol en XML

El árbol implementa el siguiente comportamiento:

- Si hay obstáculo → detenerse → girar
- Si no hay obstáculo → avanzar

### Estructura del árbol

```
Fallback (?)
├── Sequence (→) [obstacle_detected]
│   ├── Condition: IsObstacleDetected  — ¿Hay obstáculo?
│   ├── Action: Stop                   — Detenerse
│   └── Action: Turn                   — Girar
└── Action: MoveForward                — Avanzar
```

### Lógica de control

El nodo raíz es un **Fallback** que evalúa sus hijos en orden:

1. Primero evalúa el **Sequence** de obstáculo:
   - Si `IsObstacleDetected` devuelve SUCCESS → ejecuta `Stop` y `Turn` → Sequence devuelve SUCCESS → Fallback para.
   - Si `IsObstacleDetected` devuelve FAILURE → Sequence falla inmediatamente → Fallback pasa al siguiente hijo.
2. Si el Sequence falló → ejecuta `MoveForward`.

### Archivo XML

`trees/obstacle_tree.xml`

```xml
<?xml version="1.0"?>
<root main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <Fallback name="root">
      <Sequence name="obstacle_detected">
        <Condition ID="IsObstacleDetected" name="¿Hay obstáculo?"/>
        <Action ID="Stop" name="Detenerse"/>
        <Action ID="Turn" name="Girar"/>
      </Sequence>
      <Action ID="MoveForward" name="Avanzar"/>
    </Fallback>
  </BehaviorTree>
</root>
```

---

## Ejercicio 3 - Implementación en ROS 2

### Paquete

```
bt_robot/
├── CMakeLists.txt
├── package.xml
├── src/
│   └── bt_robot_node.cpp
└── trees/
    └── obstacle_tree.xml
```

### Dependencias

- `rclcpp`
- `behaviortree_cpp_v3`

### Compilar

```bash
cd ~/ros2_ws
colcon build --packages-select bt_robot
source install/setup.bash
```

### Ejecutar

```bash
ros2 run bt_robot bt_robot_node
```

### Salida esperada

```
[INFO] [BT]: Condición: HAY obstáculo
[INFO] [BT]: Acción: DETENERSE
[INFO] [BT]: Acción: GIRAR
...
[INFO] [BT]: Condición: NO hay obstáculo
[INFO] [BT]: Acción: AVANZAR
```

### Implementación de los nodos

| Nodo | Tipo | Descripción |
|------|------|-------------|
| `IsObstacleDetected` | Condition | Simula un obstáculo cada 3 ticks alternando SUCCESS/FAILURE |
| `Stop` | SyncAction | Simula la acción de detenerse, devuelve SUCCESS |
| `Turn` | SyncAction | Simula la acción de girar, devuelve SUCCESS |
| `MoveForward` | SyncAction | Simula avanzar, devuelve SUCCESS |

El BT se ejecuta a **1 Hz** mediante `rclcpp::Rate`.
