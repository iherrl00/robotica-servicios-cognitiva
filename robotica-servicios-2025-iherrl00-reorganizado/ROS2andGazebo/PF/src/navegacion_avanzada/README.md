# Práctica Final: Navegación Avanzada con Nav2

**Autor:** Isabella Herrarte  
**Máster:** Robótica e Inteligencia Artificial  
**Asignatura:** Robótica de Servicios

## Descripción del Proyecto

Este proyecto implementa un sistema de navegación avanzada para un robot usando ROS 2 Jazzy y Nav2. El robot puede:

- Leer waypoints desde un archivo YAML
- Navegar secuencialmente o aleatoriamente
- Interactuar mediante entrada de teclado (alternativa a voz)
- Cambiar entre múltiples planificadores dinámicamente (opcional)

## Estructura del Proyecto

```
navegacion_avanzada/
├── config/
│   ├── waypoints.yaml          # Puntos de navegación
│   └── planner_server.yaml     # Configuración de planificadores
├── navegacion_avanzada/
│   ├── __init__.py
│   ├── waypoint_navigator.py   # Script principal
│   └── planner_changer.py      # Cambio de planificadores
├── setup.py
├── package.xml
└── README.md
```

## Instalación y Configuración

### 1. Crear el paquete

```bash
cd ~/robotica-servicios-2025-iherrl00/ros2_ws/src
ros2 pkg create --build-type ament_python navegacion_avanzada --dependencies rclpy nav2_simple_commander geometry_msgs
```

### 2. Copiar los archivos

Copia los archivos proporcionados en sus ubicaciones correspondientes:

- `waypoint_navigator.py` → `navegacion_avanzada/waypoint_navigator.py`
- `planner_changer.py` → `navegacion_avanzada/planner_changer.py`
- `waypoints.yaml` → `config/waypoints.yaml`
- `planner_server.yaml` → `config/planner_server.yaml`
- `setup.py` → raíz del paquete

### 3. Dar permisos de ejecución

```bash
chmod +x navegacion_avanzada/waypoint_navigator.py
chmod +x navegacion_avanzada/planner_changer.py
```

### 4. Compilar el workspace

```bash
cd ~/robotica-servicios-2025-iherrl00/ros2_ws
colcon build --packages-select navegacion_avanzada
source install/setup.bash
```

## Instrucciones de Ejecución

### Terminal 1: Lanzar Gazebo y Nav2

```bash
# Si usas TurtleBot3
export TURTLEBOT3_MODEL=waffle
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

### Terminal 2: Lanzar el sistema de navegación

```bash
source ~/robotica-servicios-2025-iherrl00/ros2_ws/install/setup.bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True
```

### Terminal 3: Ejecutar el navegador de waypoints

```bash
source ~/robotica-servicios-2025-iherrl00/ros2_ws/install/setup.bash
ros2 run navegacion_avanzada waypoint_navigator
```

### Terminal 4 (Opcional): Cambiar planificadores

```bash
source ~/robotica-servicios-2025-iherrl00/ros2_ws/install/setup.bash
ros2 run navegacion_avanzada planner_changer
```

## Uso del Sistema

1. **Inicio:** El robot espera a que Nav2 esté activo
2. **Selección de modo:** Elige navegación `(s)ecuencial` o `(r)andom`
3. **Durante la navegación:**
   - El robot se mueve hacia cada waypoint
   - Muestra la distancia restante en tiempo real
   - Al llegar, pregunta si continuar

## Respuestas a las Preguntas

### 1. Implementación de lectura de waypoints

**Método implementado:**
- Uso de la librería `yaml` para parsear el archivo `waypoints.yaml`
- Función `read_waypoints()` que carga los datos en una lista de diccionarios
- Cada waypoint contiene: nombre, coordenadas (x, y) y orientación (z, w)

**Integración con Nav2:**
```python
goal_pose = PoseStamped()
goal_pose.header.frame_id = 'map'
goal_pose.pose.position.x = waypoint['x']
goal_pose.pose.position.y = waypoint['y']
goal_pose.pose.orientation.z = waypoint['z']
goal_pose.pose.orientation.w = waypoint['w']

navigator.goToPose(goal_pose)
```

### 2. Paquetes de voz utilizados

**Para esta implementación básica:**
- **Input de usuario:** `input()` de Python (teclado)
- **Output del robot:** `print()` y logging

**Alternativas recomendadas para voz real:**
- **Síntesis de voz:** 
  - `sound_play` (ROS wrapper)
  - `pyttsx3` (Python TTS)
  - `festival_tts`
- **Reconocimiento de voz:**
  - `speech_recognition` (Python)
  - `whisper` de OpenAI
  - `chatbot_ros` de mgonzs13

### 3. Configuración de múltiples planificadores

**Proceso de configuración:**

#### a) Desde archivo YAML (`planner_server.yaml`):

```yaml
planner_server:
  ros__parameters:
    planner_plugins: ["GridBased", "SmacPlanner"]
    
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      # parámetros...
    
    SmacPlanner:
      plugin: "nav2_smac_planner/SmacPlanner2D"
      # parámetros...
```

#### b) Cambio dinámico durante ejecución:

Se utiliza el servicio `set_parameters` de ROS 2:

```python
# Crear cliente del servicio
client = self.create_client(SetParameters, '/planner_server/set_parameters')

# Cambiar parámetro planner_id
param = Parameter()
param.name = 'planner_id'
param.value = ParameterValue(string_value='SmacPlanner')

# Llamar al servicio
client.call_async(request)
```

**Ventajas de cada enfoque:**
- **Archivo de configuración:** Cambio permanente, se aplica al iniciar
- **Cambio dinámico:** Flexible, permite adaptar en tiempo real

### 4. Criterios para cambio de planificador (Opcional)

**Criterios implementables:**

1. **Áreas congestionadas:**
   - Detectar alta densidad de obstáculos
   - Cambiar a SmacPlanner (mejor en espacios estrechos)

2. **Espacios abiertos:**
   - Usar NavFn (más rápido, eficiente)

3. **Robot atascado:**
   - Si `isTaskComplete()` tarda mucho
   - Alternar entre planificadores para encontrar ruta

**Efectos en el comportamiento:**

| Situación | NavFn (GridBased) | SmacPlanner |
|-----------|-------------------|-------------|
| Navegación normal | Rápido, directo | Más suave, natural |
| Objeto en ruta | Rodeo simple | Maniobras complejas |
| Atascado | Puede fallar | Mejor escape |

**Ejemplo de lógica:**

```python
if feedback.distance_remaining > 5.0 and tiempo_sin_avance > 10:
    # Espacio abierto pero atascado
    change_planner('SmacPlanner')
elif obstacle_density < 0.3:
    # Espacio libre
    change_planner('GridBased')
```

### Problemas detectados:

- **Problema 1:** Waypoints fuera del mapa
  - **Solución:** Ajustar coordenadas al mapa usado

## Dependencias

```xml
<depend>rclpy</depend>
<depend>nav2_simple_commander</depend>
<depend>geometry_msgs</depend>
<depend>rcl_interfaces</depend>
<depend>yaml</depend>
```

## Mejoras Futuras

- [ ] Integrar síntesis de voz real (pyttsx3)
- [ ] Reconocimiento de voz con speech_recognition
- [ ] Detección automática de obstáculos para cambio de planificador
- [ ] Interfaz gráfica con RQt

## Licencia

Apache License 2.0

**Fecha de entrega:** Enero 2026  
**Versión:** 1.0.0
