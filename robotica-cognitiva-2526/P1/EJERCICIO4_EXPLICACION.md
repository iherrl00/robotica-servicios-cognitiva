# Ejercicio 4: Integración de FSM con servicios en ROS2

## Funcionamiento de la integración

### Componentes principales

#### 1. **ServiceState**
Clase especializada que extiende `State` para interactuar con servicios ROS2:
```python
class AddTwoIntsState(ServiceState):
    def __init__(self) -> None:
        super().__init__(
            AddTwoInts,                      # Tipo del servicio
            "/add_two_ints",                 # Nombre del servicio
            self.create_request_handler,     # Callback para crear request
            ["outcome1"],                    # Outcomes personalizados
            self.response_handler,           # Callback para procesar response
        )
```

#### 2. **create_request_handler**
Función que crea el mensaje de solicitud desde el Blackboard:
```python
def create_request_handler(self, blackboard: Blackboard) -> AddTwoInts.Request:
    req = AddTwoInts.Request()
    req.a = blackboard["a"]  # Lee del Blackboard
    req.b = blackboard["b"]
    return req
```

#### 3. **response_handler**
Función que procesa la respuesta y actualiza el Blackboard:
```python
def response_handler(self, blackboard: Blackboard, response: AddTwoInts.Response) -> str:
    blackboard["sum"] = response.sum  # Guarda en Blackboard
    return "outcome1"                 # Retorna outcome
```

#### 4. **CbState**
Estado simple basado en callbacks (sin ROS2):
```python
CbState([SUCCEED], set_ints)  # Ejecuta la función set_ints
```

### Flujo de ejecución

1. **SETTING_INTS**: Inicializa `a=10` y `b=5` en el Blackboard
2. **ADD_TWO_INTS**: 
   - Lee `a` y `b` del Blackboard
   - Crea request y llama al servicio
   - Espera respuesta
   - Guarda `sum=15` en Blackboard
3. **PRINTING_SUM**: Lee `sum` del Blackboard y lo muestra

### Ventajas de esta arquitectura

- **Desacoplamiento**: La FSM no necesita conocer detalles de implementación del servicio
- **Sincronización automática**: ServiceState maneja la espera de respuesta
- **Gestión de errores**: Outcomes SUCCEED/ABORT para manejar fallos
- **Reutilización**: El mismo estado puede usarse en diferentes FSMs

## Modificación realizada: Múltiples solicitudes

### Cambios implementados

1. **Inicialización de datos** (`INIT_DATA`):
   - Lista de operaciones a realizar: `[(10,5), (20,15), (7,3), (100,50)]`
   - Lista vacía para almacenar resultados
   - Contador de índice

2. **Preparación de cada solicitud** (`PREPARE_REQUEST`):
   - Lee la siguiente operación de la lista
   - La coloca en el Blackboard como `current_a` y `current_b`
   - Retorna ABORT cuando no quedan más operaciones

3. **Llamada al servicio** (`CALL_SERVICE`):
   - Usa los valores actuales del Blackboard
   - Almacena el resultado en la lista `results`

4. **Incremento del contador** (`INCREMENT`):
   - Incrementa el índice
   - Decide si hay más operaciones (`continue`) o si terminó (`done`)

5. **Impresión de resultados** (`PRINT_RESULTS`):
   - Muestra todos los resultados almacenados al final

### Flujo de ejecución
```
INIT_DATA → PREPARE_REQUEST → CALL_SERVICE → INCREMENT
                ↑                                  ↓
                └──────────────────────────────────┘
                         (si hay más)
                              ↓ (si terminó)
                        PRINT_RESULTS → outcome_final
```

### Variable interna para almacenar respuestas
```python
blackboard["results"] = []  # Inicialización

# Al recibir cada respuesta:
blackboard["results"].append({
    "a": blackboard["current_a"],
    "b": blackboard["current_b"],
    "sum": response.sum
})
```

### Resultados obtenidos
```
Operación 1: 10 + 5 = 15
Operación 2: 20 + 15 = 35
Operación 3: 7 + 3 = 10
Operación 4: 100 + 50 = 150
```

### Ventajas de esta implementación

- **Escalabilidad**: Fácil añadir más operaciones
- **Persistencia**: Todos los resultados se mantienen en el Blackboard
- **Modularidad**: Cada estado tiene una responsabilidad clara
- **Reutilización**: Los estados son independientes y reutilizables
