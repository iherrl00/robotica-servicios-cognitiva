# Ejercicio 5: Integración de FSM con acciones en ROS2

## Funcionamiento de la integración

### Diferencia entre Servicios y Acciones

**Servicios**: Operaciones síncronas, esperan hasta completarse (sin feedback intermedio).

**Acciones**: Operaciones asíncronas de larga duración con:
- **Goal**: Objetivo a lograr
- **Feedback**: Actualizaciones periódicas del progreso
- **Result**: Resultado final

### Componentes principales

#### 1. **ActionState**
Clase especializada que integra acciones ROS2 en la FSM:
```python
class FibonacciState(ActionState):
    def __init__(self) -> None:
        super().__init__(
            Fibonacci,                      # Tipo de la acción
            "/fibonacci",                   # Nombre de la acción
            self.create_goal_handler,       # Callback para crear el goal
            set(),                          # Outcomes personalizados
            self.response_handler,          # Callback para el resultado
            self.print_feedback,            # Callback para el feedback
        )
```

#### 2. **create_goal_handler**
Crea el objetivo desde el Blackboard:
```python
def create_goal_handler(self, blackboard: Blackboard) -> Fibonacci.Goal:
    goal = Fibonacci.Goal()
    goal.order = blackboard["n"]  # Lee del Blackboard
    return goal
```

#### 3. **print_feedback**
Procesa actualizaciones periódicas durante la ejecución:
```python
def print_feedback(self, blackboard: Blackboard, feedback: Fibonacci.Feedback) -> None:
    yasmin.YASMIN_LOG_INFO(f"Received feedback: {list(feedback.sequence)}")
```

#### 4. **response_handler**
Procesa el resultado final:
```python
def response_handler(self, blackboard: Blackboard, response: Fibonacci.Result) -> str:
    blackboard["fibo_res"] = response.sequence
    return SUCCEED
```

### Flujo de ejecución

1. **CALLING_FIBONACCI**:
   - Lee `n=10` del Blackboard
   - Envía goal al servidor
   - Recibe feedback cada segundo (secuencia parcial)
   - Recibe resultado final cuando termina
   - Guarda `fibo_res` en Blackboard

2. **PRINTING_RESULT**:
   - Lee `fibo_res` del Blackboard
   - Muestra el resultado

### Ventajas sobre servicios

- **Feedback en tiempo real**: Supervisión del progreso
- **Cancelación**: Posibilidad de abortar operaciones largas
- **No bloqueante**: Permite ejecutar otras tareas mientras espera

## Modificación realizada: Supervisión con cancelación

### Cambios implementados

1. **Parámetro de umbral máximo**:
```python
   FibonacciMonitorState(max_value=20)
```

2. **Supervisión en el feedback**:
```python
   def monitor_feedback(self, blackboard: Blackboard, feedback: Fibonacci.Feedback):
       sequence = list(feedback.sequence)
       if sequence and sequence[-1] > self.max_value:
           yasmin.YASMIN_LOG_WARN(f"¡ALERTA! Valor {sequence[-1]} supera el umbral {self.max_value}")
           self.should_cancel = True
           blackboard["cancel_reason"] = f"Valor {sequence[-1]} superó el umbral {self.max_value}"
           blackboard["last_sequence"] = sequence
           self.cancel_state()  # Cancela la acción
```

3. **Gestión de cancelación**:
   - Estado `PRINTING_CANCELLED` para mostrar información de la cancelación
   - Almacena razón de cancelación y última secuencia en Blackboard

### Flujo observado
```
1. Solicita Fibonacci de orden 15
2. Recibe feedback: [0, 1, 1]
3. Recibe feedback: [0, 1, 1, 2]
4. Recibe feedback: [0, 1, 1, 2, 3]
5. Recibe feedback: [0, 1, 1, 2, 3, 5]
6. Recibe feedback: [0, 1, 1, 2, 3, 5, 8]
7. Recibe feedback: [0, 1, 1, 2, 3, 5, 8, 13]
8. Recibe feedback: [0, 1, 1, 2, 3, 5, 8, 13, 21]
ALERTA: 21 > 20 → Cancela la acción
9. Servidor recibe cancelación y detiene
```

### Ventajas de esta implementación

- **Supervisión en tiempo real**: Detecta condiciones problemáticas durante la ejecución
- **Cancelación segura**: Detiene operaciones antes de que causen problemas
- **Trazabilidad**: Almacena toda la información relevante en el Blackboard
- **Reutilizable**: El umbral es configurable

### Aplicaciones prácticas

Este patrón es útil para:
- Robots que deben abortar movimientos peligrosos
- Procesos que consumen demasiados recursos
- Operaciones con límites de tiempo o costo
- Detección de anomalías en tiempo real
